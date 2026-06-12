"""
Full system integration test
Validates that the system can boot and respond to requests.
"""

import pytest
import requests
import os

@pytest.mark.integration
def test_full_system_boot():
    try:
        response = requests.get('http://localhost:10000/api/health', timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'ok'
    except requests.ConnectionError:
        pytest.skip("Flask not running on port 10000")

@pytest.mark.integration
def test_api_contract():
    try:
        response = requests.get('http://localhost:10000/api/stats', timeout=5)
        if response.status_code == 200:
            data = response.json()
            assert 'success' in data
            assert 'total_signals' in data or 'error' in data
    except requests.ConnectionError:
        pytest.skip("Flask not running")
