"""
Git-related endpoints.
"""

import os
import subprocess
from fastapi import HTTPException


async def get_git_status():
    """
    Get git status of the repository.

    Returns:
        Git status output as string
    """
    try:
        result = subprocess.run(
            ["git", "status"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd(),
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500, detail=f"Git status failed: {result.stderr}"
            )

        return {"output": result.stdout, "exit_code": result.returncode}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Git status command timed out")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error executing git status: {str(e)}"
        )


async def get_git_diff():
    """
    Get git diff of the repository.

    Returns:
        Git diff output as string
    """
    try:
        result = subprocess.run(
            ["git", "diff"], capture_output=True, text=True, timeout=30, cwd=os.getcwd()
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500, detail=f"Git diff failed: {result.stderr}"
            )

        return {"output": result.stdout, "exit_code": result.returncode}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Git diff command timed out")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error executing git diff: {str(e)}"
        )
