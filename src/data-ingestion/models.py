"""SQLAlchemy models re-exported for data-ingestion service."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared", "db"))
from models import *  # noqa: F401, F403, E402
