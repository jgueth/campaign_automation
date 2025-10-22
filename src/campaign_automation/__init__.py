"""
Campaign Creative Automation Package

This package provides tools and utilities for automating campaign creative generation,
including validation, folder structure generation, and AI-powered creative generation.

Main modules:
- campaign_validator: Validates campaign YAML files against schema
- assets_validator: Validates that required assets exist
- output_folder_generator: Creates output folder structure from campaign files
- workflow: Orchestrates the complete campaign workflow
- credentials: Manages API credentials
- gen_ai: Generative AI integrations (OpenAI, Gemini)
- helper: Helper utilities (Dropbox, etc.)
"""

__version__ = "0.1.0"

# Lazy imports to avoid circular import issues when running as module
def __getattr__(name):
    if name == 'CampaignValidator':
        from .campaign_validator import CampaignValidator
        return CampaignValidator
    elif name == 'validate_campaign_file':
        from .campaign_validator import validate_campaign_file
        return validate_campaign_file
    elif name == 'AssetsValidator':
        from .assets_validator import AssetsValidator
        return AssetsValidator
    elif name == 'validate_campaign_assets':
        from .assets_validator import validate_campaign_assets
        return validate_campaign_assets
    elif name == 'OutputFolderGenerator':
        from .output_folder_generator import OutputFolderGenerator
        return OutputFolderGenerator
    elif name == 'generate_folders_from_campaign':
        from .output_folder_generator import generate_folders_from_campaign
        return generate_folders_from_campaign
    elif name == 'CampaignWorkflow':
        from .workflow import CampaignWorkflow
        return CampaignWorkflow
    elif name == 'run_workflow':
        from .workflow import run_workflow
        return run_workflow
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'CampaignValidator',
    'validate_campaign_file',
    'AssetsValidator',
    'validate_campaign_assets',
    'OutputFolderGenerator',
    'generate_folders_from_campaign',
    'CampaignWorkflow',
    'run_workflow',
]
