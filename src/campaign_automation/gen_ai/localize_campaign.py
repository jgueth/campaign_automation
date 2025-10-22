"""
Campaign Image Localization using Gemini 2.5 Flash

This module adds localized text overlays to base campaign images using
Google's Gemini 2.5 Flash Image API (Nano Banana).

Takes base images and adds:
- Product name (near product, not hiding it)
- Product message (aligned with product name)
- Campaign primary message (prominent)
- Campaign secondary message (different position/size)
- CTA button (if enabled)

All text is translated to the target market's language.

Usage:
    from campaign_automation.gen_ai.localize_campaign import localize_campaign_images

    localize_campaign_images(
        campaign_file='holiday_campaign.yaml',
        dry_run=False
    )
"""

import base64
import requests
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from ..credentials import get_gemini_api_key


# Gemini 2.5 Flash Image API endpoint
GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"


def _load_campaign(campaign_file: str) -> Dict[str, Any]:
    """
    Load campaign YAML file.

    Args:
        campaign_file: Path to campaign YAML file

    Returns:
        Parsed campaign data
    """
    campaign_path = Path(campaign_file)

    # Try to resolve path
    if not campaign_path.is_absolute():
        if len(campaign_path.parts) == 1:
            # Just filename, look in input/campaigns
            campaign_path = Path("input/campaigns") / campaign_file

    if not campaign_path.exists():
        raise FileNotFoundError(f"Campaign file not found: {campaign_path}")

    with open(campaign_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


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


def _build_localization_prompt(
    product_name: str,
    product_message: str,
    campaign_primary: str,
    campaign_secondary: str,
    cta: str,
    language: str,
    aspect_ratio: str,
    include_cta: bool = True
) -> str:
    """
    Build the localization prompt for Gemini.

    Args:
        product_name: Name of the product
        product_message: Product-specific message
        campaign_primary: Primary campaign message
        campaign_secondary: Secondary campaign message
        cta: Call-to-action text
        language: Target language code (e.g., 'de-DE', 'en-GB', 'fr-FR')
        aspect_ratio: Image aspect ratio (for layout guidance)
        include_cta: Whether to include CTA button

    Returns:
        Formatted prompt for Gemini API
    """

    # Layout guidance based on aspect ratio
    if aspect_ratio == "9:16" or aspect_ratio == "9x16":
        layout = """
LAYOUT (Vertical format - 9:16):
- TOP THIRD: Campaign primary message (large, bold, prominent)
- MIDDLE: Product is already placed - add product name and product message close to it
- BOTTOM THIRD: Campaign secondary message (smaller than primary)
- BOTTOM: CTA button if required"""
    elif aspect_ratio == "1:1" or aspect_ratio == "1x1":
        layout = """
LAYOUT (Square format - 1:1):
- TOP: Campaign primary message (large, bold)
- CENTER: Product is already placed - add product name and product message close to it
- BOTTOM LEFT: Campaign secondary message
- BOTTOM RIGHT: CTA button if required"""
    elif aspect_ratio == "16:9" or aspect_ratio == "16x9":
        layout = """
LAYOUT (Landscape format - 16:9):
- LEFT SIDE: Campaign primary message (large, bold)
- CENTER: Product is already placed - add product name and product message close to it
- RIGHT SIDE: Campaign secondary message
- BOTTOM RIGHT: CTA button if required"""
    else:
        layout = """
LAYOUT:
- Position campaign messages prominently
- Add product name and message close to the product
- CTA button at bottom if required"""

    cta_instruction = f"\n- CTA button: \"{cta}\"" if include_cta else "\n- NO CTA button required"

    prompt = f"""Add localized text overlays to this campaign image.

TARGET LANGUAGE: {language}
Translate ALL text to {language}. Use natural, marketing-appropriate language.

TEXT TO ADD (translate to {language}):
- Product name: "{product_name}"
- Product message: "{product_message}"
- Campaign primary message: "{campaign_primary}"
- Campaign secondary message: "{campaign_secondary}"{cta_instruction}

{layout}

TEXT PLACEMENT RULES:
1. PRODUCT NAME & MESSAGE:
   - Place CLOSE to the product (wherever it is in the image)
   - Do NOT hide or cover the product
   - Keep them together and well-aligned
   - Make product name slightly larger/bolder than product message

2. CAMPAIGN MESSAGES:
   - Primary message: Large, bold, eye-catching
   - Secondary message: Smaller than primary, but still readable
   - Position them in different areas (not stacked together)

3. CTA BUTTON (if required):
   - Button-like appearance with background
   - Clear, contrasting colors
   - Positioned at bottom or bottom-right

DESIGN REQUIREMENTS:
- Professional, high-quality typography
- Ensure all text is clearly readable
- Use shadows/outlines if needed for legibility
- Maintain visual hierarchy (primary > product name > secondary > CTA)
- Text should complement the existing scene and product placement
- Colors should match the campaign's festive/cozy aesthetic

IMPORTANT: This is an existing campaign image with product and logo already placed.
Only ADD text overlays - do NOT regenerate or modify the background scene or product placement.
"""

    return prompt


def localize_image(
    base_image_path: str,
    product_name: str,
    product_message: str,
    campaign_primary: str,
    campaign_secondary: str,
    cta: str,
    language: str,
    aspect_ratio: str,
    output_path: str,
    include_cta: bool = True,
    dry_run: bool = False
) -> Optional[bytes]:
    """
    Add localized text overlays to a base campaign image.

    Args:
        base_image_path: Path to base image (without text)
        product_name: Product name to display
        product_message: Product-specific message
        campaign_primary: Primary campaign message
        campaign_secondary: Secondary campaign message
        cta: Call-to-action text
        language: Target language code (e.g., 'de-DE')
        aspect_ratio: Image aspect ratio
        output_path: Where to save localized image
        include_cta: Whether to include CTA button
        dry_run: If True, skip API call

    Returns:
        Generated image bytes or None
    """
    base_path = Path(base_image_path)

    if not base_path.exists():
        raise FileNotFoundError(f"Base image not found: {base_image_path}")

    if dry_run:
        print(f"    [DRY-RUN] Would localize to {language}")
        print(f"    [DRY-RUN] Product: {product_name}")
        print(f"    [DRY-RUN] Output: {output_path}")
        return None

    # Build localization prompt
    prompt = _build_localization_prompt(
        product_name=product_name,
        product_message=product_message,
        campaign_primary=campaign_primary,
        campaign_secondary=campaign_secondary,
        cta=cta,
        language=language,
        aspect_ratio=aspect_ratio,
        include_cta=include_cta
    )

    # Encode base image
    print(f"    [INFO] Encoding base image...")
    image_data, mime_type = _encode_image_to_base64(base_path)

    # Get API key
    api_key = get_gemini_api_key()

    # Build Gemini API request for image editing
    payload = {
        'contents': [{
            'parts': [
                {'text': prompt},
                {
                    'inlineData': {
                        'mimeType': mime_type,
                        'data': image_data
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
    print(f"    [INFO] Calling Gemini 2.5 Flash API for localization...")
    url = f"{GEMINI_API_ENDPOINT}?key={api_key}"

    try:
        response = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=120
        )

        if response.status_code != 200:
            error_detail = response.text
            raise RuntimeError(f"Gemini API error ({response.status_code}): {error_detail}")

        response.raise_for_status()
        result = response.json()

        # Extract generated image
        if 'candidates' not in result:
            raise RuntimeError(f"Unexpected API response: {result}")

        image_data_b64 = result['candidates'][0]['content']['parts'][0]['inlineData']['data']
        image_bytes = base64.b64decode(image_data_b64)

        # Save localized image
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(image_bytes)
        print(f"    [SUCCESS] Localized image saved: {output_path}")

        return image_bytes

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Gemini API request failed: {e}")
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Failed to extract image from API response: {e}")
    except Exception as e:
        raise RuntimeError(f"Localization failed: {e}")


def localize_campaign_images(
    campaign_file: str = "holiday_campaign.yaml",
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Localize all campaign images for all markets.

    Takes base images from output/{campaign_id}/{product_id}/{ratio}/
    Creates localized versions in output/{campaign_id}/{product_id}/{ratio}/{market_id}/

    Args:
        campaign_file: Path to campaign YAML file
        dry_run: If True, skip API calls

    Returns:
        Statistics dict with success/error counts
    """
    print("=" * 70)
    print("CAMPAIGN IMAGE LOCALIZATION")
    print("=" * 70)
    print()

    # Load campaign
    data = _load_campaign(campaign_file)

    campaign = data.get('campaign', {})
    products = data.get('products', [])
    creative = data.get('creative', {})

    campaign_id = campaign.get('id')
    markets = campaign.get('markets', [])
    aspect_ratios = creative.get('aspect_ratios', [])
    text_overlay = creative.get('text_overlay', {})

    campaign_primary = campaign.get('message', {}).get('primary', '')
    campaign_secondary = campaign.get('message', {}).get('secondary', '')
    cta = campaign.get('message', {}).get('cta', '')
    include_cta = text_overlay.get('include_cta', True)

    # Validate
    if not campaign_id or not products or not markets or not aspect_ratios:
        raise ValueError("Campaign must have id, products, markets, and aspect_ratios")

    # Calculate total
    total_images = len(products) * len(aspect_ratios) * len(markets)
    print(f"Localizing {total_images} images:")
    print(f"  - {len(products)} products")
    print(f"  - {len(aspect_ratios)} aspect ratios")
    print(f"  - {len(markets)} markets")
    print()

    # Track stats
    success_count = 0
    error_count = 0
    skipped_count = 0

    # Process each combination
    for product in products:
        product_id = product.get('id')
        product_name = product.get('name', product_id)
        product_message = product.get('message', '')

        for aspect_ratio in aspect_ratios:
            # Convert aspect ratio format
            api_aspect_ratio = aspect_ratio.replace('x', ':')

            # Path to base image (non-localized)
            base_image_filename = f"campaign_{product_id}_{aspect_ratio}.png"
            base_image_path = f"output/{campaign_id}/{product_id}/{aspect_ratio}/{base_image_filename}"

            # Check if base image exists
            if not Path(base_image_path).exists():
                print(f"[SKIPPED] {product_id} | {aspect_ratio} - Base image not found")
                skipped_count += len(markets)
                continue

            # Localize for each market
            for market in markets:
                market_id = market.get('market_id')
                language = market.get('language', 'en-US')

                # Output path for localized image
                localized_filename = f"campaign_{product_id}_{market_id}_{aspect_ratio}.png"
                output_path = f"output/{campaign_id}/{product_id}/{aspect_ratio}/{market_id}/{localized_filename}"

                print(f"Localizing: {product_id} | {aspect_ratio} | {market_id} ({language})")
                print(f"  Base: {base_image_path}")
                print(f"  Output: {output_path}")

                try:
                    localize_image(
                        base_image_path=base_image_path,
                        product_name=product_name,
                        product_message=product_message,
                        campaign_primary=campaign_primary,
                        campaign_secondary=campaign_secondary,
                        cta=cta,
                        language=language,
                        aspect_ratio=api_aspect_ratio,
                        output_path=output_path,
                        include_cta=include_cta,
                        dry_run=dry_run
                    )

                    success_count += 1
                    print()

                except Exception as e:
                    error_count += 1
                    print(f"    [ERROR] Failed: {e}")
                    print("    [INFO] Continuing with next image...")
                    print()

    # Summary
    print()
    print("=" * 70)
    print("LOCALIZATION SUMMARY")
    print("=" * 70)
    print(f"Successfully localized: {success_count}/{total_images}")
    if skipped_count > 0:
        print(f"Skipped (missing base): {skipped_count}")
    if error_count > 0:
        print(f"Failed with errors: {error_count}")
    print()

    return {
        'total': total_images,
        'success': success_count,
        'errors': error_count,
        'skipped': skipped_count
    }


if __name__ == "__main__":
    """Test campaign localization."""
    import sys

    # Parse arguments
    dry_run = '--dry-run' in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != '--dry-run']

    campaign_file = args[0] if args else "holiday_campaign.yaml"

    try:
        stats = localize_campaign_images(
            campaign_file=campaign_file,
            dry_run=dry_run
        )

        if stats['errors'] > 0:
            sys.exit(1)

        sys.exit(0)

    except Exception as e:
        print(f"[ERROR] Localization failed: {e}")
        sys.exit(1)
