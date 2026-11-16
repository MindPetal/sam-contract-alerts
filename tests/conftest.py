"""
Shared test fixtures
"""

import pytest

import client


@pytest.fixture
def api_client():
    api_config = client.Configuration()
    api_config.host = "https://api.sam.gov"

    return client.ApiClient(api_config)
