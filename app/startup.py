"""
Startup event handler for loading startup actions and initializing chat history.
"""

import json
import os
from pathlib import Path

from .config import STARTUP_ACTIONS_FILE
from .utils import build_resume_value, validate_environment_variables
from .chat_history import (
    save_action,
    initialize_chat_history_from_env,
    get_chat_history_path,
)


async def load_startup_actions():
    """
    Load startup actions from entrypoint.sh and save them to chat history.
    Also initialize chat history from environment variables if provided.
    This runs when the FastAPI app starts.
    """
    # Initialize chat history from environment variables (if provided)
    try:
        # Initialize oracle chat history (merged from all Epics on the branch)
        try:
            oracle_chat_id = build_resume_value("oracle")
            initialize_chat_history_from_env(
                oracle_chat_id, "INITIAL_CHAT_HISTORY_ORACLE"
            )
        except Exception as e:
            print(f"Warning: Could not initialize oracle chat history: {e}")

        # Initialize task coder chat histories (one per task)
        task_histories_json = os.environ.get("INITIAL_CHAT_HISTORIES_CODER")
        if task_histories_json:
            try:
                task_histories = json.loads(task_histories_json)
                if isinstance(task_histories, dict):
                    repo_name, branch_name = validate_environment_variables()
                    for task_id, chat_history in task_histories.items():
                        if isinstance(chat_history, list):
                            chat_id = f"{repo_name}/{branch_name}/{task_id}/coder"
                            # Convert Epic/Task format to agent environment format
                            converted_history = []
                            for msg in chat_history:
                                if not isinstance(msg, dict):
                                    continue
                                converted_msg = {
                                    "timestamp": msg.get("timestamp", ""),
                                }
                                if (
                                    msg.get("category") == "conversation"
                                    and "sender" in msg
                                ):
                                    converted_msg["sender"] = msg["sender"]
                                    converted_msg["text"] = msg.get("text", "")
                                elif msg.get("category") in ["action", "error"]:
                                    converted_msg["category"] = msg["category"]
                                    converted_msg["text"] = msg.get("text", "")
                                elif "sender" in msg:
                                    converted_msg["sender"] = msg["sender"]
                                    converted_msg["text"] = msg.get("text", "")
                                elif "category" in msg:
                                    converted_msg["category"] = msg["category"]
                                    converted_msg["text"] = msg.get("text", "")
                                else:
                                    continue
                                converted_history.append(converted_msg)

                            # Initialize if file doesn't exist
                            history_path = get_chat_history_path(chat_id)
                            if converted_history and not history_path.exists():
                                try:
                                    with open(history_path, "w", encoding="utf-8") as f:
                                        json.dump(
                                            converted_history,
                                            f,
                                            indent=2,
                                            ensure_ascii=False,
                                        )
                                    print(
                                        f"Initialized chat history for task {task_id} (chat_id: {chat_id})"
                                    )
                                except Exception as e:
                                    print(
                                        f"Warning: Could not initialize chat history for task {task_id}: {e}"
                                    )
            except Exception as e:
                print(f"Warning: Could not parse INITIAL_CHAT_HISTORIES_CODER: {e}")
    except Exception as e:
        print(f"Warning: Error during chat history initialization: {e}")

    # Load startup actions from file
    if not STARTUP_ACTIONS_FILE.exists():
        return

    try:
        with open(STARTUP_ACTIONS_FILE, "r", encoding="utf-8") as f:
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
            if action.get("category") == "action" and action.get("text"):
                try:
                    save_action(resume_value, action["text"])
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
