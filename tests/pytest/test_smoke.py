"""Smoke tests for SignalIQ - verify imports work."""

import sys
import os
import pytest

# Add backend/app to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend/app'))

def test_import_layer4():
    """Test that Layer 4 orchestrator can be imported."""
    from layers.layer4_orchestrator import Layer4Orchestrator
    assert Layer4Orchestrator is not None

def test_import_config():
    """Test that thresholds can be imported."""
    from config.thresholds import NDI_OVERHEATING
    assert NDI_OVERHEATING == 1.5

def test_import_news_pipeline():
    """Test that news_pipeline can be imported."""
    # Try relative import first (when imported as module)
    try:
        from app.news_pipeline import process_news_for_ticker
    except ImportError:
        # Fallback to absolute import
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend/app'))
        from news_pipeline import process_news_for_ticker
    assert callable(process_news_for_ticker)

def test_api_import():
    """Test that the production API can be imported."""
    # Add backend to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))
    from app import main
    assert hasattr(main, 'app')
    assert hasattr(main, 'get_ticker_data')
