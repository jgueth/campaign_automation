# Suppress runpy RuntimeWarning about module import
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
# This is your new "agent": agent_watcher.py

import sys
import time
import subprocess
import os
import json
from pathlib import Path
from datetime import datetime
import google.generativeai as genai
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import credentials from campaign_automation
from ..credentials import get_gemini_api_key

# --- 1. Configuration ---

# Set your folders (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
INPUT_FOLDER = str(PROJECT_ROOT / "input")
OUTPUT_FOLDER = str(PROJECT_ROOT / "output")
LOG_FOLDER = str(PROJECT_ROOT / "log")

# Set the path to your other script
YOUR_APP_SCRIPT = str(Path(__file__).parent / "process_agent_data.py")

# Global flag for Dropbox mode (can be set via command line)
USE_DROPBOX = False

# Get Gemini API Key from credentials
GOOGLE_API_KEY = get_gemini_api_key()
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')  # Using Flash for speed
else:
    print("WARNING: No Gemini API key found in credentials.json")
    model = None

# --- 2. Helper Functions ---

def run_workflow_processor(file_path):
    """
    Runs the process_agent_data script which executes the workflow and captures outputs.
    Returns parsed JSON result containing workflow data.
    """
    print(f"[Agent] Processing YAML file: {file_path}")

    # Find project root dynamically by looking for 'src' directory
    current_path = Path(__file__).resolve()
    project_root = None
    src_path = None

    # Walk up the directory tree until we find the parent of 'src'
    for parent in current_path.parents:
        if (parent / "src").exists():
            project_root = parent
            src_path = parent / "src"
            break

    if not project_root:
        # Fallback: use current working directory
        project_root = Path.cwd()
        src_path = project_root / "src"

    # Build path to process_agent_data.py
    processor_script = src_path / "campaign_automation" / "agent" / "process_agent_data.py"

    # Call the process_agent_data script to run workflow
    command = [
        sys.executable,  # Use same Python interpreter
        str(processor_script),
        "--input", file_path
    ]

    # Add --dropbox flag if enabled
    if USE_DROPBOX:
        command.append("--dropbox")

    # Set up environment with PYTHONPATH pointing to src directory
    import os
    env = os.environ.copy()

    # Add src directory to PYTHONPATH so relative imports work
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = str(src_path) + os.pathsep + env['PYTHONPATH']
    else:
        env['PYTHONPATH'] = str(src_path)

    # Execute the command with extended timeout (workflow can take a while)
    # Capture output silently - all logs go to log files only
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=900,  # 15 minutes timeout for full workflow
        cwd=str(project_root),  # Run from project root
        env=env  # Pass environment with PYTHONPATH
    )

    # Parse the JSON output from the processor
    try:
        # Look for JSON output in stdout (after the result header)
        stdout = result.stdout

        # Find the JSON block (starts after "PROCESS AGENT RESULT (JSON)")
        if "PROCESS AGENT RESULT (JSON)" in stdout:
            json_start = stdout.find("{", stdout.find("PROCESS AGENT RESULT (JSON)"))
            if json_start != -1:
                json_str = stdout[json_start:]
                workflow_data = json.loads(json_str)
                return workflow_data, result.returncode

        # If we couldn't parse JSON, return error
        return {
            "yaml_content": "",
            "workflow_log": stdout + "\n\nSTDERR:\n" + result.stderr,
            "workflow_success": False,
            "report_content": None,
            "report_path": None,
            "workflow_log_path": None,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "error": "Could not parse JSON output from processor"
        }, result.returncode

    except json.JSONDecodeError as e:
        return {
            "yaml_content": "",
            "workflow_log": f"JSON Parse Error: {e}\n\nRaw output:\n{result.stdout}\n\nSTDERR:\n{result.stderr}",
            "workflow_success": False,
            "report_content": None,
            "report_path": None,
            "workflow_log_path": None,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "error": str(e)
        }, result.returncode

def analyze_workflow_with_gemini(filename, workflow_data):
    """
    Sends workflow data (YAML, logs, report) to Gemini for comprehensive review.
    Returns a human-readable analysis of the workflow execution.
    """
    print("[Agent] Analyzing workflow results with Gemini...")

    yaml_content = workflow_data.get("yaml_content", "")
    workflow_log = workflow_data.get("workflow_log", "")
    workflow_success = workflow_data.get("workflow_success", False)
    report_content = workflow_data.get("report_content")

    # Build comprehensive prompt for Gemini
    if workflow_success and report_content:
        # Success case with report available
        prompt = f"""
You are a campaign automation quality analyst. A campaign workflow has been executed.

Please provide a comprehensive, human-readable analysis covering:

1. **Execution Summary**: Brief overview of what happened (2-3 sentences)

2. **CRITICAL VALIDATION - Image Ratio Coverage**:
   - **REQUIREMENT**: Each product MUST have at least 3 different aspect ratios generated
   - Check the YAML configuration for required aspect ratios
   - Check the report and logs to verify images were generated for ALL ratios for EACH product
   - **Status**: [PASS] if all products have 3+ ratios, [FAIL] if any product is missing ratios
   - If FAIL: List which products are missing which ratios
   - This check is MANDATORY and must appear immediately after the execution summary

3. **Campaign Details**: Key information from the YAML (campaign name, products, markets, etc.)

4. **Workflow Status**: Clear verdict on success/failure

5. **Logo Compliance Check Results**:
   - Check the logs for Step 6.5 (Logo Compliance Check)
   - Report: How many images passed vs. failed logo detection
   - Status: [PASS] All passed / [WARNING] Some failed / [ERROR] Check failed
   - If logos missing: List which products/markets had issues
   - This uses OpenCV feature detection to verify logo presence

6. **Quality Assessment**:
   - Were all steps completed successfully?
   - Any warnings or issues in the logs?
   - Quality of generated outputs (based on report)

7. **Recommendations**: Any suggestions for improvement or next steps

Be clear, concise, and actionable. Format your response in a professional report style.

---

**File Processed**: {filename}

**YAML Campaign Configuration**:
```yaml
{yaml_content}
```

**Workflow Execution Log** (excerpt - last 2000 chars):
```
{workflow_log[-2000:] if len(workflow_log) > 2000 else workflow_log}
```

**Campaign Report**:
```markdown
{report_content}
```

---

Please provide your analysis now:
"""
    elif workflow_success and not report_content:
        # Success but no report (unusual case)
        prompt = f"""
You are a campaign automation quality analyst. A campaign workflow has been executed successfully, but no report was generated.

Please provide a human-readable analysis covering:

1. **Execution Summary**: What happened

2. **CRITICAL VALIDATION - Image Ratio Coverage**:
   - **REQUIREMENT**: Each product MUST have at least 3 different aspect ratios generated
   - Check the YAML configuration for required aspect ratios
   - Check the logs to verify images were generated for ALL ratios for EACH product
   - **Status**: [PASS] if all products have 3+ ratios, [FAIL] if any product is missing ratios
   - If FAIL: List which products are missing which ratios
   - Note: Report is missing, so validation relies on YAML and logs only

3. **Campaign Details**: Key information from the YAML

4. **Status**: Success but missing report - why might this be?

5. **Logo Compliance Check Results**:
   - Check the logs for Step 6.5 (Logo Compliance Check)
   - Report: How many images passed vs. failed logo detection
   - Status: [PASS] All passed / [WARNING] Some failed / [ERROR] Check failed
   - If logos missing: List which products/markets had issues
   - Note: Report is missing, rely on log output only

6. **Log Analysis**: Any insights from the execution logs

7. **Recommendations**: What should be checked

---

**File Processed**: {filename}

**YAML Campaign Configuration**:
```yaml
{yaml_content}
```

**Workflow Execution Log** (excerpt - last 2000 chars):
```
{workflow_log[-2000:] if len(workflow_log) > 2000 else workflow_log}
```

---

Please provide your analysis now:
"""
    else:
        # Failure case
        prompt = f"""
You are a campaign automation quality analyst. A campaign workflow has FAILED.

Please provide a human-readable failure analysis covering:

1. **Failure Summary**: What went wrong (clear and concise)

2. **CRITICAL VALIDATION - Image Ratio Coverage**:
   - **REQUIREMENT**: Each product MUST have at least 3 different aspect ratios generated
   - Since the workflow FAILED, check if any images were generated at all
   - Check the YAML configuration for what aspect ratios were expected
   - Check the logs to see if image generation started and for which ratios
   - **Status**: [FAIL] (workflow did not complete)
   - Note: If failure occurred before image generation, state "Not applicable - workflow failed before image generation"

3. **Logo Compliance Check Results**:
   - Check the logs for Step 6.5 (Logo Compliance Check) if it was reached
   - If workflow failed before compliance check: State "Not reached - workflow failed at earlier step"
   - If reached: Report status from logs
   - Status: [PASS] / [WARNING] / [ERROR] / [NOT REACHED]

4. **Root Cause**: Identify the primary cause from logs

5. **Error Details**: Key error messages or stack traces

6. **Impact**: What wasn't completed

7. **Remediation Steps**: Clear action items to fix the issue

Be specific and actionable. Help the user understand what needs to be fixed.

---

**File Processed**: {filename}

**YAML Campaign Configuration** (attempted):
```yaml
{yaml_content if yaml_content else "Could not read YAML file"}
```

**Workflow Execution Log** (excerpt - last 3000 chars):
```
{workflow_log[-3000:] if len(workflow_log) > 3000 else workflow_log}
```

---

Please provide your failure analysis now:
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[Agent Error] Could not contact Gemini API: {e}"

def save_agent_log(filename, workflow_data, gemini_analysis, timestamp):
    """
    Save comprehensive agent log including all data seen by agent and Gemini analysis.
    Also saves a separate markdown report with just the Gemini analysis.
    Returns a tuple: (agent_log_path, gemini_report_path)
    """
    log_folder = Path(LOG_FOLDER)
    log_folder.mkdir(exist_ok=True)

    agent_log_filename = f"agent_{timestamp}.log"
    agent_log_path = log_folder / agent_log_filename

    gemini_report_filename = f"gemini_analysis_{timestamp}.md"
    gemini_report_path = log_folder / gemini_report_filename

    try:
        # Save comprehensive agent log (as before)
        with open(agent_log_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("GEMINI AGENT ANALYSIS LOG\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"YAML File: {filename}\n")
            f.write(f"Workflow Success: {workflow_data.get('workflow_success', False)}\n")
            f.write(f"Workflow Log File: {workflow_data.get('workflow_log_path', 'N/A')}\n")
            f.write(f"Report File: {workflow_data.get('report_path', 'N/A')}\n")
            f.write("\n")

            f.write("=" * 70 + "\n")
            f.write("1. YAML CONFIGURATION (Agent Input)\n")
            f.write("=" * 70 + "\n\n")
            f.write(workflow_data.get('yaml_content', 'No YAML content available'))
            f.write("\n\n")

            f.write("=" * 70 + "\n")
            f.write("2. WORKFLOW EXECUTION LOG (Agent Input)\n")
            f.write("=" * 70 + "\n\n")
            f.write(workflow_data.get('workflow_log', 'No log available'))
            f.write("\n\n")

            if workflow_data.get('report_content'):
                f.write("=" * 70 + "\n")
                f.write("3. CAMPAIGN REPORT (Agent Input)\n")
                f.write("=" * 70 + "\n\n")
                f.write(workflow_data['report_content'])
                f.write("\n\n")
            else:
                f.write("=" * 70 + "\n")
                f.write("3. CAMPAIGN REPORT (Agent Input)\n")
                f.write("=" * 70 + "\n\n")
                f.write("No report generated (expected in error scenarios)\n\n")

            f.write("=" * 70 + "\n")
            f.write("4. GEMINI AI ANALYSIS & REVIEW\n")
            f.write("=" * 70 + "\n\n")
            f.write(gemini_analysis)
            f.write("\n\n")

            f.write("=" * 70 + "\n")
            f.write("5. NOTIFICATION (Placeholder)\n")
            f.write("=" * 70 + "\n\n")
            f.write("[PLACEHOLDER] Notification System\n")
            f.write("  Status: Not yet implemented\n")
            f.write("  Future: This section will contain notification details\n")
            f.write("           (email, Slack, webhook, etc.)\n")
            if workflow_data.get('workflow_success'):
                f.write("  Action: Would send SUCCESS notification\n")
            else:
                f.write("  Action: Would send FAILURE ALERT notification\n")
            f.write("\n")
            f.write("For now, notifications are logged here only.\n")
            f.write("Review the Gemini analysis above for workflow status.\n")
            f.write("\n")

            f.write("=" * 70 + "\n")
            f.write("END OF AGENT LOG\n")
            f.write("=" * 70 + "\n")

        print(f"[Agent] Agent log saved: {agent_log_path}")

        # Save separate Gemini analysis as markdown report
        with open(gemini_report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Campaign Workflow Analysis\n\n")
            f.write(f"**Generated:** {timestamp}\n\n")
            f.write(f"**YAML File:** {filename}\n\n")
            f.write(f"**Workflow Status:** {'[SUCCESS]' if workflow_data.get('workflow_success') else '[FAILED]'}\n\n")
            f.write(f"---\n\n")
            f.write(gemini_analysis)
            f.write("\n\n---\n\n")
            f.write(f"**Related Files:**\n")
            f.write(f"- Workflow Log: `{workflow_data.get('workflow_log_path', 'N/A')}`\n")
            f.write(f"- Agent Log: `{agent_log_path}`\n")
            if workflow_data.get('report_path'):
                f.write(f"- Campaign Report: `{workflow_data.get('report_path')}`\n")

        print(f"[Agent] Gemini analysis report saved: {gemini_report_path}")

        return str(agent_log_path), str(gemini_report_path)

    except Exception as e:
        print(f"[Agent] ERROR: Could not save agent log: {e}")
        return None, None

def send_notification(summary):
    """
    Placeholder function to send you the alert.
    For now, it just prints to the console.
    """
    # TODO: Replace this with your preferred notification

    print("\n" + "="*70)
    print("GEMINI AGENT NOTIFICATION")
    print("="*70)
    print(summary)
    print("="*70 + "\n")

    # --- Example: Send an email (uncomment to use) ---
    # import smtplib
    # from email.message import EmailMessage
    # msg = EmailMessage()
    # msg.set_content(summary)
    # msg['Subject'] = 'Campaign Workflow Alert!'
    # msg['From'] = 'your-agent@example.com'
    # msg['To'] = 'your-email@example.com'
    # s = smtplib.SMTP('your-smtp-server.com')
    # s.send_message(msg)
    # s.quit()

# --- 3. The Watchdog Event Handler ---

class YamlEventHandler(FileSystemEventHandler):
    def __init__(self):
        """Initialize handler with set to track processed files."""
        super().__init__()
        self.processed_files = set()  # Track processed files to avoid duplicates

    def process_yaml_file(self, file_path):
        """
        Process a YAML file: run workflow, analyze with Gemini, save logs.
        """
        filename = os.path.basename(file_path)

        # Check if already processed
        if file_path in self.processed_files:
            return

        # Mark as processed
        self.processed_files.add(file_path)

        # Log YAML file detection
        print(f"\n[Agent] [DETECTED] YAML file: {filename}")
        print(f"[Agent] [PROCESSING] Starting workflow execution...")

        # Wait a moment to ensure the file is fully written
        time.sleep(1)

        # 1. Run the workflow processor (which runs workflow.py and captures everything)
        try:
            workflow_data, _ = run_workflow_processor(file_path)
            timestamp = workflow_data.get('timestamp', datetime.now().strftime("%Y%m%d_%H%M%S"))

            if workflow_data.get('workflow_success'):
                print(f"[Agent] [SUCCESS] Workflow completed successfully")
            else:
                print(f"[Agent] [FAILED] Workflow execution failed")

        except subprocess.TimeoutExpired:
            print(f"[Agent] [TIMEOUT] Workflow execution exceeded timeout")
            workflow_data = {
                "yaml_content": "",
                "workflow_log": "ERROR: Workflow execution timeout",
                "workflow_success": False,
                "report_content": None,
                "report_path": None,
                "workflow_log_path": None,
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "error": "Timeout"
            }
            timestamp = workflow_data['timestamp']
        except Exception as e:
            print(f"[Agent] [ERROR] Failed to run workflow processor: {e}")
            workflow_data = {
                "yaml_content": "",
                "workflow_log": f"FATAL ERROR: {e}",
                "workflow_success": False,
                "report_content": None,
                "report_path": None,
                "workflow_log_path": None,
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "error": str(e)
            }
            timestamp = workflow_data['timestamp']

        # 2. Analyze workflow data with Gemini
        print(f"[Agent] [ANALYZING] Sending to Gemini for review...")
        gemini_analysis = analyze_workflow_with_gemini(filename, workflow_data)

        # 3. Save comprehensive agent log and separate Gemini markdown report
        print(f"[Agent] [LOGGING] Saving agent log and Gemini analysis report...")
        agent_log_path, gemini_report_path = save_agent_log(filename, workflow_data, gemini_analysis, timestamp)

        # 4. Send notification (currently just console output)
        send_notification(gemini_analysis)

        # 5. Open the Gemini markdown report in default application
        if gemini_report_path:
            try:
                import platform
                import subprocess as sp

                print(f"[Agent] [OPENING] Opening Gemini analysis report...")

                if platform.system() == 'Windows':
                    os.startfile(gemini_report_path)
                elif platform.system() == 'Darwin':  # macOS
                    sp.run(['open', gemini_report_path])
                else:  # Linux
                    sp.run(['xdg-open', gemini_report_path])

            except Exception as e:
                print(f"[Agent] [WARNING] Could not open report automatically: {e}")

        # 6. Summary
        print(f"[Agent] [COMPLETE] Processing finished for {filename}")
        print(f"[Agent]   Workflow Log: {workflow_data.get('workflow_log_path', 'N/A')}")
        print(f"[Agent]   Agent Log: {agent_log_path or 'N/A'}")
        print(f"[Agent]   Gemini Report: {gemini_report_path or 'N/A'}")
        print()

    def on_created(self, event):
        """
        Called when a new file is created in the input folder.
        Only processes .yaml and .yml files, logs all events.
        """
        if event.is_directory:
            # Log directory creation but don't process
            dirname = os.path.basename(event.src_path)
            print(f"[Agent] [EVENT] Directory created: {dirname}")
            return

        file_path = event.src_path
        filename = os.path.basename(file_path)

        # Log all file events
        print(f"[Agent] [EVENT] File created: {filename}")

        # Check if it's a YAML file
        if not (filename.endswith('.yaml') or filename.endswith('.yml')):
            print(f"[Agent] [IGNORED] Not a YAML file")
            return

        # Process the YAML file
        self.process_yaml_file(file_path)

    def on_modified(self, event):
        """
        Called when a file is modified.
        On Windows, this often fires for new files, so we process YAML files here too.
        """
        if event.is_directory:
            return

        file_path = event.src_path
        filename = os.path.basename(file_path)

        # Check if it's a YAML file
        if not (filename.endswith('.yaml') or filename.endswith('.yml')):
            return

        # On Windows, modified can fire for new files, so process it
        # (but only once due to processed_files tracking)
        self.process_yaml_file(file_path)

# --- 4. Main Execution ---

def start_watcher():
    """
    Main function to start the YAML file watcher agent.
    """
    global USE_DROPBOX

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Campaign Automation Agent")
    parser.add_argument("--dropbox", action="store_true", help="Enable Dropbox sync")
    args = parser.parse_args()

    # Set Dropbox mode
    USE_DROPBOX = args.dropbox

    if not GOOGLE_API_KEY:
        print("[Agent] [ERROR] Please configure Gemini API key in credentials.json")
        sys.exit(1)

    if not os.path.exists(INPUT_FOLDER):
        print(f"[Agent] [ERROR] Input folder does not exist: {INPUT_FOLDER}")
        sys.exit(1)

    # Ensure log folder exists
    Path(LOG_FOLDER).mkdir(exist_ok=True)

    print("=" * 70)
    print("[Agent] Starting Gemini Campaign Workflow Agent...")
    print("=" * 70)
    print(f"[Agent] Watching folder: {INPUT_FOLDER}")
    print(f"[Agent] Watching subfolders: YES (recursive)")
    print(f"[Agent] File types: .yaml, .yml")
    print(f"[Agent] Workflow processor: {YOUR_APP_SCRIPT}")
    print(f"[Agent] Log folder: {LOG_FOLDER}")
    print(f"[Agent] Dropbox mode: {'ENABLED' if USE_DROPBOX else 'DISABLED'}")
    print(f"[Agent] Status: READY - Waiting for YAML files...")
    print("=" * 70)
    print()

    event_handler = YamlEventHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_FOLDER, recursive=True)

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Agent] [SHUTDOWN] Stopping agent...")
        observer.stop()
    observer.join()
    print("[Agent] [SHUTDOWN] Agent stopped successfully.")


if __name__ == "__main__":
    start_watcher()
