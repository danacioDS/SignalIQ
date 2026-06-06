#!/usr/bin/env python3
"""Test del Fundamental Engine"""

from layers.fundamental.fundamental_engine import FundamentalEngine, EXAMPLE_FUNDAMENTALS

print("=" * 70)
print("SignalIQ - Fundamental Engine Test")
print("=" * 70)

# Crear motor
engine = FundamentalEngine()

print("\n📊 Processing fundamentals for NVDA, AAPL, MSFT...")

for ticker, metrics in EXAMPLE_FUNDAMENTALS.items():
    print(f"\n{'='*70}")
    result = engine.process_metrics(ticker, metrics, sector='Technology')
    
    print(f"\n📈 {ticker} - Results:")
    print(f"   Fundamental Score: {result['scores']['fundamental_score']:.1f}/100")
    print(f"   Rating: {result['scores']['quality_rating']}")
    print(f"\n   Scores by category:")
    print(f"     - Valuation:     {result['scores']['valuation_score']:.1f}")
    print(f"     - Growth:        {result['scores']['growth_score']:.1f}")
    print(f"     - Profitability: {result['scores']['profitability_score']:.1f}")
    print(f"     - Cash Flow:     {result['scores']['cash_flow_score']:.1f}")
    print(f"     - Financial Hlth: {result['scores']['financial_health_score']:.1f}")
    
    print(f"\n   Key Metrics:")
    metrics_data = result['metrics']
    if metrics_data.get('pe_ratio'):
        print(f"     - P/E: {metrics_data['pe_ratio']:.1f}x")
    if metrics_data.get('roe'):
        print(f"     - ROE: {metrics_data['roe']*100:.1f}%")
    if metrics_data.get('eps_growth_1y'):
        print(f"     - EPS Growth: {metrics_data['eps_growth_1y']*100:.1f}%")
    if metrics_data.get('debt_to_equity'):
        print(f"     - D/E: {metrics_data['debt_to_equity']:.2f}x")
    
    print(f"\n   Analysis:")
    print(result['analysis'])
    
    # Calculate contribution to Bubble Risk
    risk_contrib = engine.get_bubble_risk_contribution(ticker)
    if risk_contrib:
        print(f"\n   🎯 Contribution to Bubble Risk Score: {risk_contrib:.1f}/100")
        if risk_contrib < 40:
            print("      ✅ Strong fundamentals → low risk")
        elif risk_contrib > 60:
            print("      ⚠️ Weak fundamentals → high risk")

print("\n" + "=" * 70)
print("✅ Fundamental Engine test completed")
print("=" * 70)
