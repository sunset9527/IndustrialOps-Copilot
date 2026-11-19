"""Default ASGI application for local and container execution."""

from __future__ import annotations

import os

from industrialops.api import create_app
from industrialops.config import Settings
from industrialops.logging_config import configure_logging


configure_logging()
app = create_app(Settings.from_environment(os.environ))
