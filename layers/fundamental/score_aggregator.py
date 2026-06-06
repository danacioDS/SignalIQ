"""Fundamental score aggregator for SignalIQ"""

import numpy as np
from typing import Dict, Optional, List
from .metrics_calculator import FundamentalMetrics


class FundamentalScoreAggregator:
    """
    Aggregates fundamental metrics into a single score (0-100)
    according to SignalIQ methodology
    """
    
    # Weights by category (adjustable)
    CATEGORY_WEIGHTS = {
        'valuation': 0.25,      # 25% - Valuation ratios
        'growth': 0.30,          # 30% - Growth metrics
        'profitability': 0.20,   # 20% - Margins, ROE, ROA
        'cash_flow': 0.15,       # 15% - FCF, dividend yield
        'financial_health': 0.10 # 10% - Debt, liquidity
    }
    
    # Valuation benchmarks by sector (adjustable)
    SECTOR_VALUATION_BENCHMARKS = {
        'Technology': {'pe_benchmark': 25, 'ps_benchmark': 6, 'pb_benchmark': 8},
        'Financials': {'pe_benchmark': 15, 'ps_benchmark': 3, 'pb_benchmark': 1.5},
        'Healthcare': {'pe_benchmark': 20, 'ps_benchmark': 4, 'pb_benchmark': 5},
        'Consumer': {'pe_benchmark': 18, 'ps_benchmark': 2, 'pb_benchmark': 4},
        'Energy': {'pe_benchmark': 12, 'ps_benchmark': 1.5, 'pb_benchmark': 1.8},
        'Industrial': {'pe_benchmark': 16, 'ps_benchmark': 2, 'pb_benchmark': 3},
        'Default': {'pe_benchmark': 20, 'ps_benchmark': 3, 'pb_benchmark': 4}
    }
    
    @classmethod
    def _score_valuation(cls, metrics: FundamentalMetrics, sector: str = 'Default') -> Dict:
        """Valuation score (lower P/E, better score)"""
        benchmarks = cls.SECTOR_VALUATION_BENCHMARKS.get(sector, cls.SECTOR_VALUATION_BENCHMARKS['Default'])
        
        scores = []
        
        # P/E Score (inverse)
        if metrics.pe_ratio:
            pe_score = max(0, 100 * (benchmarks['pe_benchmark'] / metrics.pe_ratio))
            pe_score = min(100, pe_score)
            scores.append(pe_score)
        
        # P/S Score (inverse)
        if metrics.ps_ratio:
            ps_score = max(0, 100 * (benchmarks['ps_benchmark'] / metrics.ps_ratio))
            ps_score = min(100, ps_score)
            scores.append(ps_score)
        
        # P/B Score (inverse)
        if metrics.pb_ratio:
            pb_score = max(0, 100 * (benchmarks['pb_benchmark'] / metrics.pb_ratio))
            pb_score = min(100, pb_score)
            scores.append(pb_score)
        
        score = np.mean(scores) if scores else 50
        
        # Determine valuation text
        if score > 70:
            text = "Cheap"
        elif score > 40:
            text = "Fair"
        else:
            text = "Rich"
        
        return {'score': score, 'text': text}
    
    @classmethod
    def _score_growth(cls, metrics: FundamentalMetrics) -> Dict:
        """Growth score (higher growth, better score)"""
        scores = []
        
        # EPS Growth
        if metrics.eps_growth_1y:
            eps_score = min(100, max(0, (metrics.eps_growth_1y + 0.5) * 100))
            scores.append(eps_score)
        
        # Revenue Growth
        if metrics.revenue_growth_1y:
            rev_score = min(100, max(0, (metrics.revenue_growth_1y + 0.5) * 100))
            scores.append(rev_score)
        
        # CAGR 3-year if available
        if metrics.eps_growth_3y:
            cagr_score = min(100, max(0, (metrics.eps_growth_3y + 0.3) * 100))
            scores.append(cagr_score)
        
        score = np.mean(scores) if scores else 50
        
        # Determine growth text
        if score > 65:
            text = "Strong"
        elif score > 35:
            text = "Moderate"
        else:
            text = "Weak"
        
        return {'score': score, 'text': text}
    
    @classmethod
    def _score_profitability(cls, metrics: FundamentalMetrics) -> Dict:
        """Profitability score (higher margins/ROE, better score)"""
        scores = []
        
        # Net Margin
        if metrics.net_margin:
            margin_score = min(100, metrics.net_margin * 200)
            scores.append(margin_score)
        
        # ROE
        if metrics.roe:
            roe_score = min(100, metrics.roe * 200)
            scores.append(roe_score)
        
        # ROA
        if metrics.roa:
            roa_score = min(100, metrics.roa * 300)
            scores.append(roa_score)
        
        # Operating Margin
        if metrics.operating_margin:
            op_score = min(100, metrics.operating_margin * 200)
            scores.append(op_score)
        
        score = np.mean(scores) if scores else 50
        
        # Determine profitability text
        if score > 65:
            text = "High"
        elif score > 35:
            text = "Average"
        else:
            text = "Low"
        
        return {'score': score, 'text': text}
    
    @classmethod
    def _score_cash_flow(cls, metrics: FundamentalMetrics) -> float:
        """Cash flow score"""
        scores = []
        
        # FCF Yield
        if metrics.fcf_yield:
            fcf_score = min(100, metrics.fcf_yield * 500)
            scores.append(fcf_score)
        
        # Dividend Yield
        if metrics.dividend_yield:
            div_score = min(100, metrics.dividend_yield * 200)
            scores.append(div_score)
        
        # Earnings Quality
        if metrics.earnings_quality_score:
            scores.append(metrics.earnings_quality_score)
        
        return np.mean(scores) if scores else 50
    
    @classmethod
    def _score_financial_health(cls, metrics: FundamentalMetrics) -> Dict:
        """Financial health score (lower debt, better)"""
        scores = []
        
        # Debt-to-Equity (inverse)
        if metrics.debt_to_equity:
            if metrics.debt_to_equity <= 0.5:
                de_score = 100
            elif metrics.debt_to_equity <= 1.0:
                de_score = 75
            elif metrics.debt_to_equity <= 2.0:
                de_score = 50
            elif metrics.debt_to_equity <= 3.0:
                de_score = 25
            else:
                de_score = 0
            scores.append(de_score)
        
        # Current Ratio
        if metrics.current_ratio:
            if metrics.current_ratio >= 2.0:
                cr_score = 100
            elif metrics.current_ratio >= 1.5:
                cr_score = 75
            elif metrics.current_ratio >= 1.0:
                cr_score = 50
            else:
                cr_score = 25
            scores.append(cr_score)
        
        # Interest Coverage (inverse)
        if metrics.interest_coverage:
            if metrics.interest_coverage >= 10:
                ic_score = 100
            elif metrics.interest_coverage >= 5:
                ic_score = 75
            elif metrics.interest_coverage >= 2:
                ic_score = 50
            else:
                ic_score = 25
            scores.append(ic_score)
        
        score = np.mean(scores) if scores else 50
        
        # Determine health text
        if score > 65:
            text = "Strong"
        elif score > 35:
            text = "Adequate"
        else:
            text = "Risky"
        
        return {'score': score, 'text': text}
    
    @classmethod
    def aggregate_score(cls, metrics: FundamentalMetrics, sector: str = 'Default') -> Dict[str, float]:
        """
        Calculate complete fundamental score
        
        Returns:
            Dict with individual scores and composite score
        """
        valuation = cls._score_valuation(metrics, sector)
        growth = cls._score_growth(metrics)
        profitability = cls._score_profitability(metrics)
        cash_flow = cls._score_cash_flow(metrics)
        financial_health = cls._score_financial_health(metrics)
        
        # Composite weighted score
        composite_score = sum([
            valuation['score'] * cls.CATEGORY_WEIGHTS['valuation'],
            growth['score'] * cls.CATEGORY_WEIGHTS['growth'],
            profitability['score'] * cls.CATEGORY_WEIGHTS['profitability'],
            cash_flow * cls.CATEGORY_WEIGHTS['cash_flow'],
            financial_health['score'] * cls.CATEGORY_WEIGHTS['financial_health']
        ])
        
        return {
            'valuation_score': valuation['score'],
            'valuation_text': valuation['text'],
            'growth_score': growth['score'],
            'growth_text': growth['text'],
            'profitability_score': profitability['score'],
            'profitability_text': profitability['text'],
            'cash_flow_score': cash_flow,
            'financial_health_score': financial_health['score'],
            'health_text': financial_health['text'],
            'fundamental_score': round(composite_score, 1),
            'quality_rating': cls._get_rating(composite_score)
        }
    
    @classmethod
    def _get_rating(cls, score: float) -> str:
        """Convert numeric score to qualitative rating"""
        if score >= 80:
            return "Excellent"
        elif score >= 65:
            return "Good"
        elif score >= 50:
            return "Fair"
        elif score >= 35:
            return "Weak"
        else:
            return "Poor"
