"""
Shared rate-limit instance. Endpoints import `limiter` from here and decorate
with @limiter.limit("…"); main.py wires it to the app state and registers the
exception handler.

Keyed by the remote client IP. Uvicorn must be started with --proxy-headers so
X-Forwarded-For from Fly's edge is honored, otherwise every request shares the
proxy's IP and the limit becomes global.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
