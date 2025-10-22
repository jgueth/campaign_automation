"""
Assets Validator

This module validates that all required assets referenced in a campaign YAML file
exist in the input/assets/ directory.

It first validates the campaign structure using CampaignValidator, then checks
for the existence of all required asset files.

Usage:
    from campaign_automation import AssetsValidator

    # Validate assets for a campaign
    validator = AssetsValidator()
    is_valid, errors = validator.validate('holiday_campaign.yaml')
"""

import yaml
from typing import Tuple, List, Dict, Any, Optional, Set
from pathlib import Path

from .campaign_validator import CampaignValidator


class AssetsValidator:
    """Validates that all required assets exist for a campaign."""

    # Default paths
    DEFAULT_CAMPAIGNS_DIR = "input/campaigns"
    DEFAULT_ASSETS_DIR = "input/assets"
    DEFAULT_CAMPAIGN_FILE = "holiday_campaign.yaml"

    def __init__(
        self,
        campaigns_dir: Optional[str] = None,
        assets_dir: Optional[str] = None
    ):
        """
        Initialize the assets validator.

        Args:
            campaigns_dir: Override the default campaigns directory
            assets_dir: Override the default assets directory
        """
        self.campaigns_dir = campaigns_dir or self.DEFAULT_CAMPAIGNS_DIR
        self.assets_dir = assets_dir or self.DEFAULT_ASSETS_DIR
        self.campaign_validator = CampaignValidator(campaigns_dir=self.campaigns_dir)

    def _resolve_file_path(self, file_path: str) -> Path:
        """
        Resolve campaign file path with the following priority:
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
            return campaign_path

        # It's a relative path - try as-is first
        if path.exists():
            return path

        # Try relative to campaigns directory
        campaign_path = Path(self.campaigns_dir) / file_path
        if campaign_path.exists():
            return campaign_path

        if path.is_absolute():
            return path
        return campaign_path

    def _load_campaign(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse a campaign YAML file.

        Args:
            file_path: Path to the campaign YAML file

        Returns:
            Parsed campaign data dictionary

        Raises:
            FileNotFoundError: If the campaign file doesn't exist
        """
        path = self._resolve_file_path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Campaign file not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return data

    def _extract_required_assets(self, campaign_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Extract all required asset filenames from campaign data.

        Args:
            campaign_data: Parsed campaign YAML data

        Returns:
            Dictionary mapping product_id to list of required asset filenames
        """
        required_assets = {}
        products = campaign_data.get('products', [])

        for product in products:
            product_id = product.get('id', 'unknown')
            assets = product.get('assets', {})

            product_assets = []

            # product_image is required
            if assets.get('product_image'):
                product_assets.append(assets['product_image'])

            # logo is required
            if assets.get('logo'):
                product_assets.append(assets['logo'])

            # hero_image is optional, only add if not null
            if assets.get('hero_image'):
                product_assets.append(assets['hero_image'])

            if product_assets:
                required_assets[product_id] = product_assets

        return required_assets

    def _check_assets_exist(self, required_assets: Dict[str, List[str]]) -> Tuple[List[str], List[str]]:
        """
        Check which assets exist and which are missing.

        Args:
            required_assets: Dictionary mapping product_id to list of asset filenames

        Returns:
            Tuple of (found_assets, missing_assets)
        """
        assets_path = Path(self.assets_dir)
        found = []
        missing = []

        # Get all unique asset filenames
        all_assets: Set[str] = set()
        for product_assets in required_assets.values():
            all_assets.update(product_assets)

        for asset_file in all_assets:
            asset_path = assets_path / asset_file
            if asset_path.exists():
                found.append(asset_file)
            else:
                missing.append(asset_file)

        return found, missing

    def validate(self, campaign_file: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Validate that all required assets exist for a campaign.

        This performs two validation steps:
        1. Validates the campaign YAML structure using CampaignValidator
        2. Checks that all required asset files exist in assets directory

        Args:
            campaign_file: Path to campaign YAML file (defaults to holiday_campaign.yaml)

        Returns:
            Tuple of (is_valid, error_messages)
            - is_valid: Boolean indicating if validation passed
            - error_messages: List of error messages (empty if valid)
        """
        errors = []

        # Use default campaign if none specified
        if campaign_file is None:
            campaign_file = self.DEFAULT_CAMPAIGN_FILE

        # Step 1: Validate campaign structure
        campaign_is_valid, campaign_errors = self.campaign_validator.validate_file(campaign_file)

        if not campaign_is_valid:
            errors.append("Campaign validation failed. Fix campaign structure first:")
            errors.extend([f"  - {err}" for err in campaign_errors])
            return False, errors

        # Step 2: Load campaign data
        try:
            campaign_data = self._load_campaign(campaign_file)
        except FileNotFoundError as e:
            return False, [str(e)]
        except Exception as e:
            return False, [f"Error loading campaign file: {e}"]

        # Step 3: Extract required assets
        required_assets = self._extract_required_assets(campaign_data)

        if not required_assets:
            errors.append("No products with assets found in campaign")
            return False, errors

        # Step 4: Check if assets directory exists
        assets_path = Path(self.assets_dir)
        if not assets_path.exists():
            return False, [f"Assets directory not found: {self.assets_dir}"]

        # Step 5: Check which assets exist
        found, missing = self._check_assets_exist(required_assets)

        # Step 6: Report missing assets per product
        if missing:
            errors.append(f"Missing {len(missing)} required asset(s) in '{self.assets_dir}/':")

            # Group by product for clearer error messages
            for product_id, product_assets in required_assets.items():
                missing_for_product = [a for a in product_assets if a in missing]
                if missing_for_product:
                    errors.append(f"  Product '{product_id}':")
                    for asset in missing_for_product:
                        errors.append(f"    - {asset}")

            return False, errors

        # All validations passed
        return True, []

    def get_assets_summary(self, campaign_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a summary of assets required and found for a campaign.

        Args:
            campaign_file: Path to campaign YAML file (defaults to holiday_campaign.yaml)

        Returns:
            Dictionary with assets statistics
        """
        if campaign_file is None:
            campaign_file = self.DEFAULT_CAMPAIGN_FILE

        try:
            campaign_data = self._load_campaign(campaign_file)
        except Exception as e:
            return {"error": str(e)}

        required_assets = self._extract_required_assets(campaign_data)
        found, missing = self._check_assets_exist(required_assets)

        return {
            'campaign_file': campaign_file,
            'assets_dir': self.assets_dir,
            'total_products': len(required_assets),
            'total_assets_required': len(found) + len(missing),
            'assets_found': len(found),
            'assets_missing': len(missing),
            'found_files': sorted(found),
            'missing_files': sorted(missing),
            'per_product': required_assets
        }


def validate_campaign_assets(campaign_file: Optional[str] = None) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate campaign assets.

    Args:
        campaign_file: Path to campaign YAML file (defaults to holiday_campaign.yaml)

    Returns:
        Tuple of (is_valid, error_messages)
    """
    validator = AssetsValidator()
    return validator.validate(campaign_file)


if __name__ == "__main__":
    """
    Command-line interface for assets validation.

    Usage:
        python assets_validator.py                          # Validate default (holiday_campaign.yaml)
        python assets_validator.py my_campaign.yaml         # Validate specific campaign
    """
    import sys

    validator = AssetsValidator()

    # Get campaign file from arguments or use default
    campaign_file = sys.argv[1] if len(sys.argv) > 1 else None

    # Use default if not specified
    display_file = campaign_file or validator.DEFAULT_CAMPAIGN_FILE

    print(f"Validating assets for campaign: {display_file}\n")

    try:
        # Get summary first
        summary = validator.get_assets_summary(campaign_file)

        if "error" in summary:
            print(f"[ERROR] {summary['error']}")
            sys.exit(1)

        print(f"Campaign: {summary['campaign_file']}")
        print(f"Assets directory: {summary['assets_dir']}/")
        print(f"\nAssets summary:")
        print(f"  - Products: {summary['total_products']}")
        print(f"  - Total assets required: {summary['total_assets_required']}")
        print(f"  - Found: {summary['assets_found']}")
        print(f"  - Missing: {summary['assets_missing']}")
        print()

        # Perform validation
        is_valid, errors = validator.validate(campaign_file)

        if is_valid:
            print("[VALID] All required assets found!")
            print(f"\nFound assets ({len(summary['found_files'])}):")
            for asset in summary['found_files']:
                print(f"  [OK] {asset}")
            sys.exit(0)
        else:
            print("[INVALID] Asset validation failed\n")
            for error in errors:
                print(error)

            if summary['found_files']:
                print(f"\nFound assets ({len(summary['found_files'])}):")
                for asset in summary['found_files']:
                    print(f"  [OK] {asset}")

            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)
