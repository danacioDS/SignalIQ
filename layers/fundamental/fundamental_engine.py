"""Layer 3 Fundamental Engine - Main Module"""

from typing import Dict, Optional, Any
from datetime import datetime
import numpy as np

from .metrics_calculator import FundamentalMetrics, MetricsCalculator
from .score_aggregator import FundamentalScoreAggregator


class FundamentalEngine:
    """
    Fundamental Analysis Engine for SignalIQ
    
    Processes financial metrics and generates normalized scores
    for integration with NDI and Bubble Risk Score.
    """
    
    def __init__(self):
        self.calculator = MetricsCalculator()
        self.aggregator = FundamentalScoreAggregator()
        self._cache: Dict[str, FundamentalMetrics] = {}
    
    def process_metrics(self, ticker: str, metrics_data: Dict[str, Any], 
                        sector: str = 'Default') -> Dict[str, Any]:
        """
        Process fundamental metrics for a ticker
        
        Args:
            ticker: Asset symbol
            metrics_data: Dictionary with raw metrics
            sector: Industry sector (for benchmarks)
            
        Returns:
            Dict with calculated metrics and scores
        """
        # Create metrics object
        metrics = FundamentalMetrics(
            ticker=ticker,
            date=datetime.now(),
            
            # Valuation
            pe_ratio=metrics_data.get('pe_ratio'),
            forward_pe=metrics_data.get('forward_pe'),
            pb_ratio=metrics_data.get('pb_ratio'),
            ps_ratio=metrics_data.get('ps_ratio'),
            
            # Growth
            eps_growth_1y=metrics_data.get('eps_growth_1y'),
            eps_growth_3y=metrics_data.get('eps_growth_3y'),
            revenue_growth_1y=metrics_data.get('revenue_growth_1y'),
            revenue_growth_3y=metrics_data.get('revenue_growth_3y'),
            
            # Profitability
            gross_margin=metrics_data.get('gross_margin'),
            operating_margin=metrics_data.get('operating_margin'),
            net_margin=metrics_data.get('net_margin'),
            roe=metrics_data.get('roe'),
            roa=metrics_data.get('roa'),
            
            # Cash Flow
            fcf=metrics_data.get('fcf'),
            fcf_yield=metrics_data.get('fcf_yield'),
            dividend_yield=metrics_data.get('dividend_yield'),
            
            # Debt
            debt_to_equity=metrics_data.get('debt_to_equity'),
            current_ratio=metrics_data.get('current_ratio'),
            interest_coverage=metrics_data.get('interest_coverage'),
            
            # Quality
            earnings_quality_score=metrics_data.get('earnings_quality_score'),
            accounting_risk=metrics_data.get('accounting_risk')
        )
        
        # Calculate derived metrics if needed
        if metrics_data.get('price') and metrics_data.get('eps'):
            metrics.pe_ratio = self.calculator.calculate_pe_ratio(
                metrics_data['price'], metrics_data['eps']
            )
        
        if metrics_data.get('fcf') and metrics_data.get('market_cap'):
            metrics.fcf_yield = self.calculator.calculate_fcf_yield(
                metrics_data['fcf'], metrics_data['market_cap']
            )
        
        # Calculate earnings quality if data available
        if metrics_data.get('accruals_ratio') and metrics_data.get('cash_conversion'):
            metrics.earnings_quality_score = self.calculator.calculate_earnings_quality(
                metrics_data['accruals_ratio'], metrics_data['cash_conversion']
            )
        
        # Cache
        self._cache[ticker] = metrics
        
        # Generate aggregated scores
        scores = self.aggregator.aggregate_score(metrics, sector)
        
        # Generate textual analysis (ENGLISH)
        analysis = self._generate_analysis(ticker, metrics, scores)
        
        return {
            'ticker': ticker,
            'metrics': self._metrics_to_dict(metrics),
            'scores': scores,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }
    
    def _metrics_to_dict(self, metrics: FundamentalMetrics) -> Dict:
        """Convert metrics object to dict for serialization"""
        return {
            'pe_ratio': metrics.pe_ratio,
            'forward_pe': metrics.forward_pe,
            'pb_ratio': metrics.pb_ratio,
            'ps_ratio': metrics.ps_ratio,
            'eps_growth_1y': metrics.eps_growth_1y,
            'revenue_growth_1y': metrics.revenue_growth_1y,
            'net_margin': metrics.net_margin,
            'roe': metrics.roe,
            'roa': metrics.roa,
            'fcf_yield': metrics.fcf_yield,
            'dividend_yield': metrics.dividend_yield,
            'debt_to_equity': metrics.debt_to_equity,
            'current_ratio': metrics.current_ratio
        }
    
    def _generate_analysis(self, ticker: str, metrics: FundamentalMetrics, 
                          scores: Dict) -> str:
        """Generate textual analysis of fundamentals (ENGLISH)"""
        
        score = scores['fundamental_score']
        rating = scores['quality_rating']
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        if metrics.roe and metrics.roe > 0.15:
            strengths.append(f"Strong ROE of {metrics.roe*100:.1f}%")
        elif metrics.roe and metrics.roe < 0.05:
            weaknesses.append(f"Low ROE ({metrics.roe*100:.1f}%)")
        
        if metrics.eps_growth_1y and metrics.eps_growth_1y > 0.10:
            strengths.append(f"EPS growth of {metrics.eps_growth_1y*100:.1f}%")
        elif metrics.eps_growth_1y and metrics.eps_growth_1y < 0:
            weaknesses.append(f"EPS contraction ({metrics.eps_growth_1y*100:.1f}%)")
        
        if metrics.net_margin and metrics.net_margin > 0.15:
            strengths.append(f"High net margin of {metrics.net_margin*100:.1f}%")
        elif metrics.net_margin and metrics.net_margin < 0.05:
            weaknesses.append(f"Low net margin ({metrics.net_margin*100:.1f}%)")
        
        if metrics.debt_to_equity and metrics.debt_to_equity > 2:
            weaknesses.append(f"High leverage (D/E {metrics.debt_to_equity:.1f}x)")
        elif metrics.debt_to_equity and metrics.debt_to_equity < 0.3:
            strengths.append(f"Low debt (D/E {metrics.debt_to_equity:.1f}x)")
        
        if metrics.current_ratio and metrics.current_ratio < 1.0:
            weaknesses.append(f"Liquidity concern (Current ratio {metrics.current_ratio:.1f})")
        elif metrics.current_ratio and metrics.current_ratio > 2.0:
            strengths.append(f"Strong liquidity (Current ratio {metrics.current_ratio:.1f})")
        
        # Valuation interpretation
        valuation_text = {
            'Cheap': 'Appears undervalued relative to fundamentals',
            'Fair': 'Trading near fair value',
            'Rich': 'Premium valuation may limit upside'
        }.get(scores.get('valuation_text', 'Fair'), 'Fairly valued')
        
        # Growth interpretation
        growth_text = {
            'Strong': 'Robust growth trajectory supporting narrative',
            'Moderate': 'Solid but not exceptional growth',
            'Weak': 'Growth concerns may weigh on sentiment'
        }.get(scores.get('growth_text', 'Moderate'), 'Moderate growth profile')
        
        # Financial health interpretation
        health_text = {
            'Strong': 'Balance sheet provides crisis buffer',
            'Adequate': 'Sufficient financial flexibility',
            'Risky': 'Leverage increases risk profile'
        }.get(scores.get('health_text', 'Adequate'), 'Adequate financial position')
        
        analysis = f"""
📊 **Fundamental Analysis - {ticker}**

**Overall Score: {score:.1f}/100 ({rating})**

**Key Strengths:** {', '.join(strengths) if strengths else 'No significant strengths identified'}
**Key Weaknesses:** {', '.join(weaknesses) if weaknesses else 'No significant weaknesses identified'}

**Valuation Assessment:** {valuation_text}
**Growth Profile:** {growth_text}
**Financial Health:** {health_text}

**Implications for NDI:**
- {self._get_ndi_implication(score, scores.get('valuation_score', 50))}

**Bubble Risk Contribution:** {100 - score:.1f}% of risk score attributed to fundamentals
"""
        return analysis.strip()
    
    def _get_ndi_implication(self, fundamental_score: float, valuation_score: float) -> str:
        """Generate NDI implication based on fundamental strength"""
        if fundamental_score > 70:
            return "Strong fundamentals may justify premium valuation and higher NDI levels"
        elif fundamental_score > 50:
            if valuation_score > 70:
                return "Solid fundamentals but valuation stretched - monitor for divergence"
            else:
                return "Adequate fundamentals providing moderate support to current narrative"
        elif fundamental_score > 30:
            return "Weak fundamentals suggest narrative may be disconnected from reality"
        else:
            return "Critical fundamental weakness - narrative divergence likely overstates value"
    
    def get_ticker_metrics(self, ticker: str) -> Optional[FundamentalMetrics]:
        """Get cached metrics for a ticker"""
        return self._cache.get(ticker)
    
    def get_bubble_risk_contribution(self, ticker: str) -> Optional[float]:
        """
        Calculate fundamental contribution to Bubble Risk Score
        (Inverse: weaker fundamentals → higher risk contribution)
        """
        if ticker not in self._cache:
            return None
        
        metrics = self._cache[ticker]
        scores = self.aggregator.aggregate_score(metrics)
        
        fundamental_score = scores['fundamental_score']
        
        # Transform: low score (weak fundamentals) → high risk contribution
        # High score (strong fundamentals) → low risk contribution
        risk_contribution = max(0, min(100, 100 - fundamental_score))
        
        return risk_contribution
    
    def get_ndi_adjustment(self, ticker: str, narrative_score: float) -> float:
        """
        Adjust NDI based on fundamentals
        Strong fundamentals cushion negative divergences
        """
        if ticker not in self._cache:
            return narrative_score
        
        metrics = self._cache[ticker]
        scores = self.aggregator.aggregate_score(metrics)
        
        fundamental_score = scores['fundamental_score']
        
        # Adjustment: strong fundamentals reduce NDI by up to 30%
        if fundamental_score > 70 and narrative_score > 1.5:
            # Strong fundamentals justify positive narrative
            adjusted = narrative_score * 0.7
        elif fundamental_score < 30 and narrative_score < -1.5:
            # Weak fundamentals justify negative narrative
            adjusted = narrative_score * 0.7
        else:
            adjusted = narrative_score
        
        return adjusted


# Example data for testing
EXAMPLE_FUNDAMENTALS = {
    'NVDA': {
        'pe_ratio': 65.4,
        'forward_pe': 42.1,
        'ps_ratio': 28.3,
        'pb_ratio': 52.1,
        'eps_growth_1y': 0.85,
        'revenue_growth_1y': 1.26,
        'net_margin': 0.48,
        'roe': 0.71,
        'roa': 0.42,
        'fcf_yield': 0.018,
        'debt_to_equity': 0.35,
        'current_ratio': 2.8,
        'market_cap': 2800000000000,
        'price': 890.0,
        'eps': 13.6
    },
    'AAPL': {
        'pe_ratio': 28.4,
        'forward_pe': 25.1,
        'ps_ratio': 7.2,
        'pb_ratio': 46.1,
        'eps_growth_1y': 0.12,
        'revenue_growth_1y': 0.05,
        'net_margin': 0.26,
        'roe': 1.56,
        'roa': 0.28,
        'fcf_yield': 0.035,
        'debt_to_equity': 1.8,
        'current_ratio': 0.99,
        'market_cap': 2800000000000,
        'price': 175.0,
        'eps': 6.16
    },
    'MSFT': {
        'pe_ratio': 34.2,
        'forward_pe': 30.1,
        'ps_ratio': 12.5,
        'pb_ratio': 15.3,
        'eps_growth_1y': 0.18,
        'revenue_growth_1y': 0.14,
        'net_margin': 0.36,
        'roe': 0.38,
        'roa': 0.15,
        'fcf_yield': 0.028,
        'debt_to_equity': 0.62,
        'current_ratio': 1.85,
        'market_cap': 3100000000000,
        'price': 420.0,
        'eps': 12.28
    }
}
