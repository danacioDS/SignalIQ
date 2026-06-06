"""Métricas fundamentales según especificación de SignalIQ"""

import numpy as np
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FundamentalMetrics:
    """Contenedor de métricas fundamentales"""
    ticker: str
    date: datetime
    
    # Valuation Ratios
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    
    # Growth Metrics
    eps_growth_1y: Optional[float] = None
    eps_growth_3y: Optional[float] = None
    revenue_growth_1y: Optional[float] = None
    revenue_growth_3y: Optional[float] = None
    
    # Profitability
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roe: Optional[float] = None  # Return on Equity
    roa: Optional[float] = None  # Return on Assets
    
    # Cash Flow
    fcf: Optional[float] = None  # Free Cash Flow
    fcf_yield: Optional[float] = None
    dividend_yield: Optional[float] = None
    
    # Debt
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None
    
    # Quality
    earnings_quality_score: Optional[float] = None  # 0-100
    accounting_risk: Optional[str] = None  # Low, Medium, High


class MetricsCalculator:
    """Calculadora de métricas fundamentales"""
    
    @staticmethod
    def calculate_pe_ratio(price: float, eps: float) -> Optional[float]:
        """Price-to-Earnings Ratio"""
        if eps is None or eps <= 0:
            return None
        return round(price / eps, 2)
    
    @staticmethod
    def calculate_forward_pe(price: float, estimated_eps: float) -> Optional[float]:
        """Forward P/E basado en EPS estimado"""
        if estimated_eps is None or estimated_eps <= 0:
            return None
        return round(price / estimated_eps, 2)
    
    @staticmethod
    def calculate_pb_ratio(price: float, book_value_per_share: float) -> Optional[float]:
        """Price-to-Book Ratio"""
        if book_value_per_share is None or book_value_per_share <= 0:
            return None
        return round(price / book_value_per_share, 2)
    
    @staticmethod
    def calculate_ps_ratio(price: float, revenue_per_share: float) -> Optional[float]:
        """Price-to-Sales Ratio"""
        if revenue_per_share is None or revenue_per_share <= 0:
            return None
        return round(price / revenue_per_share, 2)
    
    @staticmethod
    def calculate_growth_rate(current: float, previous: float) -> Optional[float]:
        """Calcula tasa de crecimiento anualizada"""
        if previous is None or previous == 0:
            return None
        growth = (current - previous) / abs(previous)
        return round(growth, 4)
    
    @staticmethod
    def calculate_cagr(start_value: float, end_value: float, years: int) -> Optional[float]:
        """Compound Annual Growth Rate"""
        if start_value is None or start_value <= 0 or years <= 0:
            return None
        cagr = (end_value / start_value) ** (1 / years) - 1
        return round(cagr, 4)
    
    @staticmethod
    def calculate_margin(numerator: float, denominator: float) -> Optional[float]:
        """Calcula cualquier margen (gross, operating, net)"""
        if denominator is None or denominator == 0:
            return None
        margin = numerator / denominator
        return round(margin, 4)
    
    @staticmethod
    def calculate_roe(net_income: float, shareholder_equity: float) -> Optional[float]:
        """Return on Equity = Net Income / Shareholder's Equity"""
        if shareholder_equity is None or shareholder_equity == 0:
            return None
        roe = net_income / shareholder_equity
        return round(roe, 4)
    
    @staticmethod
    def calculate_roa(net_income: float, total_assets: float) -> Optional[float]:
        """Return on Assets = Net Income / Total Assets"""
        if total_assets is None or total_assets == 0:
            return None
        roa = net_income / total_assets
        return round(roa, 4)
    
    @staticmethod
    def calculate_fcf_yield(fcf: float, market_cap: float) -> Optional[float]:
        """Free Cash Flow Yield = FCF / Market Cap"""
        if market_cap is None or market_cap == 0:
            return None
        return round(fcf / market_cap, 4)
    
    @staticmethod
    def calculate_debt_to_equity(total_debt: float, shareholder_equity: float) -> Optional[float]:
        """Debt-to-Equity Ratio"""
        if shareholder_equity is None or shareholder_equity == 0:
            return None
        return round(total_debt / shareholder_equity, 2)
    
    @staticmethod
    def calculate_current_ratio(current_assets: float, current_liabilities: float) -> Optional[float]:
        """Current Ratio (Liquidez)"""
        if current_liabilities is None or current_liabilities == 0:
            return None
        return round(current_assets / current_liabilities, 2)
    
    @staticmethod
    def calculate_interest_coverage(ebit: float, interest_expense: float) -> Optional[float]:
        """Interest Coverage Ratio = EBIT / Interest Expense"""
        if interest_expense is None or interest_expense == 0:
            return None
        return round(ebit / interest_expense, 2)
    
    @staticmethod
    def calculate_earnings_quality(accruals_ratio: float, cash_conversion: float) -> float:
        """
        Earnings Quality Score (0-100)
        Mayor puntaje = mayor calidad de ganancias
        """
        # Accruals ratio: menor es mejor (inverso)
        accruals_score = max(0, 100 - (abs(accruals_ratio) * 100)) if accruals_ratio else 50
        
        # Cash conversion: mayor es mejor
        cash_score = min(100, cash_conversion * 100) if cash_conversion else 50
        
        # Promedio ponderado
        quality_score = (accruals_score * 0.6) + (cash_score * 0.4)
        return round(quality_score, 1)
