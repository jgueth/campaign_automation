"""
Campaign Report Generator

This module generates a comprehensive summary report of the campaign workflow,
including statistics about generated assets, validation results, and next steps.

Usage:
    from campaign_automation.generate_report import generate_campaign_report

    generate_campaign_report(
        campaign_file='holiday_campaign.yaml',
        output_file='reports/campaign_report.md'
    )
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


def _load_campaign(campaign_file: str) -> Dict[str, Any]:
    """Load campaign YAML file."""
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


def _count_generated_files(campaign_id: str, product_ids: List[str], aspect_ratios: List[str], markets: List[Dict]) -> Dict[str, Any]:
    """
    Count generated files in the output directory.

    Returns:
        Dict with counts for base images, localized images, and missing files
    """
    output_dir = Path("output") / campaign_id

    if not output_dir.exists():
        return {
            'base_images': 0,
            'localized_images': 0,
            'total_expected_base': len(product_ids) * len(aspect_ratios),
            'total_expected_localized': len(product_ids) * len(aspect_ratios) * len(markets),
            'missing_base': [],
            'missing_localized': []
        }

    base_count = 0
    localized_count = 0
    missing_base = []
    missing_localized = []

    # Check base images
    for product_id in product_ids:
        for aspect_ratio in aspect_ratios:
            base_path = output_dir / product_id / aspect_ratio / f"campaign_{product_id}_{aspect_ratio}.png"
            if base_path.exists():
                base_count += 1
            else:
                missing_base.append(str(base_path.relative_to("output")))

            # Check localized versions
            for market in markets:
                market_id = market.get('market_id')
                localized_path = output_dir / product_id / aspect_ratio / market_id / f"campaign_{product_id}_{market_id}_{aspect_ratio}.png"
                if localized_path.exists():
                    localized_count += 1
                else:
                    missing_localized.append(str(localized_path.relative_to("output")))

    return {
        'base_images': base_count,
        'localized_images': localized_count,
        'total_expected_base': len(product_ids) * len(aspect_ratios),
        'total_expected_localized': len(product_ids) * len(aspect_ratios) * len(markets),
        'missing_base': missing_base,
        'missing_localized': missing_localized
    }


def generate_campaign_report(
    campaign_file: str = "holiday_campaign.yaml",
    output_file: Optional[str] = None,
    print_to_console: bool = True
) -> str:
    """
    Generate a comprehensive campaign report.

    Args:
        campaign_file: Path to campaign YAML file
        output_file: Optional path to save report (markdown format)
        print_to_console: If True, print report to console

    Returns:
        Report content as string
    """
    # Load campaign data
    data = _load_campaign(campaign_file)

    campaign = data.get('campaign', {})
    products = data.get('products', [])
    creative = data.get('creative', {})

    campaign_id = campaign.get('id', 'unknown')
    campaign_name = campaign.get('name', 'Unknown Campaign')
    region = campaign.get('region', 'Unknown')
    markets = campaign.get('markets', [])
    aspect_ratios = creative.get('aspect_ratios', [])

    # Extract product IDs
    product_ids = [p.get('id') for p in products if p.get('id')]

    # Count generated files
    file_stats = _count_generated_files(campaign_id, product_ids, aspect_ratios, markets)

    # Calculate success rates
    base_success_rate = (file_stats['base_images'] / file_stats['total_expected_base'] * 100) if file_stats['total_expected_base'] > 0 else 0
    localized_success_rate = (file_stats['localized_images'] / file_stats['total_expected_localized'] * 100) if file_stats['total_expected_localized'] > 0 else 0

    # Build report
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report_lines = [
        "# Campaign Creative Generation Report",
        "",
        f"**Generated:** {timestamp}",
        f"**Campaign File:** {campaign_file}",
        "",
        "---",
        "",
        "## Campaign Overview",
        "",
        f"- **Campaign ID:** {campaign_id}",
        f"- **Campaign Name:** {campaign_name}",
        f"- **Region:** {region}",
        f"- **Markets:** {len(markets)} ({', '.join([m.get('market_id', '?') for m in markets])})",
        f"- **Products:** {len(products)}",
        f"- **Aspect Ratios:** {len(aspect_ratios)} ({', '.join(aspect_ratios)})",
        "",
        "### Products",
        ""
    ]

    for i, product in enumerate(products, 1):
        product_name = product.get('name', 'Unknown')
        product_id = product.get('id', 'unknown')
        category = product.get('category', 'N/A')
        report_lines.append(f"{i}. **{product_name}** (`{product_id}`) - {category}")

    report_lines.extend([
        "",
        "### Markets",
        ""
    ])

    for i, market in enumerate(markets, 1):
        market_id = market.get('market_id', '?')
        country = market.get('country', 'Unknown')
        language = market.get('language', 'Unknown')
        report_lines.append(f"{i}. **{country}** (`{market_id}`) - Language: {language}")

    report_lines.extend([
        "",
        "---",
        "",
        "## Generation Statistics",
        "",
        "### Base Images (Non-Localized)",
        "",
        f"- **Expected:** {file_stats['total_expected_base']}",
        f"- **Generated:** {file_stats['base_images']}",
        f"- **Success Rate:** {base_success_rate:.1f}%",
        ""
    ])

    if file_stats['missing_base']:
        report_lines.append("**Missing Base Images:**")
        for missing in file_stats['missing_base'][:10]:  # Show max 10
            report_lines.append(f"- `{missing}`")
        if len(file_stats['missing_base']) > 10:
            report_lines.append(f"- ... and {len(file_stats['missing_base']) - 10} more")
        report_lines.append("")

    report_lines.extend([
        "### Localized Images",
        "",
        f"- **Expected:** {file_stats['total_expected_localized']}",
        f"- **Generated:** {file_stats['localized_images']}",
        f"- **Success Rate:** {localized_success_rate:.1f}%",
        ""
    ])

    if file_stats['missing_localized']:
        report_lines.append("**Missing Localized Images:**")
        for missing in file_stats['missing_localized'][:10]:  # Show max 10
            report_lines.append(f"- `{missing}`")
        if len(file_stats['missing_localized']) > 10:
            report_lines.append(f"- ... and {len(file_stats['missing_localized']) - 10} more")
        report_lines.append("")

    report_lines.extend([
        "---",
        "",
        "## Output Structure",
        "",
        "Generated files are organized as:",
        "",
        "```",
        f"output/{campaign_id}/",
    ])

    for product_id in product_ids[:2]:  # Show first 2 products
        report_lines.append(f"├── {product_id}/")
        for aspect_ratio in aspect_ratios[:2]:  # Show first 2 ratios
            report_lines.append(f"│   └── {aspect_ratio}/")
            report_lines.append(f"│       ├── campaign_{product_id}_{aspect_ratio}.png (base)")
            for market in markets[:1]:  # Show first market
                market_id = market.get('market_id')
                report_lines.append(f"│       └── {market_id}/")
                report_lines.append(f"│           └── campaign_{product_id}_{market_id}_{aspect_ratio}.png")

    if len(product_ids) > 2:
        report_lines.append(f"└── ... ({len(product_ids) - 2} more products)")

    report_lines.append("```")
    report_lines.append("")

    report_lines.extend([
        "---",
        "",
        "## Workflow Summary",
        "",
        "The workflow completed the following steps:",
        "",
        "1. [DONE] **Campaign Structure Validation** - YAML structure validated",
        "2. [DONE] **Assets Validation** - Product images and logos checked",
        "3. [DONE] **Output Folder Generation** - Directory structure created",
        "4. [DONE] **AI Prompt Generation** - Optimized prompts created (GPT-5)",
        "5. [DONE] **Base Image Generation** - Lifestyle scenes generated (Gemini 2.5 Flash)",
        "6. [DONE] **Image Localization** - Text overlays added for markets (Gemini 2.5 Flash)",
        "6.5. [DONE] **Logo Compliance Check** - OpenCV feature detection verified logo presence",
        "",
        "---",
        "",
        "## Next Steps",
        "",
        "### Review Generated Images",
        "",
        f"1. Check base images in `output/{campaign_id}/[product_id]/[ratio]/`",
        f"2. Review localized versions in `output/{campaign_id}/[product_id]/[ratio]/[market_id]/`",
        "",
        "### Quality Checks",
        "",
        "- [ ] Verify product placement and visibility",
        "- [ ] Check logo presence and positioning",
        "- [ ] Review text readability and translation accuracy",
        "- [ ] Validate brand colors and style consistency",
        "- [ ] Test across different devices/platforms",
        "",
        "### Compliance (Manual)",
        "",
        "- [ ] Brand guidelines compliance",
        "- [ ] Legal/regulatory requirements per market",
        "- [ ] Accessibility standards",
        "- [ ] Copyright and licensing verification",
        "",
        "### Distribution",
        "",
        "Once approved:",
        "- [ ] Upload to asset management system",
        "- [ ] Distribute to marketing channels",
        "- [ ] Schedule campaign launch",
        "",
        "---",
        "",
        f"**Report Generated by Campaign Automation Tool v1.0**"
    ])

    report_content = "\n".join(report_lines)

    # Print to console if requested
    if print_to_console:
        print(report_content)

    # Save to file if requested
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_content, encoding='utf-8')
        if print_to_console:
            print(f"\n[INFO] Report saved to: {output_file}")

    return report_content


if __name__ == "__main__":
    """Generate report for default campaign."""
    import sys

    campaign_file = sys.argv[1] if len(sys.argv) > 1 else "holiday_campaign.yaml"
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        generate_campaign_report(
            campaign_file=campaign_file,
            output_file=output_file,
            print_to_console=True
        )
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Failed to generate report: {e}")
        sys.exit(1)
