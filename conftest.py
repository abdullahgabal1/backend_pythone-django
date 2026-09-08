"""
Pytest global configuration and fixtures.
"""
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Fixture providing a standard DRF API client."""
    return APIClient()
