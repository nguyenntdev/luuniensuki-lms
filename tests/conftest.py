import sys
from pathlib import Path

# Add repo root to sys.path so tests can import research and backend
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

pytest_plugins = ["tests.backend.conftest"]

