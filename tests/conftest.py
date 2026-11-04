# 全局fixture(如 api session)

import pytest
import requests
from config.settings import BASE_URL,TIMEOUT

@pytest.fixture(scope="session")
def api():
    """全局共享的 requests Session"""
    with requests.Session() as session:
        session.base_url = BASE_URL
        session.timeout = TIMEOUT
        yield session