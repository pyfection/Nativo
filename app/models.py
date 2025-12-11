"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel


class PromptRequest(BaseModel):
    prompt: str


class StartTaskRequest(BaseModel):
    task_id: str


class FinishTaskRequest(BaseModel):
    git_user_name: str
    git_user_email: str
