"""
Git configuration helpers.
"""

import os
import subprocess
from pathlib import Path
from fastapi import HTTPException


def configure_git_user(repo_dir: Path, git_user_name: str, git_user_email: str) -> None:
    """
    Configure git user.name and user.email.

    Args:
        repo_dir: Path to repository directory
        git_user_name: Git user name
        git_user_email: Git user email

    Raises:
        HTTPException if configuration fails
    """
    git_config_name_result = subprocess.run(
        ["git", "config", "user.name", git_user_name],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if git_config_name_result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure git user.name: {git_config_name_result.stderr}",
        )

    git_config_email_result = subprocess.run(
        ["git", "config", "user.email", git_user_email],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if git_config_email_result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure git user.email: {git_config_email_result.stderr}",
        )


def configure_github_auth(repo_dir: Path) -> None:
    """
    Configure git remote URL with GitHub token if available.

    Args:
        repo_dir: Path to repository directory
    """
    github_token = os.environ.get("GITHUB_ACCESS_TOKEN")
    if not github_token:
        return

    # Get the current remote URL
    remote_url_result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=5,
    )

    if remote_url_result.returncode == 0:
        remote_url = remote_url_result.stdout.strip()
        # If URL doesn't already contain token, add it
        if github_token not in remote_url:
            # Parse URL and add token
            if remote_url.startswith("https://"):
                # Format: https://github.com/user/repo.git -> https://token@github.com/user/repo.git
                url_parts = remote_url.split("://", 1)
                if len(url_parts) == 2:
                    domain_and_path = url_parts[1]
                    authenticated_url = f"https://{github_token}@{domain_and_path}"
                    # Update remote URL
                    subprocess.run(
                        [
                            "git",
                            "remote",
                            "set-url",
                            "origin",
                            authenticated_url,
                        ],
                        cwd=repo_dir,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
