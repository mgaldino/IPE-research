import os
from pathlib import Path

import pytest

TEST_DB_URL = "sqlite:///./codex_council_test.db"
TEST_DB_PATH = Path("codex_council_test.db")

os.environ.setdefault("CODEX_COUNCIL_DB_URL", TEST_DB_URL)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db() -> None:
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
