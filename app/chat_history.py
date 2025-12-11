"""
Chat history management functions.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

from .config import CHAT_HISTORY_DIR


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
        with open(history_path, "r", encoding="utf-8") as f:
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
        "text": text,
    }

    history.append(message)

    # Save back to file
    history_path = get_chat_history_path(chat_id)
    try:
        with open(history_path, "w", encoding="utf-8") as f:
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
        "text": text,
    }

    history.append(message)

    # Save back to file
    history_path = get_chat_history_path(chat_id)
    try:
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Warning: Could not save action to {history_path}: {e}")


def initialize_chat_history_from_env(chat_id: str, env_var_name: str) -> None:
    """
    Initialize chat history file from environment variable.
    Converts Epic/Task chat_history format to agent environment format.

    Args:
        chat_id: The chat ID (resume value)
        env_var_name: Name of environment variable containing chat history JSON
    """
    import os

    env_value = os.environ.get(env_var_name)
    if not env_value:
        return

    try:
        # Parse JSON from environment variable
        epic_chat_history = json.loads(env_value)
        if not isinstance(epic_chat_history, list):
            print(f"Warning: {env_var_name} is not a list, skipping initialization")
            return

        # Convert Epic format to agent environment format
        converted_history = []
        for msg in epic_chat_history:
            if not isinstance(msg, dict):
                continue

            # Convert message format
            converted_msg = {
                "timestamp": msg.get(
                    "timestamp", datetime.now(timezone.utc).isoformat()
                ),
            }

            # Handle conversation messages (with sender)
            if msg.get("category") == "conversation" and "sender" in msg:
                converted_msg["sender"] = msg["sender"]
                converted_msg["text"] = msg.get("text", "")
            # Handle action/error messages (with category)
            elif msg.get("category") in ["action", "error"]:
                converted_msg["category"] = msg["category"]
                converted_msg["text"] = msg.get("text", "")
            # Fallback: if it already has sender, use as-is
            elif "sender" in msg:
                converted_msg["sender"] = msg["sender"]
                converted_msg["text"] = msg.get("text", "")
            # Fallback: if it already has category, use as-is
            elif "category" in msg:
                converted_msg["category"] = msg["category"]
                converted_msg["text"] = msg.get("text", "")
            else:
                # Skip malformed messages
                continue

            converted_history.append(converted_msg)

        # Only write if we have messages and file doesn't exist yet
        # (don't overwrite existing chat history)
        history_path = get_chat_history_path(chat_id)
        if converted_history and not history_path.exists():
            try:
                with open(history_path, "w", encoding="utf-8") as f:
                    json.dump(converted_history, f, indent=2, ensure_ascii=False)
                print(f"Initialized chat history for {chat_id} from {env_var_name}")
            except IOError as e:
                print(
                    f"Warning: Could not initialize chat history from {env_var_name}: {e}"
                )

    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse {env_var_name} as JSON: {e}")
    except Exception as e:
        print(f"Warning: Error initializing chat history from {env_var_name}: {e}")
