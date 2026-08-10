"""Tests unitarios para el cálculo del NDI."""

import pytest
import sys
import os

# Agregar el path correcto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from app.main import calculate_ndi

def test_calculate_ndi_returns_dict():
    """Verificar que calculate_ndi devuelve un dict."""
    result = calculate_ndi("NVDA")
    assert isinstance(result, dict)
    assert 'ndi' in result

def test_calculate_ndi_has_required_fields():
    """Verificar que calculate_ndi tiene todos los campos necesarios."""
    result = calculate_ndi("NVDA")
    required_fields = ['ticker', 'price', 'current_price', 'sentiment', 'momentum', 'ndi', 'regime', 'signal', 'confidence']
    for field in required_fields:
        assert field in result, f"Falta el campo {field}"

def test_calculate_ndi_ndi_range():
    """Verificar que el NDI está en el rango esperado."""
    result = calculate_ndi("NVDA")
    ndi = result.get('ndi', 0)
    assert -3.0 <= ndi <= 3.0, f"NDI fuera de rango: {ndi}"

def test_calculate_ndi_consistency():
    """Verificar que calculate_ndi es consistente."""
    result1 = calculate_ndi("NVDA")
    result2 = calculate_ndi("NVDA")
    
    price1 = result1.get('price', 0)
    price2 = result2.get('price', 0)
    assert abs(price1 - price2) < 10.0, f"Los precios difieren mucho: {price1} vs {price2}"

def test_calculate_ndi_regime_mapping():
    """Verificar que los regímenes son válidos."""
    valid_regimes = ['OVERHEATING', 'WATCHING', 'NEUTRAL', 'ALIGNED', 'UNDERVALUED', 'EXTREME_OVERHEATING', 'CAPITULATION']
    result = calculate_ndi("NVDA")
    regime = result.get('regime', '')
    assert regime in valid_regimes, f"Régimen inválido: {regime}"

def test_calculate_ndi_ticker_case_insensitive():
    """Verificar que los tickers son case-insensitive."""
    result1 = calculate_ndi("NVDA")
    result2 = calculate_ndi("nvda")
    assert result1.get('ticker', '').upper() == result2.get('ticker', '').upper()

def test_calculate_ndi_invalid_ticker():
    """Verificar que tickers inválidos manejan el error correctamente."""
    result = calculate_ndi("INVALID_TICKER")
    assert isinstance(result, dict)
    assert 'ndi' in result
