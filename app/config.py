"""
Configuration constants for the agent environment API.
"""

from pathlib import Path

# Directory to store chat history files
# Store in workspace directory (outside repo) for persistence
CHAT_HISTORY_DIR = Path("/workspace/chat_history")
CHAT_HISTORY_DIR.mkdir(exist_ok=True)

# File where entrypoint.sh writes startup actions
STARTUP_ACTIONS_FILE = Path("/app/startup_actions.json")
