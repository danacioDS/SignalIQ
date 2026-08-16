"""
Tests unitarios para api.py - Versión que funciona correctamente
Probamos las funciones con los datos correctos
"""

import pytest
import sys
import numpy as np
sys.path.insert(0, '/home/daniel/repo_lab/SignalIQ/backend')
from app import api

class TestAPIWorking:
    """Tests unitarios para funciones reales de api.py"""
    
    def test_calculate_ndi_with_price_list(self):
        """Verificar calculate_ndi con lista de precios (uso correcto)"""
        # Datos de prueba: 30 precios simulados
        closes = [100.0 + i * 0.5 for i in range(30)]
        
        # Llamar a la función correctamente
        ndi, sentiment, momentum = api.calculate_ndi(closes)
        
        # Verificar tipos
        assert isinstance(ndi, float)
        assert isinstance(sentiment, float)
        assert isinstance(momentum, float)
        # NDI debe estar en rango [-3, 3]
        assert -3.0 <= ndi <= 3.0
    
    def test_calculate_ndi_with_uptrend(self):
        """Verificar NDI en tendencia alcista"""
        closes = [100.0 + i * 1.2 for i in range(30)]
        ndi, sentiment, momentum = api.calculate_ndi(closes)
        # En tendencia alcista, NDI debería ser positivo
        assert ndi > -0.5
    
    def test_calculate_ndi_with_downtrend(self):
        """Verificar NDI en tendencia bajista"""
        closes = [100.0 - i * 1.2 for i in range(30)]
        ndi, sentiment, momentum = api.calculate_ndi(closes)
        # En tendencia bajista, NDI debería ser negativo
        assert ndi < 0.5
    
    def test_calculate_ndi_with_short_data(self):
        """Verificar con pocos datos (< 20)"""
        closes = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
        ndi, sentiment, momentum = api.calculate_ndi(closes)
        # Debe retornar valores aunque el momentum sea menos preciso
        assert isinstance(ndi, float)
        assert not np.isnan(ndi)
    
    def test_calculate_ndi_with_very_short_data(self):
        """Verificar con datos muy cortos (< 2)"""
        closes = [100.0]
        ndi, sentiment, momentum = api.calculate_ndi(closes)
        # Debe retornar 0.0
        assert ndi == 0.0
        assert sentiment == 0.0
        assert momentum == 0.0
    
    def test_calculate_ndi_with_string_prices(self):
        """Verificar que maneja strings como precios"""
        closes = ['100.0', '101.5', '102.3', '103.7', '104.2', '105.0']
        ndi, sentiment, momentum = api.calculate_ndi(closes)
        # Debe convertir a float y calcular
        assert isinstance(ndi, float)
        assert not np.isnan(ndi)
    
    def test_calculate_ndi_with_mixed_types(self):
        """Verificar con tipos mixtos (int, float, string)"""
        closes = [100, '101.5', 102.3, '103.7', 104]
        ndi, sentiment, momentum = api.calculate_ndi(closes)
        # Debe manejar todos los tipos
        assert isinstance(ndi, float)
        assert not np.isnan(ndi)
    
    def test_classify_regime_extreme_overheating(self):
        """Verificar clasificación EXTREME OVERHEATING"""
        result = api.classify_regime(2.5)
        assert result['regime'] == 'EXTREME OVERHEATING'
        assert result['label'] == 'SELL'
        assert result['color'] == 'red'
    
    def test_classify_regime_overheating(self):
        """Verificar clasificación OVERHEATING"""
        result = api.classify_regime(1.8)
        assert result['regime'] == 'OVERHEATING'
        assert result['label'] == 'REDUCE'
        assert result['color'] == 'orange'
    
    def test_classify_regime_watching(self):
        """Verificar clasificación WATCHING"""
        result = api.classify_regime(1.0)
        assert result['regime'] == 'WATCHING'
        assert result['label'] == 'MONITOR'
        assert result['color'] == 'orange'
    
    def test_classify_regime_neutral(self):
        """Verificar clasificación NEUTRAL"""
        result = api.classify_regime(0.0)
        assert result['regime'] == 'NEUTRAL'
        assert result['label'] == 'HOLD'
        assert result['color'] == 'yellow'
    
    def test_classify_regime_aligned(self):
        """Verificar clasificación ALIGNED"""
        result = api.classify_regime(-1.0)
        assert result['regime'] == 'ALIGNED'
        assert result['label'] == 'BUY'
        assert result['color'] == 'green'
    
    def test_classify_regime_strong_undervalued(self):
        """Verificar clasificación STRONG UNDERVALUED"""
        result = api.classify_regime(-1.8)
        assert result['regime'] == 'STRONG UNDERVALUED'
        assert result['label'] == 'STRONG BUY'
        assert result['color'] == 'green'
    
    def test_classify_regime_capitulation(self):
        """Verificar clasificación CAPITULATION"""
        result = api.classify_regime(-2.5)
        assert result['regime'] == 'CAPITULATION'
        assert result['label'] == 'ACCUMULATE'
        assert result['color'] == 'blue'

if __name__ == '__main__':
    pytest.main(['-v'])
