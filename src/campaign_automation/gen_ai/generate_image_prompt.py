"""
Image Prompt Generator

This module generates optimized prompts for AI image generation services.
It uses OpenAI GPT-5 to create detailed, context-aware prompts for hero images
based on campaign and product information.

Supported Models (as of 2025):
- gpt-5 (default) - Latest flagship model, best quality
- gpt-5-mini - Faster and more cost-effective
- gpt-5-nano - Smallest variant for simple tasks
- gpt-4 - Previous generation, still supported

Usage:
    from campaign_automation.gen_ai.generate_image_prompt import generate_hero_image_prompt

    prompt = generate_hero_image_prompt(
        product_name="Aromatherapy Diffuser Set",
        product_description="Essential oil diffuser with seasonal scents",
        product_message="Create Your Holiday Sanctuary",
        campaign_context={
            'audience': 'Gift-givers aged 30-55',
            'region': 'EU',
            'mood': 'warm, cozy, festive',
            'colors': ['burgundy', 'forest green', 'warm cream', 'gold'],
            'setting': 'cozy home interior'
        },
        model="gpt-5"  # Optional: defaults to gpt-5
    )
"""

from typing import Dict, List, Any, Optional
from openai import OpenAI

from ..credentials import get_openai_api_key


def generate_hero_image_prompt(
    product_name: str,
    product_description: str,
    product_message: str,
    campaign_context: Dict[str, Any],
    model: str = "gpt-5"
) -> str:
    """
    Generate an optimized prompt for hero image creation using OpenAI GPT.

    This function creates a detailed, AI-optimized prompt for generating hero images
    that incorporate product images and logos. The prompt is crafted to align with
    campaign context, target audience, and visual style requirements.

    Args:
        product_name: Name of the product
        product_description: Detailed product description
        product_message: Product-specific campaign message/tagline
        campaign_context: Dictionary containing:
            - audience: Target audience description
            - region: Geographic region
            - mood: Comma-separated mood descriptors
            - colors: List of primary colors
            - setting: Scene/environment description
        model: OpenAI model to use (default: gpt-5, also supports gpt-5-mini, gpt-4)

    Returns:
        Optimized prompt string for image generation

    Example:
        >>> context = {
        ...     'audience': 'Gift-givers aged 30-55',
        ...     'region': 'EU',
        ...     'mood': 'warm, cozy, festive',
        ...     'colors': ['burgundy', 'forest green', 'gold'],
        ...     'setting': 'cozy home interior, holiday atmosphere'
        ... }
        >>> prompt = generate_hero_image_prompt(
        ...     "Aromatherapy Diffuser",
        ...     "Essential oil diffuser with seasonal scents",
        ...     "Create Your Holiday Sanctuary",
        ...     context
        ... )
    """
    # Get API key
    api_key = get_openai_api_key()
    client = OpenAI(api_key=api_key)

    # Extract campaign context
    audience = campaign_context.get('audience', 'General audience')
    region = campaign_context.get('region', 'Global')
    mood = campaign_context.get('mood', 'professional, appealing')
    colors = campaign_context.get('colors', [])
    setting = campaign_context.get('setting', 'product showcase')

    # Format colors for the prompt
    colors_text = ', '.join(colors) if colors else 'brand-appropriate colors'

    # Create the system message for GPT
    system_message = """You are an expert creative director specializing in AI image generation prompts.
Your task is to create detailed, effective prompts for generating hero images for marketing campaigns.

Key requirements for the prompts you generate:
1. The prompt should be detailed and specific to guide image generation AI
2. Include visual style, mood, lighting, and composition details
3. Specify that a product image and logo will be composited into the scene
4. NO TEXT should be included in the generated image (text will be added later during localization)
5. The image should have clear space/areas where the product image and logo can be naturally placed
6. The prompt should create a lifestyle/atmospheric scene that complements the product
7. Consider the target audience and regional preferences
8. Maintain the specified color palette and mood

Output format: Provide ONLY the image generation prompt, no additional explanation."""

    # Create the user message with product and campaign details
    user_message = f"""Create an image generation prompt for a hero image with these details:

PRODUCT INFORMATION:
- Product Name: {product_name}
- Description: {product_description}
- Campaign Message: {product_message}

CAMPAIGN CONTEXT:
- Target Audience: {audience}
- Region: {region}
- Visual Mood: {mood}
- Color Palette: {colors_text}
- Setting/Environment: {setting}

COMPOSITION REQUIREMENTS:
- A product photo and brand logo will be PROVIDED and need to be naturally composited into the scene
- Create a lifestyle scene/background that complements the product
- The AI should place the product image and logo where they look most aesthetically pleasing
- The composition should guide the eye naturally to the product
- NO text should appear in the image (text will be added later during localization)
- The scene should evoke the mood and appeal to the target audience

IMPORTANT: The prompt should instruct the image generator to composite the provided product image
and logo into the scene in visually optimal positions, not just leave empty spaces.

Generate the optimized image generation prompt now:"""

    try:
        # Call OpenAI Chat Completions API
        # GPT-5 specific parameters: reasoning_effort and verbosity
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            max_output_tokens=500,
            reasoning={"effort": "minimal"},
            text={"verbosity": "low"},
        )

        # Extract text from Responses API output
        generated_prompt = ""
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                if hasattr(content, "text") and content.text:
                    generated_prompt += content.text

        generated_prompt = generated_prompt.strip()
        
        '''
        # Extract the generated prompt
        # Debug: Check if response has content
        if not response.choices or len(response.choices) == 0:
            raise RuntimeError("No choices in API response")

        choice = response.choices[0]
        if not hasattr(choice.message, 'content') or choice.message.content is None:
            # Check if it's in a different format (some models use 'text' instead of 'content')
            if hasattr(choice, 'text'):
                generated_prompt = choice.text.strip()
            else:
                raise RuntimeError(f"Unexpected response format: {choice}")
        else:
            generated_prompt = choice.message.content.strip()
        '''

        if not generated_prompt:
            raise RuntimeError("Generated prompt is empty")

        return generated_prompt

    except Exception as e:
        raise RuntimeError(f"Failed to generate image prompt using OpenAI: {e}")


def generate_prompts_for_campaign(campaign_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate hero image prompts for all products in a campaign.

    Args:
        campaign_data: Full campaign YAML data as dictionary

    Returns:
        Dictionary mapping product_id to generated image prompt
    """
    prompts = {}

    # Extract campaign context
    campaign = campaign_data.get('campaign', {})
    creative = campaign_data.get('creative', {})
    products = campaign_data.get('products', [])

    # Build campaign context
    campaign_context = {
        'audience': campaign.get('target', {}).get('audience', 'General audience'),
        'region': campaign.get('region', 'Global'),
        'mood': creative.get('style', {}).get('mood', 'professional'),
        'colors': creative.get('style', {}).get('colors', []),
        'setting': creative.get('style', {}).get('setting', 'product showcase')
    }

    # Generate prompt for each product
    for product in products:
        product_id = product.get('id')
        if not product_id:
            continue

        product_name = product.get('name', 'Product')
        product_description = product.get('description', '')
        product_message = product.get('message', campaign.get('message', {}).get('primary', ''))

        try:
            prompt = generate_hero_image_prompt(
                product_name=product_name,
                product_description=product_description,
                product_message=product_message,
                campaign_context=campaign_context
            )
            prompts[product_id] = prompt

        except Exception as e:
            print(f"Warning: Failed to generate prompt for product {product_id}: {e}")
            # Create a fallback basic prompt
            colors_str = ', '.join(campaign_context['colors']) if campaign_context['colors'] else 'appropriate colors'
            prompts[product_id] = (
                f"Create a {campaign_context['mood']} lifestyle scene in a {campaign_context['setting']}. "
                f"Use color palette: {colors_str}. "
                f"Composite the provided product image ({product_name}) and brand logo naturally into the scene. "
                f"Place the product prominently as the hero focal point and the logo subtly but visibly. "
                f"No text in the image."
            )
    
    return prompts


if __name__ == "__main__":
    """Test the prompt generator."""
    import sys

    print("Testing Image Prompt Generator\n")
    print("=" * 70)

    # Test with example data
    test_context = {
        'audience': 'Gift-givers and home enthusiasts aged 30-55',
        'region': 'EU',
        'mood': 'warm, cozy, festive, inviting, holiday ambiance',
        'colors': ['burgundy', 'forest green', 'warm cream', 'gold accents'],
        'setting': 'cozy home interior, winter comfort, holiday atmosphere'
    }

    try:
        prompt = generate_hero_image_prompt(
            product_name="Aromatherapy Diffuser Set",
            product_description="Essential oil diffuser with 6 seasonal scents including cinnamon, pine, and vanilla",
            product_message="Create Your Holiday Sanctuary",
            campaign_context=test_context
        )

        print("\nGenerated Image Prompt:")
        print("-" * 70)
        print(prompt)
        print("-" * 70)
        print("\n[SUCCESS] Prompt generated successfully!")

    except Exception as e:
        print(f"\n[ERROR] Failed to generate prompt: {e}")
        sys.exit(1)
