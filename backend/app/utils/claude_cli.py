"""
Ask Claude for structured JSON through the local `claude` CLI.

Authenticates with a Claude subscription OAuth token (`CLAUDE_CODE_OAUTH_TOKEN`,
made with `claude setup-token`), never an API key: the child process gets a
minimal environment, so an `ANTHROPIC_API_KEY` on the server can't take over.
It runs with no tools, no settings files and no MCP servers, in an empty
directory, so the prompt is all it sees and all it can do is answer.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from app.config import settings

# Environment the CLI needs to run and reach the API (proxies, CA bundles).
_PASSTHROUGH = (
    "PATH",
    "HOME",
    "LANG",
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "NO_PROXY",
    "https_proxy",
    "http_proxy",
    "no_proxy",
    "SSL_CERT_FILE",
    "NODE_EXTRA_CA_CERTS",
)

# Each call is a separate CLI process; don't let a burst of cards start dozens.
_slots = threading.BoundedSemaphore(2)


class ClaudeUnavailableError(Exception):
    """Not configured, not installed, busy, or the call failed."""


def ask_json(prompt: str, *, system: str, schema: dict) -> dict:
    """Run one prompt and return the JSON object matching `schema`."""
    if not settings.CLAUDE_CODE_OAUTH_TOKEN:
        raise ClaudeUnavailableError("AI suggestions are not configured")
    binary = shutil.which(settings.CLAUDE_CLI_PATH)
    if binary is None:
        raise ClaudeUnavailableError("The claude CLI is not installed")

    env = {key: os.environ[key] for key in _PASSTHROUGH if key in os.environ}
    env["CLAUDE_CODE_OAUTH_TOKEN"] = settings.CLAUDE_CODE_OAUTH_TOKEN
    env["DISABLE_AUTOUPDATER"] = "1"  # never update itself mid-request
    workdir = Path(tempfile.gettempdir()) / "nativo-claude"
    workdir.mkdir(exist_ok=True)

    command = [
        binary,
        "-p",
        "--model",
        settings.AI_SUGGEST_MODEL,
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(schema),
        "--system-prompt",
        system,
        "--tools",
        "",
        "--setting-sources",
        "",
        "--strict-mcp-config",
        "--no-session-persistence",
    ]
    if not _slots.acquire(timeout=settings.AI_SUGGEST_TIMEOUT):
        raise ClaudeUnavailableError("Too many suggestions at once")
    try:
        done = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            text=True,
            env=env,
            cwd=workdir,
            timeout=settings.AI_SUGGEST_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ClaudeUnavailableError(f"claude CLI failed: {exc}") from exc
    finally:
        _slots.release()

    try:
        result = json.loads(done.stdout)
    except json.JSONDecodeError as exc:
        detail = (done.stderr or done.stdout).strip()[:300]
        raise ClaudeUnavailableError(f"claude CLI failed: {detail}") from exc
    if done.returncode != 0 or result.get("is_error"):
        raise ClaudeUnavailableError(f"claude CLI failed: {str(result.get('result'))[:300]}")

    answer = result.get("structured_output")
    if answer is None:
        try:
            answer = json.loads(result.get("result") or "")
        except json.JSONDecodeError as exc:
            raise ClaudeUnavailableError("claude CLI returned no JSON") from exc
    if not isinstance(answer, dict):
        raise ClaudeUnavailableError("claude CLI returned no JSON object")
    return answer
