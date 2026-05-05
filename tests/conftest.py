from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path

import pytest


@pytest.fixture
def tmp_path(request: pytest.FixtureRequest) -> Path:
    """Create test temp dirs without pytest's Windows 0o700 ACL handling.

    In the Codex Windows sandbox, Python directories created with mode 0o700 can
    become unreadable even to the creating process. Pytest's built-in tmp_path
    uses that mode for basetemp, so keep this repository's temp dirs local and
    create them with the platform default ACL instead.
    """
    root = Path(request.config.rootpath) / ".tmp" / "pytest-local"
    root.mkdir(parents=True, exist_ok=True)

    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", request.node.name).strip("_")
    path = root / f"{safe_name}-{uuid.uuid4().hex}"
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
