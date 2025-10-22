# Campaign Automation Agent

An intelligent agent system that monitors campaign YAML files, executes workflows automatically, and provides AI-powered analysis using Google Gemini.

## Overview

The Campaign Automation Agent is a background service that:
- Watches the `/input` folder for new campaign YAML files
- Automatically runs the complete campaign workflow (with optional Dropbox sync)
- Captures all execution logs and outputs
- Analyzes results using Google Gemini AI
- Generates comprehensive reports and analysis
- Provides notifications and summaries

**New**: Dropbox sync is now optional and can be enabled via `--dropbox` flag!

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Watcher                           │
│  (agent_watcher.py - Orchestration & AI Analysis)           │
│                                                              │
│  • Monitors /input folder for YAML files                    │
│  • Calls process_agent_data.py to run workflow              │
│  • Analyzes results with Gemini AI                          │
│  • Saves logs and generates reports                         │
│  • Opens markdown report automatically                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                Process Agent Data                           │
│  (process_agent_data.py - Workflow Executor)                │
│                                                              │
│  • Reads campaign YAML file                                 │
│  • Executes workflow.py (with optional --dropbox flag)      │
│  • Captures stdout/stderr logs                              │
│  • Reads campaign report (if generated)                     │
│  • Returns JSON with all data                               │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    Workflow.py                              │
│  (campaign_automation/workflow.py - Campaign Generation)    │
│                                                              │
│  • Validates campaign and assets                            │
│  • Generates AI image prompts                               │
│  • Creates hero images with Gemini                          │
│  • Localizes images for markets                             │
│  • Syncs with Dropbox (if --dropbox flag provided)          │
│  • Generates campaign report                                │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
project/
├── input/                          # Drop campaign YAML files here
│   └── campaigns/
│       └── your_campaign.yaml
├── output/                         # Generated campaign assets
│   └── {campaign_id}/
│       ├── campaign_report.md
│       └── {product_id}/
├── log/                           # Agent logs and reports
│   ├── workflow_YYYYMMDD_HHMMSS.log      # Workflow execution log
│   ├── agent_YYYYMMDD_HHMMSS.log         # Complete agent log
│   └── gemini_analysis_YYYYMMDD_HHMMSS.md # AI analysis report
└── src/
    └── campaign_automation/
        └── agent/
            ├── agent_watcher.py          # Main agent orchestrator
            └── process_agent_data.py     # Workflow processor
```

## Files Generated

Each workflow execution generates **3 log files** with unique timestamps:

### 1. Workflow Log (`workflow_YYYYMMDD_HHMMSS.log`)
- Complete workflow execution output
- All stdout and stderr from workflow.py
- Validation steps, image generation progress, errors
- Technical details for debugging

### 2. Agent Log (`agent_YYYYMMDD_HHMMSS.log`)
- Comprehensive log with 5 sections:
  1. YAML Configuration (input)
  2. Workflow Execution Log (captured)
  3. Campaign Report (if generated)
  4. Gemini AI Analysis & Review
  5. Notification Placeholder (future use)

### 3. Gemini Analysis Report (`gemini_analysis_YYYYMMDD_HHMMSS.md`)
- Clean markdown report with AI analysis
- Human-readable evaluation of workflow execution
- Success/failure verdict with recommendations
- Automatically opens when complete
- Perfect for sharing and review

## Setup & Installation

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key (configured in `credentials.json`)
- Dropbox access token (optional, for Dropbox sync)
- All dependencies from `requirements.txt`

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure credentials:**

   Create/update `credentials.json` in project root:
   ```json
   {
     "gemini_api_key": "your-gemini-api-key-here",
     "dropbox_access_token": "your-dropbox-token-here"
   }
   ```

3. **Verify folder structure:**
   ```bash
   # Ensure these folders exist
   mkdir -p input/campaigns
   mkdir -p input/assets
   mkdir -p log
   ```

## Usage

### Starting the Agent

**Option 1: Using the start script (Windows) - Recommended**
```bash
# Without Dropbox sync (faster, local only)
start_agent.cmd

# With Dropbox sync (downloads input, uploads output)
start_agent.cmd --dropbox
```

**Option 2: Direct Python execution**
```bash
# Without Dropbox
python -m campaign_automation.agent.agent_watcher

# With Dropbox
python -m campaign_automation.agent.agent_watcher --dropbox
```

**Option 3: Module import**
```python
from campaign_automation.agent.agent_watcher import start_watcher
start_watcher()  # Dropbox controlled by command line args
```

### Dropbox Mode

The `--dropbox` flag enables Dropbox synchronization for each workflow:
- **Downloads** `/input` folder from Dropbox before processing
- **Uploads** `/output` folder to Dropbox after completion (with timestamp)
- All processing happens locally for best performance
- Each upload creates a new timestamped folder (e.g., `/output_20250122_143052/`)

**When to use Dropbox mode:**
- ✅ Team collaboration (shared Dropbox folder)
- ✅ Remote asset management
- ✅ Automatic backups with versioning
- ✅ Cloud storage of campaign outputs

**When to skip Dropbox mode:**
- ⚡ Faster execution (no network overhead)
- 💻 Local development and testing
- 🔒 No internet connection needed

### Using the Agent

1. **Start the agent** (it will watch the `/input` folder)

2. **Drop a campaign YAML file** into `/input` or `/input/campaigns/`

3. **Watch the console** for agent status updates:
   ```
   [Agent] [DETECTED] YAML file: my_campaign.yaml
   [Agent] [PROCESSING] Starting workflow execution...
   [Agent] [SUCCESS] Workflow completed successfully
   [Agent] [ANALYZING] Sending to Gemini for review...
   [Agent] [LOGGING] Saving agent log and Gemini analysis report...
   [Agent] [OPENING] Opening Gemini analysis report...
   [Agent] [COMPLETE] Processing finished
   ```

4. **Review the results**:
   - Gemini markdown report opens automatically
   - Check `/log` folder for detailed logs
   - Check `/output/{campaign_id}` for generated assets

### Stopping the Agent

Press `Ctrl+C` to stop the agent gracefully:
```
[Agent] [SHUTDOWN] Stopping agent...
[Agent] [SHUTDOWN] Agent stopped successfully.
```

## Agent Console Output

The agent provides clean, high-level status updates:

```
======================================================================
[Agent] Starting Gemini Campaign Workflow Agent...
======================================================================
[Agent] Watching folder: C:\path\to\project\input
[Agent] Watching subfolders: YES (recursive)
[Agent] File types: .yaml, .yml
[Agent] Log folder: C:\path\to\project\log
[Agent] Dropbox mode: ENABLED        # or DISABLED
[Agent] Status: READY - Waiting for YAML files...
======================================================================

[Agent] [DETECTED] YAML file: holiday_campaign.yaml
[Agent] [PROCESSING] Starting workflow execution...
[Agent] [SUCCESS] Workflow completed successfully
[Agent] [ANALYZING] Sending to Gemini for review...
[Agent] [LOGGING] Saving agent log and Gemini analysis report...
[Agent] [OPENING] Opening Gemini analysis report...

======================================================================
GEMINI AGENT NOTIFICATION
======================================================================
[AI Analysis Summary Here]
======================================================================

[Agent] [COMPLETE] Processing finished for holiday_campaign.yaml
[Agent]   Workflow Log: log/workflow_20251022_143025.log
[Agent]   Agent Log: log/agent_20251022_143025.log
[Agent]   Gemini Report: log/gemini_analysis_20251022_143025.md
```

## Gemini AI Analysis

The agent uses Google Gemini AI to provide intelligent analysis of each workflow execution:

### For Successful Executions:
- **Execution Summary**: Brief overview of what happened
- **Campaign Details**: Key information from YAML (products, markets, etc.)
- **Workflow Status**: Clear success verdict
- **Quality Assessment**:
  - Were all steps completed?
  - Any warnings or issues?
  - Quality of generated outputs
- **Recommendations**: Suggestions for improvement

### For Failed Executions:
- **Failure Summary**: What went wrong
- **Root Cause**: Primary cause identified from logs
- **Error Details**: Key error messages or stack traces
- **Impact**: What wasn't completed
- **Remediation Steps**: Clear action items to fix the issue

## Configuration

### Environment Variables

The agent can be configured via environment variables:

```bash
# Set custom input folder
export INPUT_FOLDER=/path/to/input

# Set custom log folder
export LOG_FOLDER=/path/to/logs
```

### Agent Settings

Key settings in `agent_watcher.py`:

```python
# Folder configuration
INPUT_FOLDER = str(PROJECT_ROOT / "input")
LOG_FOLDER = str(PROJECT_ROOT / "log")

# Gemini model
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Timeouts
WORKFLOW_TIMEOUT = 900  # 15 minutes for workflow
```

## Troubleshooting

### Agent won't start

**Issue**: `No Gemini API key found`
```
Solution: Add your Gemini API key to credentials.json
```

**Issue**: `Input folder does not exist`
```
Solution: Create the input folder: mkdir input
```

### Workflow fails

**Issue**: `ImportError: attempted relative import`
```
Solution: Ensure you're running from project root with proper PYTHONPATH
```

**Issue**: `Workflow execution timeout`
```
Solution: Increase timeout in process_agent_data.py (default: 10 minutes)
```

### Gemini analysis report not opening

**Issue**: Report saved but doesn't open
```
Solution: Manually open from log/ folder, or check default markdown application
```

## Advanced Usage

### Running Workflow Directly (Without Agent)

```python
from campaign_automation.agent.process_agent_data import run_workflow_and_capture

# Run workflow and capture results (without Dropbox)
result = run_workflow_and_capture('input/campaigns/my_campaign.yaml')

# Run workflow with Dropbox sync enabled
result = run_workflow_and_capture('input/campaigns/my_campaign.yaml', use_dropbox=True)

print(f"Success: {result['workflow_success']}")
print(f"Log saved to: {result['workflow_log_path']}")
```

### Custom Gemini Analysis

Modify the prompts in `analyze_workflow_with_gemini()` to customize AI analysis:

```python
def analyze_workflow_with_gemini(filename, workflow_data):
    # Customize prompt here
    prompt = f"""
    Your custom analysis instructions...
    """
```

### Notification Integration

Replace the placeholder in `send_notification()` with your preferred notification system:

```python
def send_notification(summary):
    # Email notification
    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    msg.set_content(summary)
    msg['Subject'] = 'Campaign Workflow Alert'
    msg['From'] = 'agent@example.com'
    msg['To'] = 'you@example.com'

    # Send email...
```

## File Watching Details

The agent uses `watchdog` library to monitor file system events:

- **Recursive monitoring**: Watches all subdirectories in `/input`
- **File types**: Only processes `.yaml` and `.yml` files
- **Duplicate prevention**: Tracks processed files to avoid reprocessing
- **Platform compatible**: Works on Windows, macOS, and Linux

## Performance Considerations

- **Workflow timeout**: 10 minutes (configurable)
- **Agent timeout**: 15 minutes total including analysis
- **Concurrent processing**: One workflow at a time (sequential)
- **Memory usage**: Logs are kept in memory during processing
- **Dropbox sync**: Adds time for large asset uploads/downloads

## Security Notes

- **API Keys**: Store in `credentials.json`, never commit to version control
- **File permissions**: Agent needs read access to `/input`, write access to `/log` and `/output`
- **Network access**: Required for Gemini API and Dropbox (if enabled)
- **Subprocess execution**: Runs workflow.py as subprocess with inherited environment

## Integration with Existing Workflow

The agent system integrates seamlessly with your existing campaign automation:

1. **No changes to workflow.py**: Works with existing workflow as-is
2. **Dropbox mode enabled**: Automatically syncs input/output folders
3. **All features preserved**: Validation, image generation, localization, reporting
4. **Enhanced monitoring**: Adds AI analysis and comprehensive logging

## Future Enhancements

Potential improvements (notification placeholder section in agent log):

- [ ] Email notifications on completion/failure
- [ ] Slack/Teams integration for alerts
- [ ] Webhook support for CI/CD pipelines
- [ ] Web dashboard for monitoring multiple agents
- [ ] Campaign queue management
- [ ] Parallel workflow execution
- [ ] Real-time progress updates
- [ ] Historical analysis and trends

## Support

For issues or questions:
1. Check the log files in `/log` folder
2. Review the Gemini analysis report for insights
3. Check workflow execution log for detailed errors
4. Verify credentials and API keys
5. Ensure all dependencies are installed

## License

Part of the Campaign Automation system.

---

**Generated by Campaign Automation Agent System**
