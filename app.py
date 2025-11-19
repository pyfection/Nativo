from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import subprocess
import os
import json
import re
import logging
from datetime import datetime, timezone
from pathlib import Path

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Agent Environment API")

# Directory to store chat history files
# Store in workspace directory (outside repo) for persistence
CHAT_HISTORY_DIR = Path("/workspace/chat_history")
CHAT_HISTORY_DIR.mkdir(exist_ok=True)

# File where entrypoint.sh writes startup actions
STARTUP_ACTIONS_FILE = Path("/app/startup_actions.json")


@app.on_event("startup")
async def load_startup_actions():
    """
    Load startup actions from entrypoint.sh and save them to chat history.
    This runs when the FastAPI app starts.
    """
    if not STARTUP_ACTIONS_FILE.exists():
        return
    
    try:
        with open(STARTUP_ACTIONS_FILE, 'r', encoding='utf-8') as f:
            startup_actions = json.load(f)
        
        if not startup_actions:
            return
        
        # Get chat_id for coder (current task)
        # Note: This might not have task_id yet if called before /start_task
        # But we'll save to the base coder chat, which will be synced
        try:
            resume_value = build_resume_value("coder")
        except:
            # If we can't build resume value, skip saving actions
            return
        
        # Save each action to chat history
        for action in startup_actions:
            if action.get('category') == 'action' and action.get('text'):
                try:
                    save_action(resume_value, action['text'])
                except Exception as e:
                    print(f"Warning: Could not save startup action: {e}")
        
        # Clear the file after processing
        try:
            STARTUP_ACTIONS_FILE.unlink()
        except:
            pass
        
    except Exception as e:
        # Don't fail startup if we can't load actions
        print(f"Warning: Could not load startup actions: {e}")


class PromptRequest(BaseModel):
    prompt: str


def get_chat_history_path(chat_id: str) -> Path:
    """
    Get the file path for storing chat history.
    
    Args:
        chat_id: The chat ID (resume value)
    
    Returns:
        Path to the chat history JSON file
    """
    # Sanitize chat_id for use as filename (replace / with _)
    safe_chat_id = chat_id.replace("/", "_").replace("\\", "_")
    return CHAT_HISTORY_DIR / f"{safe_chat_id}.json"


def load_chat_history(chat_id: str) -> List[Dict[str, str]]:
    """
    Load chat history from JSON file.
    
    Args:
        chat_id: The chat ID (resume value)
    
    Returns:
        List of chat messages, each with 'timestamp', 'sender', and 'text'
    """
    history_path = get_chat_history_path(chat_id)
    
    if not history_path.exists():
        return []
    
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # If file is corrupted or can't be read, return empty history
        print(f"Warning: Could not load chat history from {history_path}: {e}")
        return []


def save_chat_message(chat_id: str, sender: str, text: str) -> None:
    """
    Save a chat message to the history file.
    
    Args:
        chat_id: The chat ID (resume value)
        sender: Who sent the message ('user', 'oracle', or 'coder')
        text: The message text
    """
    history = load_chat_history(chat_id)
    
    # Add new message with UTC timestamp
    message = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sender": sender,
        "text": text
    }
    
    history.append(message)
    
    # Save back to file
    history_path = get_chat_history_path(chat_id)
    try:
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Warning: Could not save chat history to {history_path}: {e}")


def save_action(chat_id: str, text: str) -> None:
    """
    Save an action message to the history file.
    
    Args:
        chat_id: The chat ID (resume value)
        text: The action text
    """
    history = load_chat_history(chat_id)
    
    # Add new action message with UTC timestamp
    message = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "category": "action",
        "text": text
    }
    
    history.append(message)
    
    # Save back to file
    history_path = get_chat_history_path(chat_id)
    try:
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Warning: Could not save action to {history_path}: {e}")


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
            status_code=500,
            detail="REPO_NAME environment variable is not set"
        )
    
    if not branch_name:
        raise HTTPException(
            status_code=500,
            detail="BRANCH_NAME environment variable is not set"
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
            return task_file.read_text(encoding='utf-8').strip()
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


@app.post("/prompt/oracle")
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
        import shutil
        cursor_agent_path = shutil.which("cursor-agent")
        if not cursor_agent_path:
            error_msg = "cursor-agent command not found in PATH. Please ensure Cursor CLI is installed."
            save_chat_message(resume_value, "oracle", error_msg)
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
        
        # Execute command
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=os.getcwd()
            )
        except FileNotFoundError as e:
            error_msg = f"Command not found: {cmd[0]}. PATH: {os.environ.get('PATH', 'not set')}. Error: {str(e)}"
            save_chat_message(resume_value, "oracle", error_msg)
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
        
        if result.returncode != 0:
            # Save error to chat history
            error_output = result.stderr.strip() or result.stdout.strip() or "No error output"
            error_text = f"Error (exit code {result.returncode}): {error_output}"
            save_chat_message(resume_value, "oracle", error_text)
            raise HTTPException(
                status_code=500,
                detail=f"Command failed (exit code {result.returncode}): {error_output}"
            )
        
        # Save oracle response to chat history
        save_chat_message(resume_value, "oracle", result.stdout)
        
        # Get UTC timestamp (same format as chat history)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        return {
            "output": result.stdout,
            "exit_code": result.returncode,
            "timestamp": timestamp
        }
    except subprocess.TimeoutExpired:
        resume_value = build_resume_value("oracle")
        error_text = "Command execution timed out"
        save_chat_message(resume_value, "oracle", error_text)
        raise HTTPException(
            status_code=504,
            detail="Command execution timed out"
        )
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
            detail=f"Error executing command ({error_type}): {error_msg}"
        )


@app.post("/prompt/coder")
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
        cmd = ["cursor-agent", "-p", f"--resume={resume_value}", "--force", request.prompt]
        
        # Check if cursor-agent is available
        import shutil
        cursor_agent_path = shutil.which("cursor-agent")
        if not cursor_agent_path:
            error_msg = "cursor-agent command not found in PATH. Please ensure Cursor CLI is installed."
            save_chat_message(resume_value, "coder", error_msg)
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
        
        # Execute command
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=os.getcwd()
            )
        except FileNotFoundError as e:
            error_msg = f"Command not found: {cmd[0]}. PATH: {os.environ.get('PATH', 'not set')}. Error: {str(e)}"
            save_chat_message(resume_value, "coder", error_msg)
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
        
        if result.returncode != 0:
            # Save error to chat history
            error_output = result.stderr.strip() or result.stdout.strip() or "No error output"
            error_text = f"Error (exit code {result.returncode}): {error_output}"
            save_chat_message(resume_value, "coder", error_text)
            raise HTTPException(
                status_code=500,
                detail=f"Command failed (exit code {result.returncode}): {error_output}"
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
                timeout=10
            )
            
            if git_status_result.returncode == 0 and git_status_result.stdout.strip():
                # Get detailed diff stats
                git_diff_result = subprocess.run(
                    ["git", "diff", "--stat"],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if git_diff_result.returncode == 0 and git_diff_result.stdout.strip():
                    # Parse diff stats to get file changes
                    # Format: "path/to/file.py | 5 +++++" or "path/to/file.py | 3 +--" or "path/to/file.py | 2 +5-3"
                    file_changes = []
                    for line in git_diff_result.stdout.strip().split('\n'):
                        if '|' in line and not line.startswith(' '):
                            parts = line.split('|')
                            if len(parts) == 2:
                                file_path = parts[0].strip()
                                stats = parts[1].strip()
                                
                                # Parse stats: format is usually "N +++++---" or "N +M-N" or just "N"
                                # Extract numbers and count + and - signs
                                additions = 0
                                deletions = 0
                                
                                # Try to match format like "5 +++++" or "3 +--" or "2 +5-3"
                                # First, try to extract explicit numbers like "+5-3"
                                explicit_match = re.search(r'\+(\d+)-(\d+)', stats)
                                if explicit_match:
                                    additions = int(explicit_match.group(1))
                                    deletions = int(explicit_match.group(2))
                                else:
                                    # Count + and - signs
                                    additions = stats.count('+')
                                    deletions = stats.count('-')
                                
                                if additions > 0 or deletions > 0:
                                    file_changes.append(f"{file_path} +{additions}-{deletions}")
                    
                    if file_changes:
                        # Add action with file changes
                        changes_text = "\n".join(file_changes)
                        save_action(resume_value, f"Files changed:\n{changes_text}")
        
        # Get UTC timestamp (same format as chat history)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        return {
            "output": result.stdout,
            "exit_code": result.returncode,
            "timestamp": timestamp
        }
    except subprocess.TimeoutExpired:
        resume_value = build_resume_value("coder")
        error_text = "Command execution timed out"
        save_chat_message(resume_value, "coder", error_text)
        raise HTTPException(
            status_code=504,
            detail="Command execution timed out"
        )
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
            detail=f"Error executing command ({error_type}): {error_msg}"
        )


@app.get("/status")
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
            cwd=os.getcwd()
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Git status failed: {result.stderr}"
            )
        
        return {
            "output": result.stdout,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Git status command timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing git status: {str(e)}"
        )


@app.get("/updates")
async def get_git_diff():
    """
    Get git diff of the repository.
    
    Returns:
        Git diff output as string
    """
    try:
        result = subprocess.run(
            ["git", "diff"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Git diff failed: {result.stderr}"
            )
        
        return {
            "output": result.stdout,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Git diff command timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing git diff: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/current_task")
async def get_current_task():
    """
    Get current task ID from environment.
    
    Returns:
        Current task ID if set, None otherwise
    """
    current_task_id = get_current_task_id()
    return {
        "task_id": current_task_id,
        "has_task": current_task_id is not None
    }


@app.get("/chat_history")
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
            status_code=400,
            detail="chat_type must be either 'oracle' or 'coder'"
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
        "message_count": len(history)
    }


class StartTaskRequest(BaseModel):
    task_id: str


@app.post("/start_task")
async def start_task(request: StartTaskRequest):
    """
    Start a new task by setting the task ID.
    Creates a new chat session for the coder with the task ID.
    Fails if a task is already ongoing.
    
    Args:
        request: StartTaskRequest with task_id
    
    Returns:
        Success message with chat ID
    """
    # Check if a task is already active
    current_task_id = get_current_task_id()
    if current_task_id:
        raise HTTPException(
            status_code=400,
            detail=f"A task is already active (task_id: {current_task_id}). Please finish the current task before starting a new one."
        )
    
    # Set task ID in file
    task_file = Path("/app/task_id.txt")
    try:
        task_file.write_text(request.task_id, encoding='utf-8')
    except IOError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set task ID: {str(e)}"
        )
    
    # Build chat ID for coder
    repo_name, branch_name = validate_environment_variables()
    
    chat_id = f"{repo_name}/{branch_name}/{request.task_id}/coder"
    
    return {
        "status": "started",
        "task_id": request.task_id,
        "chat_id": chat_id,
        "message": f"Task {request.task_id} started. New coder chat ID: {chat_id}"
    }


@app.post("/clear_task")
async def clear_task():
    """
    Clear the current task ID (rollback operation).
    Used when task start fails after TASK_ID was set.
    
    Returns:
        Success message
    """
    current_task_id = get_current_task_id()
    if not current_task_id:
        return {
            "status": "cleared",
            "message": "No active task to clear"
        }
    
    # Remove task ID file
    task_file = Path("/app/task_id.txt")
    if task_file.exists():
        try:
            task_file.unlink()
            return {
                "status": "cleared",
                "task_id": current_task_id,
                "message": f"Task {current_task_id} cleared"
            }
        except IOError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to clear task ID: {str(e)}"
            )
    
    return {
        "status": "cleared",
        "message": "Task ID file not found"
    }


class FinishTaskRequest(BaseModel):
    git_user_name: str
    git_user_email: str


@app.post("/finish_task")
async def finish_task(request: FinishTaskRequest):
    """
    Finish the current task by unsetting the task ID.
    Commits and pushes changes, optionally creating branch on remote if it doesn't exist.
    
    Request body:
        git_user_name: Git user.name to use for commits (required)
        git_user_email: Git user.email to use for commits (required)
    
    Returns:
        Success message with commit and push details
    """
    # Get current task ID
    current_task_id = get_current_task_id()
    if not current_task_id:
        raise HTTPException(
            status_code=400,
            detail="No active task to finish"
        )
    
    repo_name, branch_name = validate_environment_variables()
    
    try:
        # Change to repo directory
        repo_dir = Path("/workspace/repo")
        if not repo_dir.exists():
            raise HTTPException(
                status_code=500,
                detail="Repository directory not found"
            )
        
        # Configure git user with provided values
        git_config_name_result = subprocess.run(
            ["git", "config", "user.name", request.git_user_name],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        if git_config_name_result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to configure git user.name: {git_config_name_result.stderr}"
            )
        
        git_config_email_result = subprocess.run(
            ["git", "config", "user.email", request.git_user_email],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        if git_config_email_result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to configure git user.email: {git_config_email_result.stderr}"
            )
        
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        has_changes = bool(result.stdout.strip())
        
        commit_sha = None
        commit_message = f"Finish task {current_task_id}"
        permanent_error = None
        
        if has_changes:
            # Check if commit already exists (idempotent check)
            head_commit_msg = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=10
            ).stdout.strip()
            
            already_committed = commit_message in head_commit_msg
            
            if already_committed:
                # Already committed - get SHA and continue
                sha_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if sha_result.returncode == 0:
                    commit_sha = sha_result.stdout.strip()
                    # Add action for already committed (idempotent case)
                    commit_chat_id = f"{repo_name}/{branch_name}/{current_task_id}/coder"
                    save_action(commit_chat_id, f"Code already committed: {commit_message} (SHA: {commit_sha[:8]})")
            else:
                # Need to commit - stage changes first
                add_result = subprocess.run(
                    ["git", "add", "-A"],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if add_result.returncode != 0:
                    # Permanent error staging - log and move to review
                    permanent_error = f"Failed to stage changes: {add_result.stderr}"
                    logger.error(f"ERROR: {permanent_error}")
                    # Clear TASK_ID so it doesn't block new tasks
                    task_file = Path("/app/task_id.txt")
                    if task_file.exists():
                        task_file.unlink()
                    raise HTTPException(
                        status_code=500,
                        detail=permanent_error
                    )
                
                # Determine if error is transient (retryable) or permanent
                from utils import is_transient_error as check_transient_error
                
                # Try committing with retry logic for transient errors
                max_commit_retries = 3
                retry_delay = 2  # seconds
                commit_success = False
                commit_error = None
                
                for commit_attempt in range(max_commit_retries):
                    commit_result = subprocess.run(
                        ["git", "commit", "-m", commit_message],
                        cwd=repo_dir,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if commit_result.returncode == 0:
                        commit_success = True
                        # Get commit SHA
                        sha_result = subprocess.run(
                            ["git", "rev-parse", "HEAD"],
                            cwd=repo_dir,
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if sha_result.returncode == 0:
                            commit_sha = sha_result.stdout.strip()
                        
                        # Add action to chat history for commit
                        commit_chat_id = f"{repo_name}/{branch_name}/{current_task_id}/coder"
                        save_action(commit_chat_id, f"Code committed: {commit_message} (SHA: {commit_sha[:8] if commit_sha else 'N/A'})")
                        
                        break
                    elif "nothing to commit" in commit_result.stderr.lower():
                        # Nothing to commit - that's OK
                        commit_success = True
                        break
                    else:
                        # Combine stderr and stdout for better error messages
                        commit_error = commit_result.stderr.strip() or commit_result.stdout.strip() or "Unknown git commit error"
                        
                        # If not transient error, don't retry
                        if not check_transient_error(commit_error, error_type='git'):
                            # Permanent error - log and move to review
                            permanent_error = f"Failed to commit changes (permanent error): {commit_error}"
                            logger.error(f"ERROR: {permanent_error}")
                            break
                        
                        # Transient error - retry with exponential backoff
                        if commit_attempt < max_commit_retries - 1:
                            wait_time = retry_delay * (2 ** commit_attempt)
                            logger.warning(f"WARNING: Failed to commit (attempt {commit_attempt + 1}/{max_commit_retries}, transient): {commit_error}. Retrying in {wait_time}s...")
                            import time
                            time.sleep(wait_time)
                
                if not commit_success:
                    # Commit failed after retries or permanent error
                    if permanent_error:
                        # Permanent error - clear TASK_ID and raise error (caller should move task to review)
                        task_file = Path("/app/task_id.txt")
                        if task_file.exists():
                            task_file.unlink()
                        raise HTTPException(
                            status_code=500,
                            detail=permanent_error
                        )
                    else:
                        # All retries failed for transient error - treat as permanent
                        permanent_error = f"Failed to commit changes after {max_commit_retries} attempts: {commit_error}"
                        logger.error(f"ERROR: {permanent_error}")
                        task_file = Path("/app/task_id.txt")
                        if task_file.exists():
                            task_file.unlink()
                        raise HTTPException(
                            status_code=500,
                            detail=permanent_error
                        )
        
        # Unset task ID after successful commit (before push)
        # This way, if push fails, TASK_ID is already cleared and doesn't block new tasks
        task_file = Path("/app/task_id.txt")
        if task_file.exists():
            task_file.unlink()
        
        # Configure git authentication using GITHUB_ACCESS_TOKEN if available
        github_token = os.environ.get("GITHUB_ACCESS_TOKEN")
        if github_token:
            # Get the current remote URL
            remote_url_result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=5
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
                                ["git", "remote", "set-url", "origin", authenticated_url],
                                cwd=repo_dir,
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
        
        # Check if branch exists on remote
        remote_check = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", branch_name],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        branch_exists_remote = bool(remote_check.stdout.strip())
        
        # Check if local commits are already pushed (idempotent push check)
        push_skipped = False
        if commit_sha:
            # Check if commit exists on remote
            remote_commit_check = subprocess.run(
                ["git", "ls-remote", "origin", branch_name],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if remote_commit_check.returncode == 0:
                remote_sha = remote_commit_check.stdout.split()[0] if remote_commit_check.stdout.strip() else None
                if remote_sha == commit_sha:
                    # Already pushed - skip push
                    push_skipped = True
                    logger.info(f"INFO: Commit {commit_sha} already pushed to remote, skipping push.")
                    # Add action for already pushed (idempotent case)
                    push_chat_id = f"{repo_name}/{branch_name}/{current_task_id}/coder"
                    save_action(push_chat_id, f"Code already pushed to remote branch '{branch_name}'")
        
        # Push branch (creates it on remote if it doesn't exist)
        push_error = None
        push_permanent_error = None
        
        if not push_skipped:
            # Determine if error is transient (retryable) or permanent
            from utils import is_transient_error as check_transient_error
            
            # Try pushing with retry logic for transient errors
            max_push_retries = 3
            retry_delay = 2  # seconds
            push_success = False
            push_attempt_error = None
            
            for push_attempt in range(max_push_retries):
                push_result = subprocess.run(
                    ["git", "push", "-u", "origin", branch_name],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if push_result.returncode == 0:
                    push_success = True
                    # Add action to chat history for push
                    push_chat_id = f"{repo_name}/{branch_name}/{current_task_id}/coder"
                    save_action(push_chat_id, f"Code pushed to remote branch '{branch_name}'")
                    break
                else:
                    push_attempt_error = push_result.stderr
                    
                    # If not transient error, don't retry
                    if not check_transient_error(push_attempt_error, error_type='push'):
                        # Permanent error - log and move to review
                        push_permanent_error = f"Failed to push branch (permanent error): {push_attempt_error}"
                        logger.error(f"ERROR: {push_permanent_error}")
                        break
                    
                    # Transient error - retry with exponential backoff
                    if push_attempt < max_push_retries - 1:
                        wait_time = retry_delay * (2 ** push_attempt)
                        logger.warning(f"WARNING: Failed to push (attempt {push_attempt + 1}/{max_push_retries}, transient): {push_attempt_error}. Retrying in {wait_time}s...")
                        import time
                        time.sleep(wait_time)
            
            if not push_success:
                # Push failed after retries or permanent error
                if push_permanent_error:
                    # Permanent error - log and return warning (task moves to review via recovery)
                    push_error = push_permanent_error
                    logger.error(f"ERROR: {push_error}. Task ID cleared, push can be retried manually or task will be moved to review.")
                else:
                    # All retries failed for transient error - treat as permanent
                    push_error = f"Failed to push branch after {max_push_retries} attempts: {push_attempt_error}"
                    logger.error(f"ERROR: {push_error}. Task ID cleared, push can be retried manually or task will be moved to review.")
        
        # Don't stop container automatically - let the backend manage container lifecycle
        # This allows for retries and better error handling
        
        # If push failed, raise HTTPException to prevent task from being marked as done
        if push_error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to push changes: {push_error}. Task will remain in review status."
            )
        
        return {
            "status": "finished",
            "task_id": current_task_id,
            "commit_sha": commit_sha,
            "branch_created": not branch_exists_remote,
            "push_error": None,
            "message": f"Task {current_task_id} finished. Changes committed and pushed to {branch_name}."
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Git operation timed out"
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Git operation failed: {e.stderr if hasattr(e, 'stderr') else str(e)}"
        )
    except Exception as e:
        error_msg = str(e) if str(e) else repr(e)
        error_type = type(e).__name__
        logger.error(f"Error finishing task: {error_type}: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error finishing task: {error_type}: {error_msg}"
        )

