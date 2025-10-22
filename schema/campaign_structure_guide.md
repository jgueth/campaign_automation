# Campaign YAML Structure Guide

This guide describes the required structure for campaign YAML files.

## Overview

Campaign YAML files define all the parameters needed for a marketing campaign. Each campaign file contains metadata, product information, creative requirements, and compliance rules.

## File Location

Campaign files should be placed in: `input/campaigns/`

Example: `input/campaigns/holiday_campaign.yaml`

## Structure Reference

### 1. Campaign Section

The `campaign` section contains core metadata and scheduling information.

```yaml
campaign:
  id: "unique_campaign_identifier"
  name: "Campaign Display Name"
  description: "Brief description of the campaign purpose"
  region: "EU"  # Region code: EU, NA, APAC, etc.
```

#### Markets

Define all markets (countries/languages) this campaign should target:

```yaml
  markets:
    - market_id: "uk"
      country: "United Kingdom"
      language: "en-GB"
    - market_id: "de"
      country: "Germany"
      language: "de-DE"
```

**Note:** The pipeline will automatically translate all English messages to the specified languages.

#### Target Audience

```yaml
  target:
    audience: "Description of target demographic"
```

#### Schedule

```yaml
  schedule:
    start_date: "2025-12-01"  # Format: YYYY-MM-DD
    end_date: "2025-12-31"
```

#### Messages

All messages should be written in **English only**. The pipeline handles translation.

```yaml
  message:
    primary: "Main campaign headline"
    secondary: "Supporting message or offer details"
    cta: "Call-to-action button text"
```

---

### 2. Products Section

The `products` section lists all products to feature in the campaign. Each product generates separate creative assets.

```yaml
products:
  - id: "product_001"
    name: "Product Name"
    description: "Product description for context"
    category: "Product category"
```

#### Assets

Specify which visual assets are available or need generation:

```yaml
    assets:
      product_image: "filename.png"  # Required: Product image in input/assets/
      logo: "brand_logo.png"         # Required: Brand logo in input/assets/
      hero_image: null               # Optional: null = pipeline will generate
```

**Asset Rules:**
- `product_image` and `logo` are **required** - must reference existing files in `input/assets/` directory
- `hero_image` is **optional** - use `null` if it should be AI-generated
- Supported formats: PNG, JPG, SVG

#### Product Message

```yaml
    message: "Product-specific tagline (in English)"
```

---

### 3. Creative Section

The `creative` section defines visual style and technical requirements.

#### Aspect Ratios

List all required output formats:

```yaml
creative:
  aspect_ratios:
    - "1x1"    # Square (Instagram, Facebook)
    - "9x16"   # Vertical (Stories, Reels)
    - "16x9"   # Horizontal (YouTube, Display)
```

#### Visual Style

```yaml
  style:
    mood: "warm, festive, cozy"
    colors:
      - "red"
      - "gold"
      - "forest green"
    setting: "Cozy living room with holiday decorations"
```

**Style Guidelines:**
- `mood`: Comma-separated adjectives describing the desired feeling
- `colors`: Array of primary colors (used for AI generation prompts)
- `setting`: Scene description for background generation

#### Text Overlay

Control which text elements appear on the creative:

```yaml
  text_overlay:
    include_message: true   # Show campaign message
    include_cta: true       # Show call-to-action
    include_logo: true      # Show brand logo
```

---

### 4. Compliance Checks

Define which validation rules should be applied:

```yaml
compliance_checks:
  - "brand_colors"           # Verify brand color usage
  - "logo_presence"          # Confirm logo is visible
  - "prohibited_words"       # Check for restricted terms
  - "holiday_inclusivity"    # Ensure inclusive messaging
  - "language_accuracy"      # Validate translations
```

**Available Compliance Checks:**
- `brand_colors` - Validates colors match brand guidelines
- `logo_presence` - Ensures logo is present and properly positioned
- `prohibited_words` - Checks for blacklisted terms
- `holiday_inclusivity` - Reviews seasonal messaging for inclusivity
- `language_accuracy` - Validates translation quality
- `accessibility` - Checks text contrast and readability
- `legal_disclaimers` - Ensures required legal text is present

---

## Best Practices

### Naming Conventions

- **Campaign ID**: Use descriptive, unique identifiers
  - Format: `[event]_[type]_[year]_[region]`
  - Example: `holiday_gift_guide_2025_eu`

- **Market ID**: Use ISO country codes (lowercase)
  - Examples: `uk`, `de`, `fr`, `us`, `jp`

- **Product ID**: Use consistent product identifiers
  - Format: `[brand]_[product]_[variant]`
  - Example: `adobe_photoshop_2025`

### Message Writing

- Keep primary message under 10 words
- Secondary message should provide value/offer details
- CTA should be clear and actionable (e.g., "Shop Now", "Learn More")
- Write naturally - translations will adapt to local idioms

### Visual Style

- Provide 3-5 mood descriptors
- List 2-4 primary colors
- Be specific with setting descriptions (helps AI generation)
- Consider cultural appropriateness for target regions

### Multi-Product Campaigns

For campaigns featuring multiple products:
1. Each product is defined as a separate entry in the `products` array
2. Shared campaign messages apply to all products
3. Product-specific messages can be defined per product
4. Maintain visual consistency by using the same `creative.style` settings

---

## Required vs Optional Fields

### Required Fields

These fields must be present in every campaign YAML:

**Campaign section:**
- `id`
- `name`
- `description`
- `region`
- `markets` (at least one market)
- `target.audience`
- `schedule.start_date`
- `schedule.end_date`
- `message.primary`
- `message.cta`

**Products section:**
- `id`
- `name`
- `category`
- `assets.product_image`
- `assets.logo`

**Creative section:**
- `aspect_ratios` (at least one)
- `style.mood`
- `style.colors` (at least one)
- `text_overlay` (all three boolean fields)

### Optional Fields

- `campaign.message.secondary`
- `products.description`
- `products.assets.hero_image` (can be `null`)
- `products.message`
- `creative.style.setting`
- `compliance_checks` (entire array)

---

## Examples

See working examples in:
- [input/campaigns/holiday_campaign.yaml](../input/campaigns/holiday_campaign.yaml)

---

## Schema Reference

For detailed field types and requirements, see [campaign_schema.yaml](campaign_schema.yaml)
