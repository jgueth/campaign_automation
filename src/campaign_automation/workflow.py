"""
Campaign Workflow Orchestrator

This module orchestrates the complete campaign creative generation workflow,
including validation, asset checking, and creative generation.

Usage:
    from campaign_automation import run_workflow

    # Run with default campaign (holiday_campaign.yaml)
    run_workflow()

    # Run with specific campaign
    run_workflow('my_campaign.yaml')
"""

import sys
import yaml
import shutil
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from .campaign_validator import CampaignValidator
from .assets_validator import AssetsValidator
from .output_folder_generator import OutputFolderGenerator
from .gen_ai.generate_image_prompt import generate_prompts_for_campaign
from .gen_ai.generate_hero_image import generate_hero_image
from .gen_ai.localize_campaign import localize_campaign_images
from .compliance_check import check_campaign_compliance
from .generate_report import generate_campaign_report
from .helper.dropbox_helper import DropboxSync


class CampaignWorkflow:
    """Orchestrates the complete campaign creative generation workflow."""

    # Default campaign file
    DEFAULT_CAMPAIGN_FILE = "holiday_campaign.yaml"

    def __init__(self, use_dropbox: bool = False):
        """
        Initialize the workflow with validators and generators.

        Args:
            use_dropbox: If True, sync input/output folders with Dropbox
        """
        self.campaign_validator = CampaignValidator()
        self.assets_validator = AssetsValidator()
        self.folder_generator = OutputFolderGenerator()
        self.use_dropbox = use_dropbox
        self.dropbox_sync = None

        # Initialize Dropbox if requested
        if use_dropbox:
            try:
                self.dropbox_sync = DropboxSync()
            except Exception as e:
                print(f"[WARNING] Could not initialize Dropbox: {e}")
                print("Continuing without Dropbox sync...")
                self.use_dropbox = False

    def _load_campaign_data(self, campaign_file: str) -> Dict[str, Any]:
        """Load campaign YAML data."""
        # Resolve file path
        path = Path(campaign_file)
        if not path.is_absolute():
            if len(path.parts) == 1:
                path = Path(self.campaign_validator.campaigns_dir) / campaign_file

        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def run(self, campaign_file: Optional[str] = None) -> bool:
        """
        Run the complete campaign workflow.

        Steps:
        0. [Optional] Download input folder from Dropbox
        1. Validate campaign YAML structure
        2. Validate required assets exist
        3. Generate output folder structure
        4. Generate image prompts for products
        5. Generate hero images
        6. Localize campaign images
        6.5. Check logo compliance (OpenCV feature detection)
        7. Generate campaign report
        8. [Optional] Upload output folder to Dropbox

        Args:
            campaign_file: Path to campaign YAML file (defaults to holiday_campaign.yaml)

        Returns:
            True if workflow completed successfully, False otherwise
        """
        # Use default campaign if none specified
        if campaign_file is None:
            campaign_file = self.DEFAULT_CAMPAIGN_FILE

        print("=" * 70)
        print("CAMPAIGN CREATIVE GENERATION WORKFLOW")
        print("=" * 70)
        print(f"\nCampaign: {campaign_file}")
        if self.use_dropbox:
            print("Dropbox sync: ENABLED")
        print()

        # ==========================================
        # CLEANUP: Remove old output folder
        # ==========================================
        output_dir = Path('./output')
        if output_dir.exists():
            print("[CLEANUP] Removing old output folder...")
            try:
                shutil.rmtree(output_dir)
                print("[SUCCESS] Old output folder removed\n")
            except Exception as e:
                print(f"[WARNING] Could not remove old output folder: {e}")
                print("[INFO] Continuing anyway...\n")

        # ==========================================
        # STEP 0: Download Input Folder from Dropbox
        # ==========================================
        if self.use_dropbox and self.dropbox_sync:
            print("[STEP 0/8] Downloading input folder from Dropbox...")
            try:
                files_downloaded = self.dropbox_sync.download_folder('/input', './input')
                if files_downloaded > 0:
                    print(f"[SUCCESS] Downloaded {files_downloaded} files from Dropbox\n")
                else:
                    print("[INFO] No files found in Dropbox /input folder")
                    print("[INFO] Continuing with local files...\n")
            except Exception as e:
                print(f"[WARNING] Could not download from Dropbox: {e}")
                print("[INFO] Continuing with local files...\n")

        # ==========================================
        # STEP 1: Validate Campaign Structure
        # ==========================================
        step_prefix = "[STEP 1/8]" if self.use_dropbox else "[STEP 1/7]"
        print(f"{step_prefix} Validating campaign structure...")

        is_valid, errors = self.campaign_validator.validate_file(campaign_file)

        if not is_valid:
            print("[FAILED] Campaign validation failed!\n")
            print("Errors found:")
            for error in errors:
                print(f"  - {error}")
            print("\nPlease fix the campaign YAML file and try again.")
            print("Workflow stopped.")
            return False

        print("[SUCCESS] Campaign structure is valid\n")

        # ==========================================
        # STEP 2: Validate Assets Availability
        # ==========================================
        step_prefix = "[STEP 2/8]" if self.use_dropbox else "[STEP 2/7]"
        print(f"{step_prefix} Validating required assets...")

        is_valid, errors = self.assets_validator.validate(campaign_file)

        if not is_valid:
            print("[FAILED] Assets validation failed!\n")
            for error in errors:
                print(error)
            print("\nPlease add missing assets to input/assets/ directory and try again.")
            print("Workflow stopped.")
            return False

        # Get and display assets summary
        summary = self.assets_validator.get_assets_summary(campaign_file)
        print(f"[SUCCESS] All {summary['assets_found']} required assets found")
        print(f"  Assets checked:")
        for asset in summary['found_files']:
            print(f"    [OK] {asset}")
        print()

        # ==========================================
        # STEP 3: Generate Output Folder Structure
        # ==========================================
        step_prefix = "[STEP 3/8]" if self.use_dropbox else "[STEP 3/7]"
        print(f"{step_prefix} Creating base output folder structure (non-localized)...")

        try:
            folders = self.folder_generator.generate_base_folders(campaign_file)
            print(f"[SUCCESS] Created {len(folders)} base output folders")
            print()
        except Exception as e:
            print(f"[FAILED] Could not create output folders: {e}")
            print("Workflow stopped.")
            return False

        # ==========================================
        # STEP 4: Generate Image Prompts for Products
        # ==========================================
        step_prefix = "[STEP 4/8]" if self.use_dropbox else "[STEP 4/7]"
        print(f"{step_prefix} Generating AI image prompts for products...")

        try:
            # Load campaign data
            campaign_data = self._load_campaign_data(campaign_file)

            # Generate prompts for all products
            prompts = generate_prompts_for_campaign(campaign_data)

            if not prompts:
                print("[WARNING] No prompts generated")
            else:
                print(f"[SUCCESS] Generated prompts for {len(prompts)} product(s)")
                print()

                # Display generated prompts
                for product_id, prompt in prompts.items():
                    print(f"Product: {product_id}")
                    print("-" * 70)
                    print(prompt)
                    print("-" * 70)
                    print()

        except Exception as e:
            print(f"[FAILED] Could not generate image prompts: {e}")
            print("Workflow stopped.")
            return False

        # ==========================================
        # STEP 5: Generate Hero Images with Gemini 2.5 Flash
        # ==========================================
        step_prefix = "[STEP 5/8]" if self.use_dropbox else "[STEP 5/7]"
        print(f"{step_prefix} Generating hero images with Gemini 2.5 Flash...")
        print()

        # Extract campaign and product info
        campaign = campaign_data.get('campaign', {})
        campaign_id = campaign.get('id')
        products = campaign_data.get('products', [])
        aspect_ratios = campaign_data.get('creative', {}).get('aspect_ratios', [])

        if not products or not aspect_ratios:
            print("[WARNING] No products or aspect ratios found")
        else:
            # Calculate total images to generate (base images only, no market localization yet)
            total_images = len(products) * len(aspect_ratios)
            print(f"[INFO] Generating {total_images} base images (not yet localized):")
            print(f"  - {len(products)} products")
            print(f"  - {len(aspect_ratios)} aspect ratios")
            print()

            # Track statistics
            generated_count = 0
            skipped_count = 0
            error_count = 0

            # Loop through all combinations: products × ratios (NO markets yet)
            for product in products:
                product_id = product.get('id')
                product_assets = product.get('assets', {})

                # Get paths
                product_image = product_assets.get('product_image')
                logo_image = product_assets.get('logo')

                if not product_image or not logo_image:
                    print(f"[SKIPPED] Product {product_id}: Missing product_image or logo")
                    skipped_count += len(aspect_ratios)
                    continue

                # Get the prompt for this product
                prompt = prompts.get(product_id, "")

                if not prompt:
                    print(f"[SKIPPED] Product {product_id}: No prompt available")
                    skipped_count += len(aspect_ratios)
                    continue

                # Build file paths
                product_image_path = f"input/assets/{product_image}"
                logo_image_path = f"input/assets/{logo_image}"

                # Generate for all aspect ratios (base images, not localized)
                for aspect_ratio in aspect_ratios:
                    # Convert aspect ratio format for Gemini API (e.g., "1x1" -> "1:1")
                    api_aspect_ratio = aspect_ratio.replace('x', ':')

                    # Build output filename: campaign_{product_id}_{ratio}.png (no market_id yet)
                    filename = f"campaign_{product_id}_{aspect_ratio}.png"

                    # Build output path: output/{campaign_id}/{product_id}/{ratio}/campaign_{product_id}_{ratio}.png
                    output_path = f"output/{campaign_id}/{product_id}/{aspect_ratio}/{filename}"

                    print(f"Generating base image: {product_id} | {aspect_ratio}")
                    print(f"  Output: {output_path}")

                    try:
                        # Generate hero image
                        generate_hero_image(
                            prompt=prompt,
                            product_image_path=product_image_path,
                            logo_image_path=logo_image_path,
                            aspect_ratio=api_aspect_ratio,  # Use colon format for API
                            output_path=output_path,
                            dry_run=False
                        )

                        generated_count += 1
                        print(f"  [SUCCESS] Generated")
                        print()

                    except Exception as e:
                        error_count += 1
                        print(f"  [ERROR] Failed: {e}")
                        print("  [INFO] Continuing with next image...")
                        print()

            # Print summary
            print()
            print("=" * 70)
            print("IMAGE GENERATION SUMMARY")
            print("=" * 70)
            print(f"Successfully generated: {generated_count}/{total_images}")
            if skipped_count > 0:
                print(f"Skipped (missing assets): {skipped_count}")
            if error_count > 0:
                print(f"Failed with errors: {error_count}")
            print()

        # ==========================================
        # STEP 6: Localize Campaign Images
        # ==========================================
        print("=" * 70)
        step_prefix = "[STEP 6/8]" if self.use_dropbox else "[STEP 6/7]"
        print(f"{step_prefix} Localizing campaign images for all markets...")
        print("=" * 70)
        print()

        try:
            stats = localize_campaign_images(
                campaign_file=campaign_file,
                dry_run=False
            )

            if stats['errors'] > 0:
                print("[WARNING] Some images failed to localize, but workflow completed")
            else:
                print("[SUCCESS] All images localized successfully")

        except Exception as e:
            print(f"[ERROR] Localization failed: {e}")
            print("[INFO] Base images are still available without localization")
            # Don't stop workflow - base images are still usable
            print()

        # ==========================================
        # STEP 6.5: Logo Compliance Check
        # ==========================================
        print("=" * 70)
        step_prefix = "[STEP 6.5/8.5]" if self.use_dropbox else "[STEP 6.5/7.5]"
        print(f"{step_prefix} Checking logo compliance in generated images...")
        print("=" * 70)
        print()

        try:
            compliance_stats = check_campaign_compliance(
                campaign_file=campaign_file,
                min_match_count=10,
                verbose=True
            )

            # Evaluate compliance results
            if compliance_stats['errors'] > 0:
                print("[WARNING] Some images could not be checked for compliance")

            if compliance_stats['failed'] > 0:
                print(f"[WARNING] {compliance_stats['failed']} images missing logo - manual review recommended")

            if compliance_stats['passed'] == compliance_stats['total_checked'] and compliance_stats['errors'] == 0:
                print("[SUCCESS] All images passed logo compliance check")

            print()

        except Exception as e:
            print(f"[WARNING] Compliance check failed: {e}")
            print("[INFO] Workflow will continue without compliance validation")
            print()

        # ==========================================
        # STEP 7: Generate Campaign Report
        # ==========================================
        print("=" * 70)
        step_prefix = "[STEP 7/8.5]" if self.use_dropbox else "[STEP 7/7.5]"
        print(f"{step_prefix} Generating campaign report...")
        print("=" * 70)
        print()

        try:
            # Extract campaign ID for report filename
            campaign_data = self._load_campaign_data(campaign_file)
            campaign_id = campaign_data.get('campaign', {}).get('id', 'campaign')

            # Generate report filename
            report_file = f"output/{campaign_id}/campaign_report.md"

            # Generate and display report
            generate_campaign_report(
                campaign_file=campaign_file,
                output_file=report_file,
                print_to_console=True
            )

            print()
            print(f"[SUCCESS] Report saved to: {report_file}")
            print()

        except Exception as e:
            print(f"[WARNING] Could not generate report: {e}")
            print("[INFO] Workflow completed, but report generation failed")
            print()

        # ==========================================
        # STEP 8: Upload Output Folder to Dropbox
        # ==========================================
        if self.use_dropbox and self.dropbox_sync:
            print("=" * 70)
            print("[STEP 8/8.5] Uploading output folder to Dropbox...")
            print("=" * 70)
            print()

            try:
                # Generate timestamp suffix for Dropbox folder: output_YYYYMMDD_HHMMSS
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dropbox_output_path = f"/output_{timestamp}"

                files_uploaded = self.dropbox_sync.upload_folder('./output', dropbox_output_path)
                if files_uploaded > 0:
                    print(f"[SUCCESS] Copied {files_uploaded} files to Dropbox")
                    print(f"[INFO] Dropbox location: {dropbox_output_path}")
                    print(f"[INFO] Local files remain available in ./output/\n")
                else:
                    print("[WARNING] No files to upload\n")
            except Exception as e:
                print(f"[WARNING] Could not upload to Dropbox: {e}")
                print("[INFO] Output files are still available locally\n")

        # ==========================================
        # WORKFLOW COMPLETE
        # ==========================================
        print("=" * 70)
        print("WORKFLOW COMPLETE")
        print("=" * 70)
        print()

        return True


def run_workflow(campaign_file: Optional[str] = None, use_dropbox: bool = False) -> bool:
    """
    Convenience function to run the campaign workflow.

    Args:
        campaign_file: Path to campaign YAML file (defaults to holiday_campaign.yaml)
        use_dropbox: If True, sync input/output folders with Dropbox

    Returns:
        True if workflow completed successfully, False otherwise
    """
    workflow = CampaignWorkflow(use_dropbox=use_dropbox)
    return workflow.run(campaign_file)


if __name__ == "__main__":
    """
    Command-line interface for workflow execution.

    Usage:
        python workflow.py                          # Run with default campaign (holiday_campaign.yaml)
        python workflow.py my_campaign.yaml         # Run with specific campaign
        python workflow.py --dropbox                # Run with Dropbox sync enabled
        python workflow.py my_campaign.yaml --dropbox  # Run specific campaign with Dropbox sync
    """

    # Parse arguments
    campaign_file = None
    use_dropbox = False

    for arg in sys.argv[1:]:
        if arg == "--dropbox":
            use_dropbox = True
        else:
            campaign_file = arg

    # Initialize workflow
    workflow = CampaignWorkflow(use_dropbox=use_dropbox)

    # Display which campaign we're using
    display_file = campaign_file or workflow.DEFAULT_CAMPAIGN_FILE
    print(f"\nStarting workflow for: {display_file}")
    if use_dropbox:
        print("Dropbox sync: ENABLED")
    print()

    # Run workflow
    success = workflow.run(campaign_file)

    # Exit with appropriate code
    if success:
        print("\n" + "=" * 70)
        print("WORKFLOW COMPLETED SUCCESSFULLY")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("WORKFLOW FAILED")
        print("=" * 70)
        sys.exit(1)
