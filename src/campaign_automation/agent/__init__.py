"""
Agent Module

This module contains agent-related functionality for the campaign automation system.

The agent module provides:
- agent_watcher: Monitors input folder for new YAML files, runs workflow, and analyzes results with Gemini
- process_agent_data: Runs campaign workflow and captures all outputs (logs, reports, etc.)

Usage:
    # Start the YAML file watcher agent (recommended)
    from campaign_automation.agent.agent_watcher import start_watcher
    start_watcher()

    # Or run workflow processing directly
    from campaign_automation.agent.process_agent_data import run_workflow_and_capture
    result = run_workflow_and_capture('input/campaigns/my_campaign.yaml')
"""

from .agent_watcher import start_watcher
from .process_agent_data import run_workflow_and_capture, main as process_main

__all__ = [
    'start_watcher',
    'run_workflow_and_capture',
    'process_main',
]
