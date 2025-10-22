"""
Hero Image Generator using Gemini 2.5 Flash (Nano Banana)

This module generates hero images by compositing product images and logos
into AI-generated lifestyle scenes using Google's Gemini 2.5 Flash Image API.

Output Structure: output/{campaign_id}/{product_id}/hero_image/hero_image_{ratio}.png

Usage:
    from campaign_automation.gen_ai.generate_hero_image import generate_hero_image

    image_data = generate_hero_image(
        prompt="Cozy living room scene...",
        product_image_path="input/assets/product.png",
        logo_image_path="input/assets/logo.png",
        aspect_ratio="16:9",
        output_path="output/campaign_id/product_id/hero_image/hero_image_16x9.png"
    )
"""

import base64
import requests
import json
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import shutil

from ..credentials import get_gemini_api_key


# Gemini 2.5 Flash Image API endpoint
GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"


def _get_or_create_resized_image(image_path: Path, max_size: int = 1024) -> Path:
    """
    Get or create a resized version of the image in the resized/ subfolder.
    Original image is never modified.

    Args:
        image_path: Path to the original image file
        max_size: Maximum dimension (width or height) in pixels

    Returns:
        Path to the resized image (or original if no resize needed)
    """
    # Create resized folder if it doesn't exist
    resized_dir = image_path.parent / "resized"
    resized_dir.mkdir(exist_ok=True)

    # Path for resized image
    resized_path = resized_dir / image_path.name

    # If resized version already exists, use it
    if resized_path.exists():
        return resized_path

    # Open original image
    img = Image.open(image_path)

    # Check if resizing is needed
    if max(img.size) <= max_size:
        # No resize needed, just copy to resized folder
        shutil.copy2(image_path, resized_path)
        return resized_path

    # Calculate new size maintaining aspect ratio
    ratio = max_size / max(img.size)
    new_size = tuple(int(dim * ratio) for dim in img.size)

    # Resize image
    img_resized = img.resize(new_size, Image.Resampling.LANCZOS)

    # Save resized image to resized/ folder
    img_resized.save(resized_path)

    return resized_path


def _encode_image_to_base64(image_path: Path) -> Tuple[str, str]:
    """
    Encode image file to base64 string.

    Args:
        image_path: Path to the image file

    Returns:
        Tuple of (base64_data, mime_type)
    """
    # Determine MIME type
    suffix = image_path.suffix.lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp'
    }
    mime_type = mime_types.get(suffix, 'image/png')

    # Read and encode
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    return image_data, mime_type


def generate_hero_image(
    prompt: str,
    product_image_path: str,
    logo_image_path: str,
    aspect_ratio: str = "16:9",
    output_path: Optional[str] = None,
    dry_run: bool = False
) -> Optional[bytes]:
    """
    Generate a hero image using Gemini 2.5 Flash with product and logo compositing.

    Args:
        prompt: Detailed scene description prompt (from GPT-5)
        product_image_path: Path to product image file
        logo_image_path: Path to logo image file
        aspect_ratio: Desired aspect ratio (e.g., "16:9", "1:1", "9:16")
        output_path: Where to save the generated image (optional)
        dry_run: If True, skip actual API call and image generation

    Returns:
        Generated image data as bytes, or None if dry_run or error

    Raises:
        FileNotFoundError: If product or logo image doesn't exist
        RuntimeError: If API call fails
    """
    # Validate input files exist
    product_path = Path(product_image_path)
    logo_path = Path(logo_image_path)

    if not product_path.exists():
        raise FileNotFoundError(f"Product image not found: {product_image_path}")
    if not logo_path.exists():
        raise FileNotFoundError(f"Logo image not found: {logo_image_path}")

    # Convert aspect_ratio from '1x1', '16x9', '9x16' to '1:1', '16:9', '9:16' if needed
    if isinstance(aspect_ratio, str) and 'x' in aspect_ratio:
        aspect_ratio = aspect_ratio.replace('x', ':')

    # Get or create resized versions (originals remain untouched)
    print(f"  [INFO] Preparing images (originals will not be modified)...")
    product_resized = _get_or_create_resized_image(product_path, max_size=1024)
    logo_resized = _get_or_create_resized_image(logo_path, max_size=512)

    print(f"  [INFO] Using resized images from: input/assets/resized/")

    if dry_run:
        print(f"  [DRY-RUN] Would generate image with aspect ratio {aspect_ratio}")
        print(f"  [DRY-RUN] Product: {product_image_path}")
        print(f"  [DRY-RUN] Logo: {logo_image_path}")
        print(f"  [DRY-RUN] Prompt: {prompt[:100]}...")
        return None

    # Encode resized images to base64
    print(f"  [INFO] Encoding images...")
    product_data, product_mime = _encode_image_to_base64(product_resized)
    logo_data, logo_mime = _encode_image_to_base64(logo_resized)

    # Get API key
    api_key = get_gemini_api_key()

    # Enhance prompt with compositing instruction
    enhanced_prompt = f"""{prompt}

COMPOSITING INSTRUCTION:
You are provided with two images to composite into this scene:
1. A product image - place it prominently in the scene where it naturally fits
2. A brand logo - place it subtly in a corner or edge where it's visible but not dominating

Composite both images naturally into the scene at aesthetically pleasing positions.
Ensure the product is the hero/focal point and the logo is clearly visible but tasteful."""

    # Build Gemini API request
    payload = {
        'contents': [{
            'parts': [
                {'text': enhanced_prompt},
                {
                    'inlineData': {
                        'mimeType': product_mime,
                        'data': product_data
                    }
                },
                {
                    'inlineData': {
                        'mimeType': logo_mime,
                        'data': logo_data
                    }
                }
            ]
        }],
        'generationConfig': {
            'responseModalities': ['IMAGE'],
            'imageConfig': {
                'aspectRatio': aspect_ratio
            }
        }
    }

    # Make API request
    print(f"  [INFO] Calling Gemini 2.5 Flash API...")
    url = f"{GEMINI_API_ENDPOINT}?key={api_key}"

    try:
        response = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=120  # 2 minutes timeout for image generation
        )

        # Check for errors before raising
        if response.status_code != 200:
            error_detail = response.text
            raise RuntimeError(f"Gemini API error ({response.status_code}): {error_detail}")

        response.raise_for_status()
        result = response.json()

        # Extract generated image from response
        # Gemini returns image in candidates[0].content.parts[0].inlineData.data
        if 'candidates' not in result:
            raise RuntimeError(f"Unexpected API response: {result}")

        image_data_b64 = result['candidates'][0]['content']['parts'][0]['inlineData']['data']
        image_bytes = base64.b64decode(image_data_b64)

        # Save if output path specified
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_bytes(image_bytes)
            print(f"  [SUCCESS] Image saved to: {output_path}")

        return image_bytes

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Gemini API request failed: {e}")
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Failed to extract image from API response: {e}")
    except Exception as e:
        raise RuntimeError(f"Image generation failed: {e}")


if __name__ == "__main__":
    """Test the hero image generator."""
    import sys

    print("Testing Hero Image Generator\n")
    print("=" * 70)

    # Test with example data
    test_prompt = """Cozy European living room interior at golden hour with warm,
    festive holiday ambiance. Burgundy and forest green color palette with
    gold accents. Fireplace, plush armchair, warm lighting."""

    try:
        # Dry run test
        generate_hero_image(
            prompt=test_prompt,
            product_image_path="input/assets/aromatherapy_diffuser_set.png",
            logo_image_path="input/assets/cozy_home_co_logo.png",
            aspect_ratio="16:9",
            output_path="output/test/hero_test.png",
            dry_run=True
        )

        print("\n[SUCCESS] Dry run completed successfully!")
        print("[INFO] Remove dry_run=True to generate actual image")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        sys.exit(1)
