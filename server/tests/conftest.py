import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    from app import rate_limit

    rate_limit.reset()
