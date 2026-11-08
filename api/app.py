"""Default ASGI application for local and container execution."""

from __future__ import annotations

import os

from industrialops.api import create_app
from industrialops.config import Settings


app = create_app(Settings.from_environment(os.environ))
