"""
Agent Environment API - FastAPI application.
"""

import logging
from fastapi import FastAPI

from . import prompts, git, tasks, startup

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Agent Environment API")


# Register startup event
@app.on_event("startup")
async def startup_event():
    await startup.load_startup_actions()


# Register routes
app.post("/prompt/oracle")(prompts.execute_oracle_prompt)
app.post("/prompt/coder")(prompts.execute_coder_prompt)

app.get("/status")(git.get_git_status)
app.get("/updates")(git.get_git_diff)

app.get("/health")(lambda: {"status": "healthy"})

app.get("/current_task")(tasks.get_current_task)
app.get("/chat_history")(tasks.get_chat_history)
app.post("/start_task")(tasks.start_task)
app.post("/clear_task")(tasks.clear_task)
app.post("/commit_and_push")(tasks.commit_and_push)
app.post("/finish_task")(tasks.finish_task)
