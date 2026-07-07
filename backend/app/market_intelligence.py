from flask import Blueprint, jsonify, request
from datetime import datetime
import numpy as np
from app.db import get_connection, put_connection

market_intel_bp = Blueprint('market_intel', __name__)

@market_intel_bp.route('/api/ticker/analysis/<ticker>', methods=['GET'])
def get_ticker_analysis(ticker):
    """Market Intelligence - Análisis profundo del ticker"""
    ticker = ticker.strip().upper()
    
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # ============================================================
        # 1. OBTENER SEÑAL DE LAYER 4
        # ============================================================
        cur.execute("""
            SELECT 
                ndi,
                regime,
                confidence,
                signal_date
            FROM layer4.signals
            WHERE ticker = %s
            ORDER BY signal_date DESC
            LIMIT 1
        """, (ticker,))
        row = cur.fetchone()
        
        if not row:
            return jsonify({'error': f'No signals found for {ticker}'}), 404
        
        ndi, regime, confidence, signal_date = row
        
        # ============================================================
        # 2. OBTENER PRECIO ACTUAL
        # ============================================================
        cur.execute("""
            SELECT close
            FROM prices
            WHERE ticker = %s
            ORDER BY price_date DESC
            LIMIT 1
        """, (ticker,))
        price_row = cur.fetchone()
        price = price_row[0] if price_row else 0
        
        # ============================================================
        # 3. OBTENER SENTIMENT Y MOMENTUM DESDE LA TABLA prices
        # ============================================================
        # Usamos los últimos 20 días para calcular momentum y sentimiento
        cur.execute("""
            SELECT close
            FROM prices
            WHERE ticker = %s
            ORDER BY price_date DESC
            LIMIT 20
        """, (ticker,))
        price_rows = cur.fetchall()
        
        if price_rows and len(price_rows) >= 2:
            closes = [float(r[0]) for r in reversed(price_rows)]
            # Sentiment: retorno diario (simplificado)
            sentiment = (closes[-1] - closes[-2]) / closes[-2] if closes[-2] > 0 else 0
            # Momentum: retorno de 20 días
            momentum = (closes[-1] - closes[0]) / closes[0] if closes[0] > 0 else 0
        else:
            sentiment = 0
            momentum = 0
        
        # ============================================================
        # 4. OBTENER FUENTES DE NOTICIAS
        # ============================================================
        cur.execute("""
            SELECT source, COUNT(*) as count
            FROM headlines
            WHERE ticker = %s
            AND created_at >= NOW() - INTERVAL '7 days'
            GROUP BY source
            ORDER BY count DESC
        """, (ticker,))
        sources_rows = cur.fetchall()
        sources_count = sum(row[1] for row in sources_rows) if sources_rows else 0
        unique_sources = len(sources_rows)
        
        # ============================================================
        # 5. OBTENER NOTICIAS RECIENTES
        # ============================================================
        cur.execute("""
            SELECT source, headline, created_at
            FROM headlines
            WHERE ticker = %s
            ORDER BY created_at DESC
            LIMIT 5
        """, (ticker,))
        news_rows = cur.fetchall()
        
        # ============================================================
        # 6. CALCULAR MÉTRICAS NARRATIVAS
        # ============================================================
        consensus_pct = min(95, int(50 + (confidence or 50) * 0.5))
        intensity_pct = min(90, int(20 + unique_sources * 3))
        dispersion = abs(sentiment - momentum) if sentiment and momentum else 0.5
        
        # ============================================================
        # 7. NARRATIVE EXHAUSTION
        # ============================================================
        conditions_met = 0
        conditions_details = []
        
        # Condición 1: Divergencia sentiment vs momentum
        if sentiment and momentum and abs(sentiment - momentum) > 0.1:
            conditions_met += 1
            conditions_details.append({
                'id': 'cond-1',
                'description': f'Sentiment ({sentiment:.3f}) vs Momentum ({momentum:.3f}) - Divergencia',
                'isMet': True
            })
        else:
            conditions_details.append({
                'id': 'cond-1',
                'description': f'Sentiment ({sentiment:.3f}) y Momentum ({momentum:.3f}) alineados',
                'isMet': False
            })
        
        # Condición 2: Alta cobertura mediática
        if unique_sources > 5:
            conditions_met += 1
            conditions_details.append({
                'id': 'cond-2',
                'description': f'{unique_sources} fuentes en 7 días - Alta cobertura',
                'isMet': True
            })
        else:
            conditions_details.append({
                'id': 'cond-2',
                'description': f'{unique_sources} fuentes en 7 días - Cobertura normal',
                'isMet': False
            })
        
        # Condición 3: Confianza alta
        if confidence and confidence > 70:
            conditions_met += 1
            conditions_details.append({
                'id': 'cond-3',
                'description': f'Confianza: {confidence:.1f}% - Alta',
                'isMet': True
            })
        else:
            conditions_details.append({
                'id': 'cond-3',
                'description': f'Confianza: {confidence:.1f}% - Moderada',
                'isMet': False
            })
        
        exhaustion_map = {3: 'CRÍTICA', 2: 'ALTA', 1: 'MEDIA', 0: 'BAJA'}
        exhaustion_status = exhaustion_map.get(conditions_met, 'BAJA')
        
        # ============================================================
        # 8. RANKING REAL
        # ============================================================
        cur.execute("""
            SELECT ticker, ndi
            FROM layer4.signals
            WHERE ticker IN ('NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN')
            AND signal_date = (
                SELECT MAX(signal_date) FROM layer4.signals
                WHERE ticker IN ('NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN')
            )
            ORDER BY ndi DESC
        """)
        ranking_rows = cur.fetchall()
        ranking = [
            {'rank': i + 1, 'ticker': r[0], 'ndi': float(r[1]) if r[1] else 0}
            for i, r in enumerate(ranking_rows)
        ]
        
        # ============================================================
        # 9. RESPUESTA
        # ============================================================
        response = {
            'ticker': ticker,
            'ndi': float(ndi) if ndi else 0,
            'statusLabel': regime or 'UNKNOWN',
            'updatedAt': signal_date.isoformat() if signal_date else datetime.now().isoformat(),
            'confidenceScore': float(confidence) if confidence else 50,
            'measuredMetrics': {
                'sentiment': float(sentiment) if sentiment else 0,
                'momentum': float(momentum) if momentum else 0,
                'divergence': float(ndi) if ndi else 0,
                'sourcesCount': sources_count,
            },
            'narrativeBreakdown': {
                'consensusPercentage': consensus_pct,
                'consensusLabel': 'Alto' if consensus_pct > 70 else 'Moderado' if consensus_pct > 50 else 'Bajo',
                'intensityPercentage': intensity_pct,
                'intensityLabel': 'Alta' if intensity_pct > 70 else 'Moderada' if intensity_pct > 50 else 'Baja',
                'dispersionValue': round(dispersion, 3),
                'dispersionLabel': 'Alta' if dispersion > 0.8 else 'Moderada' if dispersion > 0.4 else 'Baja',
                'mediaBias': {
                    'centerBizPercentage': 60,
                    'leftPercentage': 20,
                    'rightPercentage': 20,
                }
            },
            'narrativeExhaustion': {
                'status': exhaustion_status,
                'conditionsObservedCount': conditions_met,
                'totalConditionsCount': 3,
                'conditionsDetails': conditions_details,
            },
            'aiInterpretation': f'{ticker}: NDI {ndi:.3f}, Régimen: {regime}. Divergencia entre narrativa y precio.',
            'newsSummary': {
                'items': [
                    {
                        'id': f'news-{i}',
                        'source': row[0] if row else 'Unknown',
                        'stars': 3,
                        'headline': row[1] if row else 'No headline available',
                        'sentimentScore': 0.0,
                    } for i, row in enumerate(news_rows)
                ],
                'positiveCount': 0,
                'negativeCount': 0,
                'averageSentiment': 0.0,
            },
            'relativeContext': {
                'sectorName': 'Technology',
                'comparison': {
                    'tickerSentiment': float(sentiment) if sentiment else 0,
                    'sectorSentiment': 0.45,
                    'sentimentLabel': 'Neutral',
                    'tickerConsensus': consensus_pct,
                    'sectorConsensus': 58,
                    'consensusLabel': f'{consensus_pct - 58:+d}%',
                    'tickerExhaustion': exhaustion_status,
                    'sectorExhaustion': 'MEDIA',
                    'exhaustionLabel': 'Igual',
                },
                'ranking': ranking,
                'insight': f'{ticker}: Divergencia de {ndi:.3f} entre narrativa y precio.',
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            put_connection(conn)

@market_intel_bp.route('/test', methods=['GET'])
def test_endpoint():
    return jsonify({'status': 'ok', 'message': 'Market Intelligence is working!'})
