"""
MCP server sketch wrapping your campaign workflow tools.

Install deps (one-time):
    pip install "mcp[cli]" google-generativeai watchdog pydantic

Dev run / inspect:
    mcp dev mcp_server_sketch.py --with google-generativeai --with watchdog

Install into an MCP client (e.g., Claude Desktop):
    mcp install mcp_server_sketch.py --name "Campaign Workflow MCP"
    # Optionally pass env vars / .env
    # mcp install mcp_server_sketch.py -f .env -v GOOGLE_API_KEY=... 

Notes:
- This sketch *delegates* to your existing functions in agent_watcher.py:
  run_workflow_processor, analyze_workflow_with_gemini, save_agent_log.  
- Gemini remains an internal implementation detail. MCP exposes *tools*.
- Adjust the import path (PROJECT_SRC) to match your repo layout.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP, Context
from typing import Optional, Any, Dict, Tuple
from pathlib import Path
import os
import json
import tempfile
import datetime as dt

# --- Locate your project and import your existing functions -----------------
# Update this if your repo structure differs. This assumes this file lives
# *outside* your src/ tree. If it's already inside src/, you can remove the
# sys.path hack and use a normal import.
import sys
PROJECT_ROOT = Path(__file__).resolve().parent
# Try common patterns; tweak as needed
CANDIDATE_SRC_DIRS = [
    PROJECT_ROOT / "src",
    PROJECT_ROOT.parent / "src",
    PROJECT_ROOT / "campaign_automation" / "agent",
]
for _p in CANDIDATE_SRC_DIRS:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# Now try to import from your codebase
# If your module path is different, fix below (e.g., campaign_automation.agent.agent_watcher)
try:
    from campaign_automation.agent.agent_watcher import (
        run_workflow_processor,
        analyze_workflow_with_gemini,
        save_agent_log,
    )
except Exception:
    # Fallback: allow placing this file next to agent_watcher.py for quick trials
    try:
        from agent_watcher import run_workflow_processor, analyze_workflow_with_gemini, save_agent_log  # type: ignore
    except Exception as e:
        raise ImportError(
            "Could not import your agent functions. Edit imports near the top of mcp_server_sketch.py to match your project layout."
        ) from e

# --- Configure folders to mirror your watcher defaults ----------------------
# These should match agent_watcher.py, but we keep them decoupled here.
PROJECT_ROOT_FALLBACK = Path.cwd()
INPUT_FOLDER = os.environ.get("WORKFLOW_INPUT", str(PROJECT_ROOT_FALLBACK / "input"))
LOG_FOLDER = os.environ.get("WORKFLOW_LOG", str(PROJECT_ROOT_FALLBACK / "log"))
Path(LOG_FOLDER).mkdir(parents=True, exist_ok=True)

# --- MCP server --------------------------------------------------------------
mcp = FastMCP("Campaign Workflow MCP", dependencies=["google-generativeai", "watchdog"])

# Utility: write inline YAML to a temp file when the client prefers passing content

def _write_inline_yaml(yaml_text: str, filename_hint: str | None = None) -> str:
    suffix = ".yaml" if not filename_hint else ("_" + Path(filename_hint).stem + ".yaml")
    fd, tmp_path = tempfile.mkstemp(prefix="mcp_yaml_", suffix=suffix, dir=INPUT_FOLDER if os.path.isdir(INPUT_FOLDER) else None)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(yaml_text)
    return tmp_path


@mcp.tool()
def run_workflow(
    input_path: Optional[str] = None,
    inline_yaml: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the campaign workflow and return structured results.

    Args:
        input_path: Path to a YAML file to process.
        inline_yaml: Raw YAML content. If provided, the server writes it to a temp file and uses that.

    Returns:
        A JSON-serializable dict mirroring the structure returned by run_workflow_processor: 
        {
          "yaml_content": str,
          "workflow_log": str,
          "workflow_success": bool,
          "report_content": Optional[str],
          "report_path": Optional[str],
          "workflow_log_path": Optional[str],
          "timestamp": str,
          ...
        }
    """
    if not input_path and not inline_yaml:
        raise ValueError("Provide either input_path or inline_yaml")

    if inline_yaml:
        input_path = _write_inline_yaml(inline_yaml, filename_hint="session")

    data, rc = run_workflow_processor(str(input_path))
    # Attach return code for debugging/telemetry
    data = dict(data or {})
    data["return_code"] = rc
    return data


@mcp.tool()
def analyze_workflow(
    filename: str,
    workflow_data: Dict[str, Any],
) -> str:
    """Analyze a completed workflow using your existing Gemini-powered logic.

    Args:
        filename: A name shown in the analysis (use the YAML file name if available).
        workflow_data: The dict returned from run_workflow (yaml, logs, flags, report).

    Returns:
        Markdown text produced by analyze_workflow_with_gemini().
    """
    return analyze_workflow_with_gemini(filename, workflow_data)


@mcp.tool()
def save_analysis(
    filename: str,
    workflow_data: Dict[str, Any],
    gemini_analysis_markdown: str,
    timestamp: Optional[str] = None,
) -> Dict[str, str]:
    """Persist the combined agent log and a separate Gemini analysis report.

    Args:
        filename: Display name (usually the YAML file name).
        workflow_data: The dict from run_workflow.
        gemini_analysis_markdown: The Markdown string to save as a report.
        timestamp: Optional custom timestamp. Defaults to current time if omitted.

    Returns:
        {"agent_log_path": str, "gemini_report_path": str}
    """
    ts = timestamp or dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    agent_log_path, gemini_report_path = save_agent_log(filename, workflow_data, gemini_analysis_markdown, ts)
    return {
        "agent_log_path": agent_log_path or "",
        "gemini_report_path": gemini_report_path or "",
    }


@mcp.tool()
def quickrun(
    inline_yaml: str,
    filename_hint: Optional[str] = None,
    save: bool = True,
    ctx: Context | None = None,
) -> Dict[str, Any]:
    """Convenience tool: run → analyze → (optionally) save in one call.

    Returns a compact summary with file paths if saved.
    """
    if ctx:
        ctx.info("Writing inline YAML…")
    tmp_path = _write_inline_yaml(inline_yaml, filename_hint)

    if ctx:
        ctx.info("Running workflow processor…")
    data, rc = run_workflow_processor(tmp_path)

    name = Path(filename_hint or Path(tmp_path).name).name
    if ctx:
        ctx.info("Calling Gemini analysis…")
    analysis = analyze_workflow_with_gemini(name, data)

    saved = {"agent_log_path": "", "gemini_report_path": ""}
    if save:
        if ctx:
            ctx.info("Saving logs & report…")
        agent_log_path, gemini_report_path = save_agent_log(name, data, analysis, data.get("timestamp"))
        saved = {"agent_log_path": agent_log_path or "", "gemini_report_path": gemini_report_path or ""}

    return {
        "filename": name,
        "return_code": rc,
        "workflow_success": bool(data.get("workflow_success")),
        "timestamp": data.get("timestamp"),
        "analysis_preview": (analysis[:500] + ("…" if len(analysis) > 500 else "")),
        **saved,
    }


# Helpful resource: latest reports directory listing (for easy retrieval by clients)
@mcp.resource("reports://latest")
def list_reports() -> str:
    """Return a newline-separated list of files in the log folder (reports & logs)."""
    paths = []
    if os.path.isdir(LOG_FOLDER):
        for p in sorted(Path(LOG_FOLDER).glob("*")):
            paths.append(str(p))
    return "\n".join(paths)


# Helpful prompt: let clients request a standardized review prompt if they want
@mcp.prompt()
def review_prompt() -> str:
    return (
        "You are a campaign automation quality analyst. Review the provided YAML, logs, and report.\n"
        "Summarize execution, status, issues, and actionable next steps."
    )


if __name__ == "__main__":
    # Run with: python mcp_server_sketch.py
    # Or: mcp run mcp_server_sketch.py
    mcp.run()
