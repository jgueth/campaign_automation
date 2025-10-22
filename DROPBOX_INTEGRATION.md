# Dropbox Integration

The campaign automation workflow now supports automatic synchronization with Dropbox using a hybrid approach.

## How It Works

The workflow uses a **hybrid sync approach**:
1. **Cleanup**: Removes old output folder (if exists)
2. **Before processing**: Downloads input folder from Dropbox to local filesystem
3. **During processing**: Works with local files (fast, no network delays)
4. **After processing**: Copies output folder to Dropbox (local files remain)

This gives you:
- Fast local file operations during processing
- Automatic syncing with Dropbox for collaboration
- Local output files remain available after upload
- Clean start with each workflow run (old outputs removed)
- No complex real-time sync logic

## Setup

1. Make sure you have your Dropbox access token configured in `credentials.json`:
```json
{
  "dropbox": {
    "access_token": "your-dropbox-access-token-here"
  }
}
```

2. Get your access token from: https://www.dropbox.com/developers/apps

## Usage

### Using the Python API

```python
from campaign_automation import run_workflow

# Run with Dropbox sync enabled
run_workflow(use_dropbox=True)

# Run specific campaign with Dropbox sync
run_workflow('my_campaign.yaml', use_dropbox=True)
```

### Using the Command Line

**Direct Python:**
```bash
# Run with Dropbox sync
python -m campaign_automation.workflow --dropbox

# Run specific campaign with Dropbox sync
python -m campaign_automation.workflow my_campaign.yaml --dropbox

# Run without Dropbox sync (default)
python -m campaign_automation.workflow
```

**Using launcher scripts:**
```bash
# Windows
run_workflow.cmd --dropbox
run_workflow.cmd my_campaign.yaml --dropbox

# Linux/Mac
./run_workflow.sh --dropbox
./run_workflow.sh my_campaign.yaml --dropbox
```

## Workflow Steps with Dropbox

When Dropbox sync is enabled, the workflow includes additional steps:

1. **[CLEANUP]** Remove old output folder (fresh start)
2. **[STEP 0/8]** Download input folder from Dropbox
3. **[STEP 1/8]** Validate campaign structure
4. **[STEP 2/8]** Validate required assets
5. **[STEP 3/8]** Generate output folder structure
6. **[STEP 4/8]** Generate image prompts
7. **[STEP 5/8]** Generate hero images
8. **[STEP 6/8]** Localize campaign images
9. **[STEP 7/8]** Generate campaign report
10. **[STEP 8/8]** Copy output folder to Dropbox (local files remain)

## Dropbox Folder Structure

The integration uses the following folder structure in Dropbox:

```
/input/
  ├── campaigns/
  │   └── holiday_campaign.yaml
  └── assets/
      ├── cozy_home_co_logo.png
      └── product_images...

/output_YYYYMMDD_HHMMSS/          # Timestamped folders for each workflow run
  └── (generated campaign files)

# Examples:
/output_20250122_143052/          # Run on Jan 22, 2025 at 14:30:52
/output_20250122_160215/          # Run on Jan 22, 2025 at 16:02:15
/output_20250123_091534/          # Run on Jan 23, 2025 at 09:15:34
```

**Note**: Each workflow run creates a new timestamped output folder in Dropbox, preserving all previous versions. The local `./output/` folder remains without timestamp.

## Testing

Test the Dropbox connection:

```bash
python -m src.campaign_automation.helper.dropbox_helper
```

This will:
- Connect to Dropbox
- Upload a test file
- Confirm the connection is working

## Important Notes

### Output Folder Behavior
- **Cleanup on start**: The workflow automatically removes the `./output/` folder at the beginning of each run
- **Local files kept**: After uploading to Dropbox, local output files remain in `./output/` (without timestamp)
- **Dropbox versioning**: Each upload creates a new timestamped folder in Dropbox (e.g., `/output_20250122_143052/`)
- **Multiple versions**: Keep multiple workflow runs in Dropbox without overwriting previous results
- **Check results locally**: You can review generated images locally in `./output/` after the workflow completes
- **Fresh start**: Each workflow run starts with a clean local output folder to avoid confusion

### Error Handling

The workflow is resilient to Dropbox errors:
- If Dropbox download fails, it continues with local files
- If Dropbox upload fails, output files remain available locally
- The workflow never stops due to Dropbox errors

## Advantages of the Hybrid Approach

Compared to alternatives:

| Approach | Speed | Sync | Complexity | Offline |
|----------|-------|------|------------|---------|
| **Hybrid (chosen)** | Fast | Automatic | Low | Yes (after download) |
| Direct API | Slow | Real-time | Medium | No |
| Local only | Fast | Manual | None | Yes |
| Continuous sync | Fast | Real-time | High | No |

The hybrid approach gives you the best balance of speed, simplicity, and automatic syncing.
