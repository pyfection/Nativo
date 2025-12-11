"""
Prompt execution endpoints for oracle and coder.
"""

import os
import re
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
from fastapi import HTTPException

from .models import PromptRequest
from .utils import build_resume_value
from .chat_history import save_chat_message, save_action


async def execute_oracle_prompt(request: PromptRequest):
    """
    Execute cursor-agent command for questions (oracle mode).
    Uses chat ID: {repo_name}/{branch_name}[/{task_id}]/oracle
    Does NOT use --force flag, allowing questions while coder is busy.
    Stores chat history in JSON file with UTC timestamps.

    Args:
        request: PromptRequest with prompt text

    Returns:
        Command output as string
    """
    try:
        resume_value = build_resume_value("oracle")

        # Save user prompt to chat history
        save_chat_message(resume_value, "user", request.prompt)

        # Build command: cursor-agent -p --resume="{resume_value}" "{prompt}"
        # Note: No --force flag for oracle (questions)
        cmd = ["cursor-agent", "-p", f"--resume={resume_value}", request.prompt]

        # Check if cursor-agent is available
        cursor_agent_path = shutil.which("cursor-agent")
        if not cursor_agent_path:
            error_msg = "cursor-agent command not found in PATH. Please ensure Cursor CLI is installed."
            save_chat_message(resume_value, "oracle", error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        # Execute command
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=os.getcwd(),
            )
        except FileNotFoundError as e:
            error_msg = f"Command not found: {cmd[0]}. PATH: {os.environ.get('PATH', 'not set')}. Error: {str(e)}"
            save_chat_message(resume_value, "oracle", error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        if result.returncode != 0:
            # Save error to chat history
            error_output = (
                result.stderr.strip() or result.stdout.strip() or "No error output"
            )
            error_text = f"Error (exit code {result.returncode}): {error_output}"
            save_chat_message(resume_value, "oracle", error_text)
            raise HTTPException(
                status_code=500,
                detail=f"Command failed (exit code {result.returncode}): {error_output}",
            )

        # Save oracle response to chat history
        save_chat_message(resume_value, "oracle", result.stdout)

        # Get UTC timestamp (same format as chat history)
        timestamp = datetime.now(timezone.utc).isoformat()

        return {
            "output": result.stdout,
            "exit_code": result.returncode,
            "timestamp": timestamp,
        }
    except subprocess.TimeoutExpired:
        resume_value = build_resume_value("oracle")
        error_text = "Command execution timed out"
        save_chat_message(resume_value, "oracle", error_text)
        raise HTTPException(status_code=504, detail="Command execution timed out")
    except HTTPException:
        # Re-raise HTTP exceptions (already handled above)
        raise
    except Exception as e:
        resume_value = build_resume_value("oracle")
        error_type = type(e).__name__
        error_msg = str(e) or "Unknown error"
        error_text = f"Error executing command ({error_type}): {error_msg}"
        save_chat_message(resume_value, "oracle", error_text)
        raise HTTPException(
            status_code=500,
            detail=f"Error executing command ({error_type}): {error_msg}",
        )


def _parse_git_diff_stats(diff_output: str) -> list[str]:
    """
    Parse git diff --stat output to extract file changes.

    Args:
        diff_output: Output from git diff --stat

    Returns:
        List of file change strings in format "path/to/file.py +N-M"
    """
    file_changes = []
    for line in diff_output.strip().split("\n"):
        if "|" in line and not line.startswith(" "):
            parts = line.split("|")
            if len(parts) == 2:
                file_path = parts[0].strip()
                stats = parts[1].strip()

                # Parse stats: format is usually "N +++++---" or "N +M-N" or just "N"
                # Extract numbers and count + and - signs
                additions = 0
                deletions = 0

                # Try to match format like "5 +++++" or "3 +--" or "2 +5-3"
                # First, try to extract explicit numbers like "+5-3"
                explicit_match = re.search(r"\+(\d+)-(\d+)", stats)
                if explicit_match:
                    additions = int(explicit_match.group(1))
                    deletions = int(explicit_match.group(2))
                else:
                    # Count + and - signs
                    additions = stats.count("+")
                    deletions = stats.count("-")

                if additions > 0 or deletions > 0:
                    file_changes.append(f"{file_path} +{additions}-{deletions}")

    return file_changes


async def execute_coder_prompt(request: PromptRequest):
    """
    Execute cursor-agent command for programming (coder mode).
    Uses chat ID: {repo_name}/{branch_name}[/{task_id}]/coder
    Uses --force flag to allow code execution.
    Stores chat history in JSON file with UTC timestamps.

    Args:
        request: PromptRequest with prompt text

    Returns:
        Command output as string
    """
    try:
        resume_value = build_resume_value("coder")

        # Save user prompt to chat history
        save_chat_message(resume_value, "user", request.prompt)

        # Build command: cursor-agent -p --resume="{resume_value}" --force "{prompt}"
        cmd = [
            "cursor-agent",
            "-p",
            f"--resume={resume_value}",
            "--force",
            request.prompt,
        ]

        # Check if cursor-agent is available
        cursor_agent_path = shutil.which("cursor-agent")
        if not cursor_agent_path:
            error_msg = "cursor-agent command not found in PATH. Please ensure Cursor CLI is installed."
            save_chat_message(resume_value, "coder", error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        # Execute command
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=os.getcwd(),
            )
        except FileNotFoundError as e:
            error_msg = f"Command not found: {cmd[0]}. PATH: {os.environ.get('PATH', 'not set')}. Error: {str(e)}"
            save_chat_message(resume_value, "coder", error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        if result.returncode != 0:
            # Save error to chat history
            error_output = (
                result.stderr.strip() or result.stdout.strip() or "No error output"
            )
            error_text = f"Error (exit code {result.returncode}): {error_output}"
            save_chat_message(resume_value, "coder", error_text)
            raise HTTPException(
                status_code=500,
                detail=f"Command failed (exit code {result.returncode}): {error_output}",
            )

        # Save coder response to chat history
        save_chat_message(resume_value, "coder", result.stdout)

        # Check for file changes and add action if files changed
        repo_dir = Path("/workspace/repo")
        if repo_dir.exists():
            # Get git status before (we'll compare with what was saved previously)
            # For now, just check current status
            git_status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if git_status_result.returncode == 0 and git_status_result.stdout.strip():
                # Get detailed diff stats
                git_diff_result = subprocess.run(
                    ["git", "diff", "--stat"],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if git_diff_result.returncode == 0 and git_diff_result.stdout.strip():
                    # Parse diff stats to get file changes
                    file_changes = _parse_git_diff_stats(git_diff_result.stdout)

                    if file_changes:
                        # Add action with file changes
                        changes_text = "\n".join(file_changes)
                        save_action(resume_value, f"Files changed:\n{changes_text}")

        # Get UTC timestamp (same format as chat history)
        timestamp = datetime.now(timezone.utc).isoformat()

        return {
            "output": result.stdout,
            "exit_code": result.returncode,
            "timestamp": timestamp,
        }
    except subprocess.TimeoutExpired:
        resume_value = build_resume_value("coder")
        error_text = "Command execution timed out"
        save_chat_message(resume_value, "coder", error_text)
        raise HTTPException(status_code=504, detail="Command execution timed out")
    except HTTPException:
        # Re-raise HTTP exceptions (already handled above)
        raise
    except Exception as e:
        resume_value = build_resume_value("coder")
        error_type = type(e).__name__
        error_msg = str(e) or "Unknown error"
        error_text = f"Error executing command ({error_type}): {error_msg}"
        save_chat_message(resume_value, "coder", error_text)
        raise HTTPException(
            status_code=500,
            detail=f"Error executing command ({error_type}): {error_msg}",
        )
