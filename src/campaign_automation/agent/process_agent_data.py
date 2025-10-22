"""
Process Agent Data Module

This module runs the campaign workflow with a given YAML file and captures all outputs.
It's designed to be called by the agent_watcher as a subprocess.

Usage:
    python -m campaign_automation.agent.process_agent_data --input <yaml_file>
"""

import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json


def run_workflow_and_capture(yaml_path: str, use_dropbox: bool = False) -> dict:
    """
    Run the campaign workflow with the given YAML file and capture outputs.

    Args:
        yaml_path: Path to the YAML campaign file

    Returns:
        dict containing:
            - yaml_content: The YAML file content as string
            - workflow_log: Complete stdout/stderr from workflow execution
            - workflow_success: Boolean indicating if workflow succeeded
            - report_content: Content of campaign_report.md (if exists, else None)
            - report_path: Path to the report file (if exists, else None)
            - workflow_log_path: Path where workflow log was saved
            - timestamp: Timestamp of execution
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Read the YAML file content
    yaml_content = ""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
    except Exception as e:
        return {
            "yaml_content": "",
            "workflow_log": f"ERROR: Failed to read YAML file: {e}",
            "workflow_success": False,
            "report_content": None,
            "report_path": None,
            "workflow_log_path": None,
            "timestamp": timestamp,
            "error": str(e)
        }

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

    # Run workflow as a module (python -m campaign_automation.workflow)
    # This allows relative imports to work properly
    command = [
        sys.executable,  # Use the same Python interpreter
        "-m",
        "campaign_automation.workflow",
        yaml_path
    ]

    # Add --dropbox flag if requested
    if use_dropbox:
        command.append("--dropbox")

    print(f"[Process Agent] Running workflow with: {yaml_path}")
    print(f"[Process Agent] Command: {' '.join(command)}")
    print(f"[Process Agent] Working directory: {project_root}")
    print(f"[Process Agent] Dropbox mode: {'ENABLED' if use_dropbox else 'DISABLED'}")
    print()

    # Set up environment with PYTHONPATH pointing to src directory
    import os
    env = os.environ.copy()

    # Add src directory to PYTHONPATH so relative imports work
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = str(src_path) + os.pathsep + env['PYTHONPATH']
    else:
        env['PYTHONPATH'] = str(src_path)

    # Execute workflow and capture all output (no live streaming to console)
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=600,  # 10 minute timeout
            cwd=str(project_root),  # Run from project root
            env=env  # Pass environment with PYTHONPATH
        )

        # Combine stdout and stderr for complete log
        workflow_log = ""
        if result.stdout:
            workflow_log += "=== STDOUT ===\n" + result.stdout + "\n"
        if result.stderr:
            workflow_log += "=== STDERR ===\n" + result.stderr + "\n"

        workflow_success = (result.returncode == 0)

    except subprocess.TimeoutExpired:
        workflow_log = "ERROR: Workflow execution timeout (exceeded 10 minutes)"
        workflow_success = False
    except Exception as e:
        workflow_log = f"ERROR: Failed to execute workflow: {e}"
        workflow_success = False

    # Save workflow log to file with timestamp
    log_folder = Path("log")
    log_folder.mkdir(exist_ok=True)

    workflow_log_filename = f"workflow_{timestamp}.log"
    workflow_log_path = log_folder / workflow_log_filename

    try:
        with open(workflow_log_path, 'w', encoding='utf-8') as f:
            f.write(f"Campaign Workflow Execution Log\n")
            f.write(f"{'=' * 70}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"YAML File: {yaml_path}\n")
            f.write(f"Success: {workflow_success}\n")
            f.write(f"{'=' * 70}\n\n")
            f.write(workflow_log)

        print(f"[Process Agent] Workflow log saved: {workflow_log_path}")
    except Exception as e:
        print(f"[Process Agent] WARNING: Could not save workflow log: {e}")

    # Try to read the campaign report (if it exists)
    report_content = None
    report_path = None

    # Look for report in output/{campaign_id}/campaign_report.md
    # Try to find the campaign ID from the output folder
    output_dir = Path("output")
    if output_dir.exists():
        # Get all subdirectories in output (campaign folders)
        campaign_dirs = [d for d in output_dir.iterdir() if d.is_dir()]

        # Try each campaign directory
        for campaign_dir in campaign_dirs:
            potential_report = campaign_dir / "campaign_report.md"
            if potential_report.exists():
                try:
                    with open(potential_report, 'r', encoding='utf-8') as f:
                        report_content = f.read()
                    report_path = str(potential_report)
                    print(f"[Process Agent] Campaign report found: {report_path}")
                    break  # Found the report, stop looking
                except Exception as e:
                    print(f"[Process Agent] WARNING: Could not read report at {potential_report}: {e}")

    if report_content is None:
        print(f"[Process Agent] No campaign report found (this is expected if workflow failed)")

    # Return all captured data
    return {
        "yaml_content": yaml_content,
        "workflow_log": workflow_log,
        "workflow_success": workflow_success,
        "report_content": report_content,
        "report_path": report_path,
        "workflow_log_path": str(workflow_log_path),
        "timestamp": timestamp
    }


def main():
    """
    Command-line interface for running workflow and capturing outputs.
    Outputs JSON result to stdout for the agent to capture.
    """
    parser = argparse.ArgumentParser(description="Run campaign workflow and capture outputs.")
    parser.add_argument("--input", required=True, help="Path to the YAML campaign file.")
    parser.add_argument("--dropbox", action="store_true", help="Enable Dropbox sync for workflow.")
    args = parser.parse_args()

    try:
        # Run workflow and capture all outputs
        result = run_workflow_and_capture(args.input, use_dropbox=args.dropbox)

        # Output result as JSON to stdout (agent will capture this)
        print("\n" + "="*70)
        print("PROCESS AGENT RESULT (JSON)")
        print("="*70)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Exit with appropriate code
        sys.exit(0 if result["workflow_success"] else 1)

    except Exception as e:
        # Print errors to stderr so agent can detect failures
        error_result = {
            "yaml_content": "",
            "workflow_log": f"FATAL ERROR: {e}",
            "workflow_success": False,
            "report_content": None,
            "report_path": None,
            "workflow_log_path": None,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "error": str(e)
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
