"""
Git push helpers.
"""

import subprocess
import time
import logging
from pathlib import Path

from .chat_history import save_action

logger = logging.getLogger(__name__)


def _get_transient_error_checker():
    """Import transient error checker from parent utils module."""
    import sys
    from pathlib import Path as PathLib

    parent_dir = PathLib(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    from utils import is_transient_error

    return is_transient_error


def check_branch_exists_remote(repo_dir: Path, branch_name: str) -> bool:
    """
    Check if branch exists on remote.

    Args:
        repo_dir: Path to repository directory
        branch_name: Branch name

    Returns:
        True if branch exists on remote, False otherwise
    """
    remote_check = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", branch_name],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=10,
    )

    return bool(remote_check.stdout.strip())


def check_commit_pushed(repo_dir: Path, branch_name: str, commit_sha: str) -> bool:
    """
    Check if commit is already pushed to remote.

    Args:
        repo_dir: Path to repository directory
        branch_name: Branch name
        commit_sha: Commit SHA

    Returns:
        True if commit is already pushed, False otherwise
    """
    remote_commit_check = subprocess.run(
        ["git", "ls-remote", "origin", branch_name],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=10,
    )

    if remote_commit_check.returncode == 0:
        remote_sha = (
            remote_commit_check.stdout.split()[0]
            if remote_commit_check.stdout.strip()
            else None
        )
        return remote_sha == commit_sha

    return False


def push_branch(
    repo_dir: Path,
    branch_name: str,
    repo_name: str,
    current_task_id: str,
) -> str | None:
    """
    Push branch to remote with retry logic.

    Args:
        repo_dir: Path to repository directory
        branch_name: Branch name
        repo_name: Repository name
        current_task_id: Current task ID

    Returns:
        Error message if push failed, None if successful
    """
    check_transient_error = _get_transient_error_checker()

    # Try pushing with retry logic for transient errors
    max_push_retries = 3
    retry_delay = 2  # seconds
    push_success = False
    push_attempt_error = None
    push_permanent_error = None

    for push_attempt in range(max_push_retries):
        push_result = subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if push_result.returncode == 0:
            push_success = True
            # Add action to chat history for push
            push_chat_id = f"{repo_name}/{branch_name}/{current_task_id}/coder"
            save_action(push_chat_id, f"Code pushed to remote branch '{branch_name}'")
            return None
        else:
            push_attempt_error = push_result.stderr

            # If not transient error, don't retry
            if not check_transient_error(push_attempt_error, error_type="push"):
                # Permanent error - log and move to review
                push_permanent_error = (
                    f"Failed to push branch (permanent error): {push_attempt_error}"
                )
                logger.error(f"ERROR: {push_permanent_error}")
                break

            # Transient error - retry with exponential backoff
            if push_attempt < max_push_retries - 1:
                wait_time = retry_delay * (2**push_attempt)
                logger.warning(
                    f"WARNING: Failed to push (attempt {push_attempt + 1}/{max_push_retries}, transient): {push_attempt_error}. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)

    if not push_success:
        # Push failed after retries or permanent error
        if push_permanent_error:
            return push_permanent_error
        else:
            # All retries failed for transient error - treat as permanent
            return f"Failed to push branch after {max_push_retries} attempts: {push_attempt_error}"

    return None
