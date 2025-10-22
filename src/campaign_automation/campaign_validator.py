"""
Campaign YAML Validator

This module provides validation functionality for campaign YAML files
according to the campaign schema requirements.

Usage:
    from campaign_automation import CampaignValidator

    # Validate specific file (will look in input/campaigns/ by default)
    validator = CampaignValidator()
    is_valid, errors = validator.validate_file('holiday_campaign.yaml')

    # Or use absolute/relative path
    is_valid, errors = validator.validate_file('path/to/campaign.yaml')

    # Validate all campaigns in directory
    results = validator.validate_all_campaigns()

    if is_valid:
        print("Campaign is valid!")
    else:
        for error in errors:
            print(f"Error: {error}")
"""

import yaml
from typing import Tuple, List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class CampaignValidator:
    """Validates campaign YAML files against the schema requirements."""

    # Default campaigns directory relative to project root
    DEFAULT_CAMPAIGNS_DIR = "input/campaigns"

    def __init__(self, campaigns_dir: Optional[str] = None):
        """
        Initialize the validator with required field definitions.

        Args:
            campaigns_dir: Override the default campaigns directory
        """
        self.campaigns_dir = campaigns_dir or self.DEFAULT_CAMPAIGNS_DIR
        self.required_campaign_fields = [
            'id', 'name', 'description', 'region', 'markets',
            'target', 'schedule', 'message'
        ]
        self.required_market_fields = ['market_id', 'country', 'language']
        self.required_product_fields = ['id', 'name', 'category', 'assets']
        self.required_asset_fields = ['product_image', 'logo']
        self.required_creative_fields = ['aspect_ratios', 'style', 'text_overlay']
        self.required_style_fields = ['mood', 'colors']
        self.required_text_overlay_fields = ['include_message', 'include_cta', 'include_logo']

    def _resolve_file_path(self, file_path: str) -> Path:
        """
        Resolve file path with the following priority:
        1. If it's an absolute path that exists, use it
        2. If it's a filename only, look in campaigns_dir
        3. If it's a relative path, try it as-is first, then relative to campaigns_dir

        Args:
            file_path: Path provided by user

        Returns:
            Resolved Path object
        """
        path = Path(file_path)

        # Check if absolute path exists
        if path.is_absolute() and path.exists():
            return path

        # Check if it's just a filename (no directory separators)
        if len(path.parts) == 1:
            # Look in campaigns directory
            campaign_path = Path(self.campaigns_dir) / file_path
            if campaign_path.exists():
                return campaign_path
            # Return the campaign path even if it doesn't exist for proper error message
            return campaign_path

        # It's a relative path - try as-is first
        if path.exists():
            return path

        # Try relative to campaigns directory
        campaign_path = Path(self.campaigns_dir) / file_path
        if campaign_path.exists():
            return campaign_path

        # If nothing exists, return the absolute version if it was absolute, otherwise campaigns_dir version
        if path.is_absolute():
            return path
        return campaign_path

    def validate_file(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Validate a campaign YAML file.

        Path resolution:
        - Absolute paths are used directly
        - Filenames only are assumed to be in the campaigns directory
        - Relative paths are tried as-is, then relative to campaigns directory

        Args:
            file_path: Path to the campaign YAML file

        Returns:
            Tuple of (is_valid, error_messages)
            - is_valid: Boolean indicating if validation passed
            - error_messages: List of error messages (empty if valid)
        """
        errors = []

        # Resolve file path
        path = self._resolve_file_path(file_path)

        # Check file exists
        if not path.exists():
            return False, [f"File not found: {path}"]

        # Load YAML
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return False, [f"Invalid YAML format: {e}"]
        except Exception as e:
            return False, [f"Error reading file: {e}"]

        # Validate structure
        if not isinstance(data, dict):
            return False, ["Root element must be a dictionary"]

        # Validate campaign section
        errors.extend(self._validate_campaign(data.get('campaign')))

        # Validate products section
        errors.extend(self._validate_products(data.get('products')))

        # Validate creative section
        errors.extend(self._validate_creative(data.get('creative')))

        return len(errors) == 0, errors

    def _validate_campaign(self, campaign: Any) -> List[str]:
        """Validate the campaign section."""
        errors = []

        if not campaign:
            return ["Missing 'campaign' section"]

        if not isinstance(campaign, dict):
            return ["'campaign' must be a dictionary"]

        # Check required fields
        for field in self.required_campaign_fields:
            if field not in campaign:
                errors.append(f"Missing required field: campaign.{field}")

        # Validate markets
        if 'markets' in campaign:
            if not isinstance(campaign['markets'], list):
                errors.append("campaign.markets must be a list")
            elif len(campaign['markets']) == 0:
                errors.append("campaign.markets must contain at least one market")
            else:
                errors.extend(self._validate_markets(campaign['markets']))

        # Validate target
        if 'target' in campaign:
            if not isinstance(campaign['target'], dict):
                errors.append("campaign.target must be a dictionary")
            elif 'audience' not in campaign['target']:
                errors.append("Missing required field: campaign.target.audience")

        # Validate schedule
        if 'schedule' in campaign:
            errors.extend(self._validate_schedule(campaign['schedule']))

        # Validate message
        if 'message' in campaign:
            errors.extend(self._validate_message(campaign['message']))

        return errors

    def _validate_markets(self, markets: List[Dict]) -> List[str]:
        """Validate markets list."""
        errors = []

        for idx, market in enumerate(markets):
            if not isinstance(market, dict):
                errors.append(f"campaign.markets[{idx}] must be a dictionary")
                continue

            for field in self.required_market_fields:
                if field not in market:
                    errors.append(f"Missing required field: campaign.markets[{idx}].{field}")

        return errors

    def _validate_schedule(self, schedule: Dict) -> List[str]:
        """Validate schedule section."""
        errors = []

        if not isinstance(schedule, dict):
            return ["campaign.schedule must be a dictionary"]

        # Check required date fields
        if 'start_date' not in schedule:
            errors.append("Missing required field: campaign.schedule.start_date")
        elif not self._is_valid_date(schedule['start_date']):
            errors.append(f"Invalid date format for campaign.schedule.start_date: {schedule['start_date']} (expected YYYY-MM-DD)")

        if 'end_date' not in schedule:
            errors.append("Missing required field: campaign.schedule.end_date")
        elif not self._is_valid_date(schedule['end_date']):
            errors.append(f"Invalid date format for campaign.schedule.end_date: {schedule['end_date']} (expected YYYY-MM-DD)")

        # Validate date logic
        if 'start_date' in schedule and 'end_date' in schedule:
            if self._is_valid_date(schedule['start_date']) and self._is_valid_date(schedule['end_date']):
                start = datetime.strptime(schedule['start_date'], '%Y-%m-%d')
                end = datetime.strptime(schedule['end_date'], '%Y-%m-%d')
                if end < start:
                    errors.append("campaign.schedule.end_date must be after start_date")

        return errors

    def _is_valid_date(self, date_str: Any) -> bool:
        """Check if string is a valid date in YYYY-MM-DD format."""
        if not isinstance(date_str, str):
            return False

        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _validate_message(self, message: Dict) -> List[str]:
        """Validate message section."""
        errors = []

        if not isinstance(message, dict):
            return ["campaign.message must be a dictionary"]

        if 'primary' not in message:
            errors.append("Missing required field: campaign.message.primary")

        if 'cta' not in message:
            errors.append("Missing required field: campaign.message.cta")

        return errors

    def _validate_products(self, products: Any) -> List[str]:
        """Validate the products section."""
        errors = []

        if not products:
            return ["Missing 'products' section"]

        if not isinstance(products, list):
            return ["'products' must be a list"]

        if len(products) == 0:
            return ["'products' must contain at least one product"]

        for idx, product in enumerate(products):
            if not isinstance(product, dict):
                errors.append(f"products[{idx}] must be a dictionary")
                continue

            # Check required fields
            for field in self.required_product_fields:
                if field not in product:
                    errors.append(f"Missing required field: products[{idx}].{field}")

            # Validate assets
            if 'assets' in product:
                errors.extend(self._validate_assets(product['assets'], idx))

        return errors

    def _validate_assets(self, assets: Dict, product_idx: int) -> List[str]:
        """Validate product assets."""
        errors = []

        if not isinstance(assets, dict):
            return [f"products[{product_idx}].assets must be a dictionary"]

        # Check required asset fields
        for field in self.required_asset_fields:
            if field not in assets:
                errors.append(f"Missing required field: products[{product_idx}].assets.{field}")
            elif assets[field] is None:
                errors.append(f"products[{product_idx}].assets.{field} is required and cannot be null")
            elif not isinstance(assets[field], str):
                errors.append(f"products[{product_idx}].assets.{field} must be a string")

        # hero_image is optional and can be null
        if 'hero_image' in assets and assets['hero_image'] is not None:
            if not isinstance(assets['hero_image'], str):
                errors.append(f"products[{product_idx}].assets.hero_image must be a string or null")

        return errors

    def _validate_creative(self, creative: Any) -> List[str]:
        """Validate the creative section."""
        errors = []

        if not creative:
            return ["Missing 'creative' section"]

        if not isinstance(creative, dict):
            return ["'creative' must be a dictionary"]

        # Check required fields
        for field in self.required_creative_fields:
            if field not in creative:
                errors.append(f"Missing required field: creative.{field}")

        # Validate aspect_ratios
        if 'aspect_ratios' in creative:
            if not isinstance(creative['aspect_ratios'], list):
                errors.append("creative.aspect_ratios must be a list")
            elif len(creative['aspect_ratios']) == 0:
                errors.append("creative.aspect_ratios must contain at least one ratio")

        # Validate style
        if 'style' in creative:
            errors.extend(self._validate_style(creative['style']))

        # Validate text_overlay
        if 'text_overlay' in creative:
            errors.extend(self._validate_text_overlay(creative['text_overlay']))

        return errors

    def _validate_style(self, style: Dict) -> List[str]:
        """Validate style section."""
        errors = []

        if not isinstance(style, dict):
            return ["creative.style must be a dictionary"]

        for field in self.required_style_fields:
            if field not in style:
                errors.append(f"Missing required field: creative.style.{field}")

        # Validate colors is a list with at least one color
        if 'colors' in style:
            if not isinstance(style['colors'], list):
                errors.append("creative.style.colors must be a list")
            elif len(style['colors']) == 0:
                errors.append("creative.style.colors must contain at least one color")

        return errors

    def _validate_text_overlay(self, text_overlay: Dict) -> List[str]:
        """Validate text_overlay section."""
        errors = []

        if not isinstance(text_overlay, dict):
            return ["creative.text_overlay must be a dictionary"]

        for field in self.required_text_overlay_fields:
            if field not in text_overlay:
                errors.append(f"Missing required field: creative.text_overlay.{field}")
            elif not isinstance(text_overlay[field], bool):
                errors.append(f"creative.text_overlay.{field} must be a boolean")

        return errors

    def validate_all_campaigns(self) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Validate all campaign YAML files in the campaigns directory.

        Returns:
            Dictionary mapping file paths to (is_valid, error_messages) tuples
        """
        results = {}
        campaigns_path = Path(self.campaigns_dir)

        if not campaigns_path.exists():
            return {"error": (False, [f"Campaigns directory not found: {self.campaigns_dir}"])}

        # Find all YAML files
        yaml_files = list(campaigns_path.glob("*.yaml")) + list(campaigns_path.glob("*.yml"))

        if not yaml_files:
            return {"warning": (True, [f"No YAML files found in {self.campaigns_dir}"])}

        for yaml_file in yaml_files:
            is_valid, errors = self.validate_file(str(yaml_file))
            results[str(yaml_file)] = (is_valid, errors)

        return results


def validate_campaign_file(file_path: str) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate a campaign file.

    Args:
        file_path: Path to the campaign YAML file

    Returns:
        Tuple of (is_valid, error_messages)
    """
    validator = CampaignValidator()
    return validator.validate_file(file_path)


if __name__ == "__main__":
    """
    Command-line interface for validation.

    Usage:
        python campaign_validator.py                          # Validate all campaigns in input/campaigns/
        python campaign_validator.py holiday_campaign.yaml    # Validate specific file in input/campaigns/
        python campaign_validator.py path/to/campaign.yaml    # Validate file at specific path
    """
    import sys

    validator = CampaignValidator()

    # No arguments - validate all campaigns
    if len(sys.argv) < 2:
        print(f"Validating all campaigns in '{validator.campaigns_dir}/'...\n")
        results = validator.validate_all_campaigns()

        if "error" in results:
            print(f"[ERROR] {results['error'][1][0]}")
            sys.exit(1)

        if "warning" in results:
            print(f"[WARNING] {results['warning'][1][0]}")
            sys.exit(0)

        total_files = len(results)
        valid_files = sum(1 for is_valid, _ in results.values() if is_valid)
        invalid_files = total_files - valid_files

        for file_path, (is_valid, errors) in results.items():
            if is_valid:
                print(f"[VALID] {Path(file_path).name}")
            else:
                print(f"[INVALID] {Path(file_path).name}")
                for error in errors:
                    print(f"    - {error}")
                print()

        print(f"\nSummary: {valid_files}/{total_files} files valid")
        sys.exit(0 if invalid_files == 0 else 1)

    # Validate specific file
    file_path = sys.argv[1]
    is_valid, errors = validate_campaign_file(file_path)

    if is_valid:
        resolved_path = validator._resolve_file_path(file_path)
        print(f"[VALID] Campaign file is valid: {resolved_path}")
        sys.exit(0)
    else:
        resolved_path = validator._resolve_file_path(file_path)
        print(f"[INVALID] Campaign file validation failed: {resolved_path}")
        print(f"\nFound {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
