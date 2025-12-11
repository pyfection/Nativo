"""
Git commit helpers.
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


def commit_changes(
    repo_dir: Path,
    commit_message: str,
    repo_name: str,
    branch_name: str,
    current_task_id: str,
) -> tuple[str | None, str | None]:
    """
    Commit changes to git repository with retry logic.

    Args:
        repo_dir: Path to repository directory
        commit_message: Commit message
        repo_name: Repository name
        branch_name: Branch name
        current_task_id: Current task ID

    Returns:
        Tuple of (commit_sha, error_message)
    """
    # Check if there are changes to commit
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=10,
    )

    has_changes = bool(result.stdout.strip())

    if not has_changes:
        return None, None

    # Check if commit already exists (idempotent check)
    head_commit_msg = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()

    already_committed = commit_message in head_commit_msg

    if already_committed:
        # Already committed - get SHA and continue
        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if sha_result.returncode == 0:
            commit_sha = sha_result.stdout.strip()
            # Add action for already committed (idempotent case)
            commit_chat_id = f"{repo_name}/{branch_name}/{current_task_id}/coder"
            save_action(
                commit_chat_id,
                f"Code already committed: {commit_message} (SHA: {commit_sha[:8]})",
            )
            return commit_sha, None
        return None, None

    # Need to commit - stage changes first
    add_result = subprocess.run(
        ["git", "add", "-A"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=10,
    )

    if add_result.returncode != 0:
        # Permanent error staging
        permanent_error = f"Failed to stage changes: {add_result.stderr}"
        logger.error(f"ERROR: {permanent_error}")
        return None, permanent_error

    check_transient_error = _get_transient_error_checker()

    # Try committing with retry logic for transient errors
    max_commit_retries = 3
    retry_delay = 2  # seconds
    commit_success = False
    commit_error = None
    permanent_error = None

    for commit_attempt in range(max_commit_retries):
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if commit_result.returncode == 0:
            commit_success = True
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

            # Add action to chat history for commit
            commit_chat_id = f"{repo_name}/{branch_name}/{current_task_id}/coder"
            save_action(
                commit_chat_id,
                f"Code committed: {commit_message} (SHA: {commit_sha[:8] if commit_sha else 'N/A'})",
            )

            return commit_sha, None
        elif "nothing to commit" in commit_result.stderr.lower():
            # Nothing to commit - that's OK
            commit_success = True
            return None, None
        else:
            # Combine stderr and stdout for better error messages
            commit_error = (
                commit_result.stderr.strip()
                or commit_result.stdout.strip()
                or "Unknown git commit error"
            )

            # If not transient error, don't retry
            if not check_transient_error(commit_error, error_type="git"):
                # Permanent error - log and move to review
                permanent_error = (
                    f"Failed to commit changes (permanent error): {commit_error}"
                )
                logger.error(f"ERROR: {permanent_error}")
                break

            # Transient error - retry with exponential backoff
            if commit_attempt < max_commit_retries - 1:
                wait_time = retry_delay * (2**commit_attempt)
                logger.warning(
                    f"WARNING: Failed to commit (attempt {commit_attempt + 1}/{max_commit_retries}, transient): {commit_error}. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)

    if not commit_success:
        # Commit failed after retries or permanent error
        if permanent_error:
            return None, permanent_error
        else:
            # All retries failed for transient error - treat as permanent
            return (
                None,
                f"Failed to commit changes after {max_commit_retries} attempts: {commit_error}",
            )
