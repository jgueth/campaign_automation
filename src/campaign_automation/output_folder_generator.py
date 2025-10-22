"""
Output Folder Structure Generator

This module creates the output folder structure for campaign creatives
based on the campaign YAML configuration.

Base structure (non-localized): output/{campaign_id}/{product_id}/{aspect_ratio}/
Localized structure: output/{campaign_id}/{product_id}/{aspect_ratio}/{market_id}/

Usage:
    from campaign_automation import OutputFolderGenerator

    # Generate base folders (no market localization)
    generator = OutputFolderGenerator()
    created_folders = generator.generate_base_folders('holiday_campaign.yaml')

    # Generate localized folders (with markets)
    created_folders = generator.generate_localized_folders('holiday_campaign.yaml')

    # Or generate with custom output directory
    generator = OutputFolderGenerator(output_dir='custom_output/')
    created_folders = generator.generate_base_folders('campaign.yaml')
"""

import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path


class OutputFolderGenerator:
    """Generates output folder structure from campaign YAML files."""

    # Default output directory relative to project root
    DEFAULT_OUTPUT_DIR = "output"
    DEFAULT_CAMPAIGNS_DIR = "input/campaigns"

    def __init__(self, output_dir: Optional[str] = None, campaigns_dir: Optional[str] = None):
        """
        Initialize the folder generator.

        Args:
            output_dir: Override the default output directory
            campaigns_dir: Override the default campaigns directory
        """
        self.output_dir = output_dir or self.DEFAULT_OUTPUT_DIR
        self.campaigns_dir = campaigns_dir or self.DEFAULT_CAMPAIGNS_DIR

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

    def _load_campaign(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse a campaign YAML file.

        Args:
            file_path: Path to the campaign YAML file

        Returns:
            Parsed campaign data dictionary

        Raises:
            FileNotFoundError: If the campaign file doesn't exist
            yaml.YAMLError: If the YAML is invalid
        """
        path = self._resolve_file_path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Campaign file not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError("Campaign file must contain a dictionary")

        return data

    def generate_base_folders(self, campaign_file: str, dry_run: bool = False) -> List[str]:
        """
        Generate base output folder structure (no market localization).

        Structure: output/{campaign_id}/{product_id}/{aspect_ratio}/

        Args:
            campaign_file: Path to campaign YAML file
            dry_run: If True, return paths without creating folders

        Returns:
            List of created folder paths

        Raises:
            FileNotFoundError: If campaign file doesn't exist
            ValueError: If campaign data is invalid
        """
        # Load campaign data
        data = self._load_campaign(campaign_file)

        # Extract required information
        campaign = data.get('campaign', {})
        products = data.get('products', [])
        creative = data.get('creative', {})

        campaign_id = campaign.get('id')
        aspect_ratios = creative.get('aspect_ratios', [])

        # Validate required fields
        if not campaign_id:
            raise ValueError("Campaign must have an 'id' field")
        if not products:
            raise ValueError("Campaign must have at least one product")
        if not aspect_ratios:
            raise ValueError("Campaign must have at least one aspect_ratio")

        # Generate folder paths (base folders only, no markets)
        created_folders = []

        for product in products:
            product_id = product.get('id')
            if not product_id:
                continue

            for aspect_ratio in aspect_ratios:
                # Build folder path (no market_id)
                folder_path = Path(self.output_dir) / campaign_id / product_id / aspect_ratio

                if not dry_run:
                    # Create the folder structure
                    folder_path.mkdir(parents=True, exist_ok=True)

                created_folders.append(str(folder_path))

        return created_folders

    def generate_localized_folders(self, campaign_file: str, dry_run: bool = False) -> List[str]:
        """
        Generate localized output folder structure (with markets).

        Structure: output/{campaign_id}/{product_id}/{aspect_ratio}/{market_id}/

        Args:
            campaign_file: Path to campaign YAML file
            dry_run: If True, return paths without creating folders

        Returns:
            List of created folder paths

        Raises:
            FileNotFoundError: If campaign file doesn't exist
            ValueError: If campaign data is invalid
        """
        # Load campaign data
        data = self._load_campaign(campaign_file)

        # Extract required information
        campaign = data.get('campaign', {})
        products = data.get('products', [])
        creative = data.get('creative', {})

        campaign_id = campaign.get('id')
        markets = campaign.get('markets', [])
        aspect_ratios = creative.get('aspect_ratios', [])

        # Validate required fields
        if not campaign_id:
            raise ValueError("Campaign must have an 'id' field")
        if not products:
            raise ValueError("Campaign must have at least one product")
        if not markets:
            raise ValueError("Campaign must have at least one market")
        if not aspect_ratios:
            raise ValueError("Campaign must have at least one aspect_ratio")

        # Generate folder paths
        created_folders = []

        for product in products:
            product_id = product.get('id')
            if not product_id:
                continue

            for aspect_ratio in aspect_ratios:
                for market in markets:
                    market_id = market.get('market_id')
                    if not market_id:
                        continue

                    # Build folder path
                    folder_path = Path(self.output_dir) / campaign_id / product_id / aspect_ratio / market_id

                    if not dry_run:
                        # Create the folder structure
                        folder_path.mkdir(parents=True, exist_ok=True)

                    created_folders.append(str(folder_path))

        return created_folders

    def generate_from_campaign(self, campaign_file: str, dry_run: bool = False) -> List[str]:
        """
        Generate output folder structure from a campaign YAML file.
        Defaults to generating localized folders (with markets).

        For base folders only, use generate_base_folders() instead.

        Structure: output/{campaign_id}/{product_id}/{aspect_ratio}/{market_id}/

        Args:
            campaign_file: Path to campaign YAML file
            dry_run: If True, return paths without creating folders

        Returns:
            List of created folder paths

        Raises:
            FileNotFoundError: If campaign file doesn't exist
            ValueError: If campaign data is invalid
        """
        return self.generate_localized_folders(campaign_file, dry_run)

    def generate_structure(
        self,
        campaign_id: str,
        product_ids: List[str],
        market_ids: List[str],
        aspect_ratios: List[str],
        dry_run: bool = False
    ) -> List[str]:
        """
        Generate output folder structure from explicit parameters.

        Args:
            campaign_id: Campaign identifier
            product_ids: List of product identifiers
            market_ids: List of market identifiers
            aspect_ratios: List of aspect ratios (e.g., ["1x1", "9x16", "16x9"])
            dry_run: If True, return paths without creating folders

        Returns:
            List of created folder paths
        """
        created_folders = []

        for product_id in product_ids:
            for aspect_ratio in aspect_ratios:
                for market_id in market_ids:
                    # Build folder path
                    folder_path = Path(self.output_dir) / campaign_id / product_id / aspect_ratio / market_id

                    if not dry_run:
                        # Create the folder structure
                        folder_path.mkdir(parents=True, exist_ok=True)

                    created_folders.append(str(folder_path))

        return created_folders

    def get_folder_stats(self, campaign_file: str) -> Dict[str, Any]:
        """
        Get statistics about the folder structure that would be generated.

        Args:
            campaign_file: Path to campaign YAML file

        Returns:
            Dictionary with statistics (campaign_id, counts, total_folders)
        """
        data = self._load_campaign(campaign_file)

        campaign = data.get('campaign', {})
        products = data.get('products', [])
        creative = data.get('creative', {})

        campaign_id = campaign.get('id')
        markets = campaign.get('markets', [])
        aspect_ratios = creative.get('aspect_ratios', [])

        num_products = len([p for p in products if p.get('id')])
        num_markets = len([m for m in markets if m.get('market_id')])
        num_aspect_ratios = len(aspect_ratios)

        total_folders = num_products * num_markets * num_aspect_ratios

        return {
            'campaign_id': campaign_id,
            'num_products': num_products,
            'num_markets': num_markets,
            'num_aspect_ratios': num_aspect_ratios,
            'total_folders': total_folders,
            'output_dir': self.output_dir
        }


def generate_folders_from_campaign(campaign_file: str, output_dir: Optional[str] = None) -> List[str]:
    """
    Convenience function to generate folders from a campaign file.

    Args:
        campaign_file: Path to campaign YAML file
        output_dir: Optional custom output directory

    Returns:
        List of created folder paths
    """
    generator = OutputFolderGenerator(output_dir=output_dir)
    return generator.generate_from_campaign(campaign_file)


if __name__ == "__main__":
    """
    Command-line interface for folder generation.

    Usage:
        python output_folder_generator.py                          # Show usage
        python output_folder_generator.py holiday_campaign.yaml    # Generate from specific campaign
        python output_folder_generator.py campaign.yaml --dry-run  # Preview without creating
    """
    import sys

    generator = OutputFolderGenerator()

    # Parse arguments
    dry_run = '--dry-run' in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != '--dry-run']

    if len(args) == 0:
        print("Usage: python output_folder_generator.py <campaign_file.yaml> [--dry-run]")
        print("\nExamples:")
        print("  python output_folder_generator.py holiday_campaign.yaml")
        print("  python output_folder_generator.py holiday_campaign.yaml --dry-run")
        sys.exit(1)

    campaign_file = args[0]

    try:
        # Get statistics first
        stats = generator.get_folder_stats(campaign_file)
        print(f"Campaign: {stats['campaign_id']}")
        print(f"Output directory: {stats['output_dir']}/")
        print(f"\nFolder structure:")
        print(f"  - {stats['num_products']} products")
        print(f"  - {stats['num_markets']} markets")
        print(f"  - {stats['num_aspect_ratios']} aspect ratios")
        print(f"  = {stats['total_folders']} total folders\n")

        if dry_run:
            print("DRY RUN - No folders will be created\n")

        # Generate folders
        created_folders = generator.generate_from_campaign(campaign_file, dry_run=dry_run)

        if dry_run:
            print("Folders that would be created:")
        else:
            print("Created folders:")

        # Group by product for better readability
        current_product = None
        for folder in created_folders:
            parts = Path(folder).parts
            if len(parts) >= 2:
                product = parts[-3]  # product_id is 3rd from end
                if product != current_product:
                    if current_product is not None:
                        print()  # Blank line between products
                    current_product = product

            print(f"  {folder}")

        if not dry_run:
            print(f"\n[SUCCESS] Successfully created {len(created_folders)} folders")
        else:
            print(f"\n[DRY-RUN] Would create {len(created_folders)} folders")

        sys.exit(0)

    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"[ERROR] Invalid campaign data: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)
