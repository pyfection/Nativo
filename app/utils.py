"""
Utility functions for environment variables and task management.
"""

import os
from pathlib import Path
from typing import Optional
from fastapi import HTTPException


def validate_environment_variables() -> tuple[str, str]:
    """
    Validate that required environment variables are set.

    Returns:
        Tuple of (repo_name, branch_name)

    Raises:
        HTTPException if REPO_NAME or BRANCH_NAME are not set
    """
    repo_name = os.environ.get("REPO_NAME")
    branch_name = os.environ.get("BRANCH_NAME")

    if not repo_name:
        raise HTTPException(
            status_code=500, detail="REPO_NAME environment variable is not set"
        )

    if not branch_name:
        raise HTTPException(
            status_code=500, detail="BRANCH_NAME environment variable is not set"
        )

    return repo_name, branch_name


def get_current_task_id() -> Optional[str]:
    """
    Get current task ID from file (if set).

    Returns:
        Task ID string or None if no task is active
    """
    task_file = Path("/app/task_id.txt")
    if task_file.exists():
        try:
            return task_file.read_text(encoding="utf-8").strip()
        except IOError:
            return None
    return None


def build_resume_value(chat_type: str) -> str:
    """
    Build resume value (chat ID) based on environment variables and chat type.

    Args:
        chat_type: Either 'oracle' or 'coder'

    Returns:
        Resume value string:
        - Oracle: {repo_name}/{branch_name}/oracle (no task_id)
        - Coder: {repo_name}/{branch_name}[/{task_id}]/coder
    """
    repo_name, branch_name = validate_environment_variables()

    # Oracle never includes task_id
    if chat_type == "oracle":
        return f"{repo_name}/{branch_name}/oracle"

    # Coder includes task_id if available
    task_id = get_current_task_id()
    if task_id:
        return f"{repo_name}/{branch_name}/{task_id}/coder"
    else:
        return f"{repo_name}/{branch_name}/coder"
