import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
project_root_str = str(PROJECT_ROOT)

if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)


@pytest.fixture(autouse=True)
def isolated_http_response_cache():
    from src.presentation.http.large_json import large_json

    large_json.cache.clear()
    yield
    assert (
        not large_json.flights
    ), "HTTP response did not release its temporary artifact"
    large_json.cache.clear()
