# Campaign Creative Automation Tool

## Overview

Creating localized campaign creatives for multiple markets, languages, and products manually is time-consuming and error-prone. This tool automates the entire process from a single campaign definition to localized assets across different platforms and markets.

### What This Tool Does

This creative automation pipeline takes a campaign definition in YAML format along with product assets and automatically generates localized campaign images for multiple markets, products, and aspect ratios.

**A concrete example**: You define a holiday campaign with 2 products targeting 3 European markets (Germany, France, Spain) in 2 aspect ratios. The tool automatically generates 12 localized campaign images (2 products × 3 markets × 2 ratios), each with properly translated messaging and consistent branding.

The workflow handles the complete process end-to-end:

1. **Campaign validation** - Verifies your campaign YAML structure and checks that all required assets exist
2. **AI prompt generation** - Creates optimized prompts for image generation based on your campaign parameters (GPT-5)
3. **Lifestyle image generation** - Generates brand-appropriate lifestyle scenes using AI, or uses provided hero images (Gemini 2.5 Flash)
4. **Product compositing** - Integrates product images and logos into the lifestyle scenes
5. **Multi-market localization** - Translates campaign messaging to target languages and overlays text on images for each market (Gemini 2.5 Flash for translation)
6. **Brand compliance checking** - Validates that logos are present in all generated images using computer vision (OpenCV feature detection)
7. **Report generation** - Creates a comprehensive summary of the campaign execution
8. **AI-powered analysis** - Analyzes workflow logs and generated report to validate execution quality and provide recommendations (Gemini, available in agent mode)
9. **Optional Dropbox sync** - Uploads generated assets to cloud storage for team access

The tool generates creatives in multiple aspect ratios (1:1 for Instagram feed, 9:16 for Stories/Reels, 16:9 for YouTube, etc.) to support different social media platforms. Output files are organized by campaign, product, market, and aspect ratio for easy distribution. The tool can run as a command-line workflow for manual execution or in agent mode for automated monitoring of new campaign files.

## Quick Reference

### Prerequisites (First Time Setup)

Before running the workflow, you need to complete these one-time setup steps:

1. **Install Python 3.8+** (if not already installed)
2. **Install the package and dependencies:**
   ```bash
   pip install -e .           # Installs package from setup.py
   pip install -r requirements.txt   # Installs all dependencies (including opencv-python)
   ```
3. **Configure API credentials:**
   ```bash
   cp credentials.json.example credentials.json
   # Edit credentials.json with your OpenAI, Gemini, and Dropbox (optional) API keys
   ```

See [Installation](#installation) and [Configuration](#configuration) sections below for detailed instructions.

**Note:** The launcher scripts (`run_workflow.cmd`, `start_agent.cmd`) automatically check for and install missing dependencies, but manual setup is recommended for better control.

### Usage (After Setup)

```bash
# Basic workflow usage (manual execution)
run_workflow.cmd                              # Windows: default campaign
./run_workflow.sh                             # Linux/Mac: default campaign
run_workflow.cmd my_campaign.yaml             # Specific campaign

# With Dropbox sync (optional)
run_workflow.cmd --dropbox                    # Sync input/output with Dropbox
run_workflow.cmd my_campaign.yaml --dropbox   # Specific campaign + Dropbox

# Agent mode (automatic monitoring with AI analysis)
start_agent.cmd                               # Start agent (no Dropbox)
start_agent.cmd --dropbox                     # Start agent with Dropbox sync
```

**Agent Mode**: For automated workflow execution with AI-powered analysis, see [README_AGENT.md](README_AGENT.md).

For detailed Dropbox setup, see [DROPBOX_INTEGRATION.md](DROPBOX_INTEGRATION.md).

## Project Structure

```
project/
├── input/
│   ├── campaigns/              # Campaign YAML files (default location)
│   └── assets/                 # Product images, logos, and other assets
├── output/                     # Generated creative assets (organized by campaign/market/product)
├── log/                        # Agent logs and analysis reports (created by agent mode)
│   ├── workflow_*.log          # Workflow execution logs
│   ├── agent_*.log             # Complete agent logs
│   └── gemini_analysis_*.md    # AI analysis reports (auto-opens)
├── schema/                     # Campaign structure documentation and schema
│   ├── campaign_schema.yaml
│   └── campaign_structure_guide.md
├── docs/                       # Additional documentation
│   └── GEMINI_SETUP.md
├── src/
│   └── campaign_automation/    # Main package
│       ├── campaign_validator.py
│       ├── output_folder_generator.py
│       ├── credentials.py      # Credentials management
│       ├── gen_ai/             # AI integrations
│       └── agent/              # Intelligent agent system
│           ├── agent_watcher.py       # Main agent orchestrator
│           └── process_agent_data.py  # Workflow processor
├── credentials.json.example    # Template for API credentials
├── setup.py                    # Package installation configuration
├── requirements.txt
├── start_agent.cmd             # Windows: Start intelligent agent
├── README.md                   # This file
└── README_AGENT.md             # Agent system documentation
```

## Key Assumptions and Conventions

### Default Directories

The tool uses the following default directories:

- **Campaign files**: `input/campaigns/`
  - All campaign YAML files should be placed here
  - Tools will automatically look in this directory when only a filename is provided

- **Asset files**: `input/assets/`
  - All product images, logos, and other visual assets referenced in campaigns
  - Assets must exist here before running the campaign pipeline

- **Output files**: `output/`
  - Generated creatives are organized by: `output/[campaign_id]/[market_id]/[product_id]/`

### File Naming

- **Campaign files**: Use descriptive names with format `[event]_[type]_[year]_[region].yaml`
  - Example: `holiday_gift_guide_2025_eu.yaml`

- **Asset files**: Reference exact filenames in campaign YAML
  - Supported formats: PNG, JPG, SVG

### Path Resolution

Tools in this project use smart path resolution:

1. **Absolute paths** are used directly
2. **Filenames only** are automatically looked up in the default directory
3. **Relative paths** are tried as-is first, then relative to the default directory

**Example:**
```bash
# These all work:
python -m campaign_automation.campaign_validator                          # Validates all in input/campaigns/
python -m campaign_automation.campaign_validator holiday_campaign.yaml    # Looks in input/campaigns/
python -m campaign_automation.campaign_validator C:/full/path/file.yaml   # Uses absolute path
```

## Campaign YAML Structure

Campaign files define all parameters for creative generation. See the [Campaign Structure Guide](schema/campaign_structure_guide.md) for detailed documentation.

### Required Fields

Every campaign YAML must include:

**Campaign metadata:**
- `id`, `name`, `description`, `region`
- At least one `market` with `market_id`, `country`, `language`
- `target.audience`
- `schedule.start_date` and `schedule.end_date` (YYYY-MM-DD format)
- `message.primary` and `message.cta`

**Products:**
- At least one product with `id`, `name`, `category`
- Each product must have `assets.product_image` and `assets.logo` (cannot be null)
- `assets.hero_image` is optional (can be null for AI generation)

**Creative requirements:**
- At least one `aspect_ratio`
- `style.mood` and at least one `style.color`
- All three `text_overlay` boolean fields

### Messages and Translation

- **Write all messages in English only**
- The pipeline automatically translates messages to all target market languages
- English messages are defined in: `campaign.message` and `products[].message`

## Validation

### 1. Validate Campaign Structure

Validate that your campaign YAML files follow the correct schema:

```bash
# Validate all campaigns in input/campaigns/
python -m campaign_automation.campaign_validator

# Validate specific campaign
python -m campaign_automation.campaign_validator holiday_campaign.yaml
```

**Output:**
```
[VALID] holiday_campaign.yaml
[INVALID] broken_campaign.yaml
    - Missing required field: campaign.id
    - products[0].assets.logo is required and cannot be null

Summary: 1/2 files valid
```

### 2. Validate Campaign Assets

Validate that all required assets exist in `input/assets/`:

```bash
# Validate assets for default campaign (holiday_campaign.yaml)
python -m campaign_automation.assets_validator

# Validate assets for specific campaign
python -m campaign_automation.assets_validator my_campaign.yaml
```

**Output:**
```
Validating assets for campaign: holiday_campaign.yaml

Campaign: holiday_campaign.yaml
Assets directory: input/assets/

Assets summary:
  - Products: 2
  - Total assets required: 2
  - Found: 2
  - Missing: 0

[VALID] All required assets found!

Found assets (2):
  [OK] aromatherapy_diffuser_set.png
  [OK] cozy_home_co_logo.png
```

The assets validator:
- First validates the campaign YAML structure
- Then checks that all required `product_image` and `logo` files exist
- Reports which assets are found and which are missing

### Using Validators in Code

**Campaign Structure Validator:**
```python
from campaign_automation import CampaignValidator

validator = CampaignValidator()

# Validate single file
is_valid, errors = validator.validate_file('holiday_campaign.yaml')

if not is_valid:
    for error in errors:
        print(f"Error: {error}")

# Validate all campaigns
results = validator.validate_all_campaigns()
for file_path, (is_valid, errors) in results.items():
    if not is_valid:
        print(f"{file_path}: {len(errors)} errors")
```

**Assets Validator:**
```python
from campaign_automation import AssetsValidator

validator = AssetsValidator()

# Validate assets (uses holiday_campaign.yaml by default)
is_valid, errors = validator.validate()

# Or specify a campaign
is_valid, errors = validator.validate('my_campaign.yaml')

# Get detailed summary
summary = validator.get_assets_summary('holiday_campaign.yaml')
print(f"Found: {summary['assets_found']}, Missing: {summary['assets_missing']}")
```

## Quick Start

### Easy Launcher Scripts (Recommended)

The easiest way to run the workflow is using the provided launcher scripts. They automatically check for prerequisites and run the complete workflow.

**Windows:**
```cmd
run_workflow.cmd
```

**Linux/Mac:**
```bash
./run_workflow.sh
```

**With specific campaign:**
```bash
# Windows
run_workflow.cmd my_campaign.yaml

# Linux/Mac
./run_workflow.sh my_campaign.yaml
```

**With Dropbox sync (optional):**
```bash
# Windows
run_workflow.cmd --dropbox
run_workflow.cmd my_campaign.yaml --dropbox

# Linux/Mac
./run_workflow.sh --dropbox
./run_workflow.sh my_campaign.yaml --dropbox
```

When `--dropbox` is enabled, the workflow will:
- Clean up old output folder (fresh start)
- Download the `/input` folder from Dropbox before processing
- Process everything locally (fast performance)
- Copy the `/output` folder to Dropbox with timestamp suffix (e.g., `/output_20250122_143052/`)
- Keep local files in `./output/` (without timestamp)

**Note**: Each Dropbox upload creates a timestamped folder, preserving multiple versions. Local output remains in `./output/` for review.

See [DROPBOX_INTEGRATION.md](DROPBOX_INTEGRATION.md) for detailed setup and usage.

The launcher scripts will:
- ✅ Check if Python is installed
- ✅ Check if credentials.json exists
- ✅ Install the package if needed (`pip install -e .`)
- ✅ Install dependencies from requirements.txt if needed
- ✅ Run the complete workflow
- ✅ Show clear success/error messages

**No Python knowledge required!** Just run the script and follow any error messages.

### What the Workflow Does

The complete workflow runs 8 automated steps (9 with `--dropbox`):

1. **[Optional] Download from Dropbox** - Downloads input folder from Dropbox (if `--dropbox` flag used)
2. **Validate Campaign Structure** - Ensures your campaign YAML is correctly formatted
3. **Validate Assets** - Checks that all product images and logos exist
4. **Create Output Folders** - Generates organized folder structure
5. **Generate AI Prompts** - Creates optimized prompts for image generation (GPT-5)
6. **Generate Base Images** - Creates lifestyle scenes with product + logo composited (Gemini 2.5 Flash)
7. **Localize Images** - Adds translated text overlays for each market (Gemini 2.5 Flash)
8. **Check Logo Compliance** - Verifies logo presence in all generated images using OpenCV feature detection
9. **Generate Report** - Creates comprehensive campaign report
10. **[Optional] Upload to Dropbox** - Uploads output folder to Dropbox (if `--dropbox` flag used)

**Output Structure:**
```
output/
└── campaign_id/
    └── product_id/
        └── aspect_ratio/
            ├── campaign_product_ratio.png          (base image, no text)
            └── market_id/
                └── campaign_product_market_ratio.png  (localized with text)
```

**Example:**
```
output/holiday_gift_guide_2025_eu/
├── aromatherapy_diffuser_set/
│   └── 9x16/
│       ├── campaign_aromatherapy_diffuser_set_9x16.png      (base)
│       └── de/
│           └── campaign_aromatherapy_diffuser_set_de_9x16.png  (German text)
└── weighted_throw_blanket/
    └── 9x16/
        ├── campaign_weighted_throw_blanket_9x16.png         (base)
        └── de/
            └── campaign_weighted_throw_blanket_de_9x16.png     (German text)
```

---

### Manual Setup (Advanced)

If you prefer manual control:

1. **Create a campaign YAML file** in `input/campaigns/`
   - See [holiday_campaign.yaml](input/campaigns/holiday_campaign.yaml) as an example
   - Refer to [Campaign Structure Guide](schema/campaign_structure_guide.md) for field definitions

2. **Add required assets** to `input/assets/`
   - Product images referenced in your campaign
   - Brand logos

3. **Validate your campaign**
   ```bash
   python -m campaign_automation.campaign_validator your_campaign.yaml
   ```

4. **Run the complete workflow**
   ```bash
   python -m campaign_automation.workflow your_campaign.yaml

   # Or with Dropbox sync
   python -m campaign_automation.workflow your_campaign.yaml --dropbox
   ```

## Automated Agent Mode

The Campaign Automation Agent provides intelligent, automated workflow execution with AI-powered analysis:

### Features
- **Automatic monitoring**: Watches `/input` folder for new YAML files
- **Hands-free execution**: Runs complete workflow automatically with Dropbox sync
- **AI analysis**: Gemini analyzes results and provides recommendations
- **Smart logging**: 3 log files per execution (workflow, agent, AI analysis)
- **Auto-opening reports**: Gemini analysis opens automatically in markdown viewer

### Quick Start

```bash
# Start the agent (watches for YAML files)
start_agent.cmd                    # Without Dropbox
start_agent.cmd --dropbox          # With Dropbox sync
```

Then simply drop a YAML file into `/input` or `/input/campaigns/` and the agent will:
1. Detect the file
2. Run the complete workflow
3. Analyze results with Gemini AI
4. Generate comprehensive reports
5. Open the analysis report automatically

**For complete agent documentation**, see [README_AGENT.md](README_AGENT.md).

## Documentation

- **[Agent System Guide](README_AGENT.md)** - Automated workflow execution with AI analysis
- **[Campaign Structure Guide](schema/campaign_structure_guide.md)** - Detailed documentation of YAML structure
- **[Campaign Schema](schema/campaign_schema.yaml)** - Technical schema reference
- **[Example Campaign](input/campaigns/holiday_campaign.yaml)** - Working example
- **[Dropbox Integration Guide](DROPBOX_INTEGRATION.md)** - Setup and usage for Dropbox sync (optional)

## Installation

### Requirements

- Python 3.7+
- PyYAML

### Install the Package

Install the package in development mode (recommended for local development):

```bash
# From project root
pip install -e .
```

This will:
- Install the `campaign_automation` package
- Install all dependencies (PyYAML)
- Make the package importable from anywhere
- Keep it editable (changes to source code are immediately reflected)

### Alternative: Install dependencies only

If you don't want to install the package:
```bash
pip install pyyaml
```

## Configuration

### API Credentials Setup

The tool requires API keys for AI services (OpenAI, Google Gemini). Optional: Dropbox for cloud storage.

1. **Copy the example credentials file:**
   ```bash
   cp credentials.json.example credentials.json
   ```

2. **Edit `credentials.json` with your API keys:**
   ```json
   {
     "openai": {
       "api_key": "sk-proj-your-actual-openai-key"
     },
     "google": {
       "gemini_api_key": "your-actual-gemini-key"
     },
     "dropbox": {
       "access_token": "your-dropbox-access-token"
     }
   }
   ```

3. **Get your API keys:**
   - **OpenAI:** [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - **Google Gemini:** [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
   - **Dropbox (Optional):** [https://www.dropbox.com/developers/apps](https://www.dropbox.com/developers/apps)

**Important:**
- `credentials.json` is already in `.gitignore` and will **not** be committed to git
- Never share your API keys publicly
- Each developer should maintain their own `credentials.json` file

### Using Credentials in Code

```python
from campaign_automation.credentials import get_openai_api_key, get_gemini_api_key, get_dropbox_access_token

# Get API keys
openai_key = get_openai_api_key()
gemini_key = get_gemini_api_key()
dropbox_token = get_dropbox_access_token()  # Optional, for Dropbox sync
```

### Python API with Dropbox

```python
from campaign_automation import run_workflow

# Run with default settings (no Dropbox)
run_workflow()

# Run with Dropbox sync enabled
run_workflow(use_dropbox=True)

# Run specific campaign with Dropbox sync
run_workflow('my_campaign.yaml', use_dropbox=True)
```

## Limitations

### Text Rendering Quality
The current implementation generates final campaign images with text overlays using **Gemini 2.5 Flash**. While this approach is fast and convenient, AI-generated text can occasionally contain spelling errors or formatting inconsistencies inherent to generative AI models.

**Recommended Alternative Approach:**
- Generate base images without text overlays using Gemini
- Use Gemini API for translation and localization of text content only
- Overlay translated text programmatically using Python libraries like **Pillow (PIL)** or **Wand (ImageMagick)**
- This ensures precise typography, font control, and eliminates AI spelling errors

### Automated Quality Assurance

#### Logo Compliance Check (Implemented)
The tool includes an **automated logo compliance check** using OpenCV feature detection:
- **Logo presence verification** - Automatically verifies that brand logos are present in final campaign images
- **Technology**: Uses ORB (Oriented FAST and Rotated BRIEF) feature detection
- **Capabilities**: Rotation-invariant, scale-invariant, position-invariant
- **Execution**: Runs automatically as Step 6.5 after image localization
- **Reporting**: Provides detailed pass/fail status with confidence scores

#### Not Yet Implemented
The following quality checks are **not** currently automated:
- **Brand compliance** - No validation against brand guidelines (colors, fonts, spacing)
- **Content safety** - No screening for prohibited words, inappropriate content, or regulatory compliance
- **Image quality metrics** - No automated assessment of resolution, clarity, or composition quality
- **Logo positioning validation** - While logo presence is detected, optimal positioning is not validated

**Manual review of all generated creatives is still recommended** before publishing to ensure complete brand standards and quality requirements are met.

### Asset Requirements
For quality and brand consistency, the following assets **must be provided** as image files and cannot be AI-generated:
- **Product images** - Required for each product in the campaign
- **Brand logos** - Required for each product in the campaign
- **Hero images** - Optional; if not provided, they will be AI-generated

This design decision ensures that core brand elements (products and logos) maintain consistent quality and are not subject to AI generation variability.

### Technical Limitations
- **No API retry logic**: Failed API calls (due to network issues or rate limits) are not automatically retried, requiring manual re-execution.
- **No rate limiting handling**: The tool does not implement throttling or queuing for API rate limits. Large campaigns may encounter API quota errors.
- **No cost tracking**: API usage costs (OpenAI GPT-5, Google Gemini) are not tracked or estimated before execution.
- **Single-threaded processing**: Images are generated sequentially, not in parallel, which may result in longer processing times for large campaigns.

## Support

For questions about campaign structure or validation errors, refer to:
1. [Campaign Structure Guide](schema/campaign_structure_guide.md) for field definitions
2. [Campaign Schema](schema/campaign_schema.yaml) for technical requirements
3. Run the validator for specific error messages and guidance
