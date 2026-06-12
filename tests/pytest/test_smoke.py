"""
SMOKE TESTS - Single source of truth for CI.
Legacy tests (test_layer1_integration.py, test_layer3.py, test_layer4.py)
are DEPRECATED but preserved for reference.
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

@pytest.mark.smoke
def test_import_layer4():
    from layers.layer4_orchestrator import process_asset, OUTPUT_FIELDS
    assert OUTPUT_FIELDS is not None
    assert callable(process_asset)

@pytest.mark.smoke
def test_import_config():
    from signaliq.core.config import config
    assert hasattr(config, 'DATA_DIR')
    assert hasattr(config, 'db_url')
    assert hasattr(config, 'db')

@pytest.mark.smoke
def test_import_layer1():
    from layer1.collect_prices import fetch_asset_price, normalize_price_response
    assert callable(fetch_asset_price)
    assert callable(normalize_price_response)

@pytest.mark.smoke
def test_api_import():
    from backend.app.main import app
    assert app is not None
