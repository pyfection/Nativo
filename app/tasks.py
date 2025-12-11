"""
Task management endpoints.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional
from fastapi import HTTPException

from .models import StartTaskRequest, FinishTaskRequest, PromptRequest
from .utils import (
    validate_environment_variables,
    get_current_task_id,
    build_resume_value,
)
from .chat_history import load_chat_history, save_action
from .git_config import configure_git_user, configure_github_auth
from .git_commit import commit_changes
from .git_push import check_branch_exists_remote, check_commit_pushed, push_branch
from . import prompts

logger = logging.getLogger(__name__)


async def start_task(request: StartTaskRequest):
    """
    Start a new task by setting the task ID.
    Creates a new chat session for the coder with the task ID.
    Fails if a different task is already active (safeguard to prevent multiple tasks).

    Args:
        request: StartTaskRequest with task_id

    Returns:
        Success message with chat ID
    """
    # Check if a task is already active
    current_task_id = get_current_task_id()

    if current_task_id:
        # If the same task_id is being started again, allow it (idempotency)
        # This handles cases where start_task is called multiple times for the same task
        if current_task_id == request.task_id:
            logger.info(
                f"Task {request.task_id} is already active. Returning success (idempotent call)."
            )
            repo_name, branch_name = validate_environment_variables()
            chat_id = f"{repo_name}/{branch_name}/{request.task_id}/coder"
            return {
                "status": "already_started",
                "task_id": request.task_id,
                "chat_id": chat_id,
                "message": f"Task {request.task_id} is already active. Chat ID: {chat_id}",
            }
        else:
            # Different task_id trying to start while another task is active
            # This is the safeguard: prevent multiple tasks from using the same environment
            raise HTTPException(
                status_code=400,
                detail=(
                    f"A different task is already active (task_id: {current_task_id}). "
                    f"Cannot start task {request.task_id} until the current task is finished. "
                    f"Please call /finish_task or /clear_task for task {current_task_id} first."
                ),
            )

    # No task active (new environment) or same task_id - proceed with starting
    # Set task ID in file
    task_file = Path("/app/task_id.txt")
    try:
        task_file.write_text(request.task_id, encoding="utf-8")
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to set task ID: {str(e)}")

    # Build chat ID for coder
    repo_name, branch_name = validate_environment_variables()

    chat_id = f"{repo_name}/{branch_name}/{request.task_id}/coder"

    logger.info(f"Task {request.task_id} started successfully. Chat ID: {chat_id}")

    return {
        "status": "started",
        "task_id": request.task_id,
        "chat_id": chat_id,
        "message": f"Task {request.task_id} started. New coder chat ID: {chat_id}",
    }


async def clear_task():
    """
    Clear the current task ID (rollback operation).
    Used when task start fails after TASK_ID was set.

    Returns:
        Success message
    """
    current_task_id = get_current_task_id()
    if not current_task_id:
        return {"status": "cleared", "message": "No active task to clear"}

    # Remove task ID file
    task_file = Path("/app/task_id.txt")
    if task_file.exists():
        try:
            task_file.unlink()
            return {
                "status": "cleared",
                "task_id": current_task_id,
                "message": f"Task {current_task_id} cleared",
            }
        except IOError as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to clear task ID: {str(e)}"
            )

    return {"status": "cleared", "message": "Task ID file not found"}


async def get_current_task():
    """
    Get current task ID from environment.

    Returns:
        Current task ID if set, None otherwise
    """
    current_task_id = get_current_task_id()
    return {"task_id": current_task_id, "has_task": current_task_id is not None}


async def get_chat_history(chat_type: str = "oracle", task_id: Optional[str] = None):
    """
    Get chat history for oracle or coder chat.

    Query parameters:
        chat_type: Either 'oracle' or 'coder' (default: 'oracle')
        task_id: Optional task ID for coder chat (only used if chat_type is 'coder')

    Returns:
        List of chat messages with timestamp, sender, and text
    """
    if chat_type not in ["oracle", "coder"]:
        raise HTTPException(
            status_code=400, detail="chat_type must be either 'oracle' or 'coder'"
        )

    # Build chat ID based on chat_type and task_id
    repo_name, branch_name = validate_environment_variables()

    # Build chat ID
    if chat_type == "oracle":
        chat_id = f"{repo_name}/{branch_name}/oracle"
    else:  # coder
        if task_id:
            chat_id = f"{repo_name}/{branch_name}/{task_id}/coder"
        else:
            # Use current task_id if available, otherwise use base coder chat
            current_task_id = get_current_task_id()
            if current_task_id:
                chat_id = f"{repo_name}/{branch_name}/{current_task_id}/coder"
            else:
                chat_id = f"{repo_name}/{branch_name}/coder"

    # Load chat history
    history = load_chat_history(chat_id)

    return {
        "chat_id": chat_id,
        "chat_type": chat_type,
        "task_id": task_id or get_current_task_id() if chat_type == "coder" else None,
        "messages": history,
        "message_count": len(history),
    }


async def commit_and_push_with_cursor(
    repo_dir: Path,
    repo_name: str,
    branch_name: str,
    current_task_id: str,
    git_user_name: str,
    git_user_email: str,
) -> dict:
    """
    Commit uncommitted changes using Cursor to generate a meaningful commit message,
    then push to remote. Returns commit ID and commit message.

    Args:
        repo_dir: Path to repository directory
        repo_name: Repository name
        branch_name: Branch name
        current_task_id: Current task ID
        git_user_name: Git user.name for commits
        git_user_email: Git user.email for commits

    Returns:
        Dictionary with:
            - commit_id: Commit SHA (or None if no changes)
            - commit_message: Commit message (or None if no changes)
            - error: Error message if commit/push failed (or None if successful)
    """
    # Configure git user
    configure_git_user(repo_dir, git_user_name, git_user_email)

    # Check if there are uncommitted changes
    status_result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=10,
    )

    has_changes = bool(status_result.stdout.strip())

    if not has_changes:
        # No changes to commit
        return {
            "commit_id": None,
            "commit_message": None,
            "error": None,
        }

    # Stage all changes
    add_result = subprocess.run(
        ["git", "add", "-A"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=10,
    )

    if add_result.returncode != 0:
        error_msg = f"Failed to stage changes: {add_result.stderr}"
        logger.error(f"ERROR: {error_msg}")
        return {
            "commit_id": None,
            "commit_message": None,
            "error": error_msg,
        }

    # Get git diff of uncommitted changes to show oracle
    diff_result = subprocess.run(
        ["git", "diff"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=10,
    )

    oracle_prompt = "Analyze the uncommitted files and generate a good commit message. Only output the commit message text, nothing else."

    try:
        # Use execute_oracle_prompt to get commit message from oracle
        prompt_request = PromptRequest(prompt=oracle_prompt)
        oracle_result = await prompts.execute_oracle_prompt(prompt_request)

        # Extract commit message from oracle output
        oracle_output = oracle_result.get("output", "").strip()

        # Clean up commit message - extract the actual message
        commit_message = None
        lines = oracle_output.split("\n")
        for line in lines:
            line = line.strip()
            # Skip empty lines, markdown headers, code blocks, quotes
            if (
                not line
                or line.startswith("#")
                or line.startswith("```")
                or line.startswith("`")
                or line.startswith('"')
                or line.startswith("'")
            ):
                continue
            # Look for lines that look like commit messages (reasonable length)
            if 10 <= len(line) <= 200:
                # Remove common prefixes
                cleaned = line
                for prefix in [
                    "Commit message:",
                    "Message:",
                    "Commit:",
                    "Suggested message:",
                ]:
                    if cleaned.lower().startswith(prefix.lower()):
                        cleaned = cleaned[len(prefix) :].strip()
                        break
                if cleaned and 10 <= len(cleaned) <= 200:
                    commit_message = cleaned
                    break

        # Fallback if no good message found
        if not commit_message:
            commit_message = f"Update code for task {current_task_id}"

        # Commit with the oracle-generated message
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if commit_result.returncode != 0:
            error_msg = f"Failed to commit changes: {commit_result.stderr or commit_result.stdout}"
            logger.error(f"ERROR: {error_msg}")
            return {
                "commit_id": None,
                "commit_message": commit_message,
                "error": error_msg,
            }

    except HTTPException as e:
        error_msg = f"Failed to get commit message from oracle: {e.detail}"
        logger.error(f"ERROR: {error_msg}")
        return {
            "commit_id": None,
            "commit_message": None,
            "error": error_msg,
        }
    except Exception as e:
        error_msg = f"Error getting commit message from oracle: {str(e)}"
        logger.error(f"ERROR: {error_msg}")
        return {
            "commit_id": None,
            "commit_message": None,
            "error": error_msg,
        }

    # Get commit SHA
    sha_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=10,
    )

    commit_sha = None
    if sha_result.returncode == 0:
        commit_sha = sha_result.stdout.strip()

    # Add action to chat history
    commit_chat_id = f"{repo_name}/{branch_name}/{current_task_id}/coder"
    save_action(
        commit_chat_id,
        f"Code committed: {commit_message} (SHA: {commit_sha[:8] if commit_sha else 'N/A'})",
    )

    # Configure git authentication
    configure_github_auth(repo_dir)

    # Push the commit
    push_error = push_branch(repo_dir, branch_name, repo_name, current_task_id)

    if push_error:
        return {
            "commit_id": commit_sha,
            "commit_message": commit_message,
            "error": f"Commit successful but push failed: {push_error}",
        }

    return {
        "commit_id": commit_sha,
        "commit_message": commit_message,
        "error": None,
    }


def get_task_commits(repo_dir: Path, task_id: str) -> list[str]:
    """
    Get all commit SHAs for a task by checking git log for commits mentioning the task ID.
    Searches for commits with "task {task_id}" in the commit message.

    Args:
        repo_dir: Path to repository directory
        task_id: Task ID to search for

    Returns:
        List of commit SHAs (chronological order, oldest first)
    """
    import subprocess

    commit_shas = []

    # Search git log for commits with task ID in the message
    # Use --grep to search commit messages, --format to get only SHA
    # Try multiple patterns to catch different commit message formats
    patterns = [
        f"task {task_id}",  # "Finish task 123"
        f"Task {task_id}",  # "Finish Task 123"
        f"#{task_id}",  # "Finish #123"
    ]

    seen_shas = set()

    for pattern in patterns:
        result = subprocess.run(
            ["git", "log", "--all", "--grep", pattern, "--format=%H", "--reverse"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0 and result.stdout.strip():
            for sha in result.stdout.strip().split("\n"):
                sha = sha.strip()
                if sha and sha not in seen_shas:
                    commit_shas.append(sha)
                    seen_shas.add(sha)

    # If no commits found with patterns, try without --all (just current branch)
    if not commit_shas:
        for pattern in patterns:
            result = subprocess.run(
                ["git", "log", "--grep", pattern, "--format=%H", "--reverse"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0 and result.stdout.strip():
                for sha in result.stdout.strip().split("\n"):
                    sha = sha.strip()
                    if sha and sha not in seen_shas:
                        commit_shas.append(sha)
                        seen_shas.add(sha)

    return commit_shas


async def commit_and_push(request: FinishTaskRequest):
    """
    Commit uncommitted changes using Cursor to generate a meaningful commit message,
    then push to remote. Returns commit ID and commit message.

    Request body:
        git_user_name: Git user.name to use for commits (required)
        git_user_email: Git user.email to use for commits (required)

    Returns:
        Dictionary with commit_id, commit_message, and error (if any)
    """
    current_task_id = get_current_task_id()
    if not current_task_id:
        raise HTTPException(status_code=400, detail="No active task")

    repo_name, branch_name = validate_environment_variables()

    repo_dir = Path("/workspace/repo")
    if not repo_dir.exists():
        raise HTTPException(status_code=500, detail="Repository directory not found")

    result = await commit_and_push_with_cursor(
        repo_dir=repo_dir,
        repo_name=repo_name,
        branch_name=branch_name,
        current_task_id=current_task_id,
        git_user_name=request.git_user_name,
        git_user_email=request.git_user_email,
    )

    if result["error"]:
        raise HTTPException(
            status_code=500,
            detail=result["error"],
        )

    return result


async def finish_task(request: FinishTaskRequest):
    """
    Finish the current task by unsetting the task ID.
    Commits and pushes any remaining uncommitted changes, then clears the task ID.

    Request body:
        git_user_name: Git user.name to use for commits (required)
        git_user_email: Git user.email to use for commits (required)

    Returns:
        Success message with commit and push details
    """
    # Get current task ID
    current_task_id = get_current_task_id()
    if not current_task_id:
        raise HTTPException(status_code=400, detail="No active task to finish")

    repo_name, branch_name = validate_environment_variables()

    try:
        # Change to repo directory
        repo_dir = Path("/workspace/repo")
        if not repo_dir.exists():
            raise HTTPException(
                status_code=500, detail="Repository directory not found"
            )

        # Commit and push any remaining uncommitted changes using the same logic
        commit_result = await commit_and_push_with_cursor(
            repo_dir=repo_dir,
            repo_name=repo_name,
            branch_name=branch_name,
            current_task_id=current_task_id,
            git_user_name=request.git_user_name,
            git_user_email=request.git_user_email,
        )

        if commit_result["error"]:
            # Clear TASK_ID so it doesn't block new tasks
            task_file = Path("/app/task_id.txt")
            if task_file.exists():
                task_file.unlink()
            raise HTTPException(status_code=500, detail=commit_result["error"])

        # Unset task ID after successful commit and push
        task_file = Path("/app/task_id.txt")
        if task_file.exists():
            task_file.unlink()

        return {
            "status": "finished",
            "task_id": current_task_id,
            "commit_id": commit_result["commit_id"],
            "commit_message": commit_result["commit_message"],
            "message": f"Task {current_task_id} finished. Changes committed and pushed to {branch_name}.",
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Git operation timed out")
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Git operation failed: {e.stderr if hasattr(e, 'stderr') else str(e)}",
        )
    except Exception as e:
        error_msg = str(e) if str(e) else repr(e)
        error_type = type(e).__name__
        logger.error(f"Error finishing task: {error_type}: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error finishing task: {error_type}: {error_msg}"
        )
