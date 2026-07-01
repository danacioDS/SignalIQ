#!/usr/bin/env python3

# Leer el archivo original
with open('app/main.py', 'r') as f:
    content = f.read()

# Buscar la función api_analyze
start_marker = '@app.route("/api/analyze/<ticker>")'
end_marker = 'def api_stats():'

# Encontrar la función actual
start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx == -1 or end_idx == -1:
    print("❌ No se encontró la función api_analyze")
    exit(1)

# Nueva función (simplificada para usar Groq)
new_function = '''@app.route("/api/analyze/<ticker>")
@limiter.limit("10 per minute")
def api_analyze(ticker):
    err = _validate_ticker(ticker)
    if err:
        return jsonify({"error": err}), 400

    ticker = ticker.strip().upper()
    
    # Obtener datos de la base de datos
    conn = None
    ndi = get_consistent_ndi(ticker)
    sentiment = None
    momentum = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT ndi, sentiment_zscore, momentum_zscore 
            FROM layer4.signals 
            WHERE ticker = %s 
            ORDER BY signal_date DESC 
            LIMIT 1
        """, (ticker,))
        row = cur.fetchone()
        if row:
            ndi = float(row[0])
            sentiment = float(row[1]) if row[1] else None
            momentum = float(row[2]) if row[2] else None
    except Exception as e:
        log_error(f"DB error for {ticker}: {e}")
    finally:
        if conn:
            put_connection(conn)
    
    # Usar Groq para análisis
    try:
        analysis = llm_service.analyze_ticker(ticker, ndi, sentiment, momentum)
        provider = "groq"
    except Exception as e:
        log_error(f"Groq error for {ticker}: {e}")
        if model:
            try:
                response = model.generate_content(f"Analyze {ticker} stock. Give BUY/SELL/HOLD.")
                analysis = response.text
                provider = "gemini"
            except Exception as e2:
                log_error(f"Gemini error: {e2}")
                analysis = f"NDI: {ndi:.3f}. Market in {regime} regime."
                provider = "none"
        else:
            analysis = f"NDI: {ndi:.3f}."
            provider = "none"
    
    if ndi > 1.5:
        regime = "Overheating"
        regime_color = "red"
    elif ndi > 0.7:
        regime = "Watching"
        regime_color = "yellow"
    elif ndi > 0.3:
        regime = "Accumulation"
        regime_color = "blue"
    else:
        regime = "Aligned"
        regime_color = "green"
    
    recommendation = "HOLD"
    if analysis:
        upper = analysis.upper()
        if "BUY" in upper and "SELL" not in upper:
            recommendation = "BUY"
        elif "SELL" in upper and "BUY" not in upper:
            recommendation = "SELL"
    
    return jsonify({
        "success": True,
        "ticker": ticker,
        "ndi": round(ndi, 3) if ndi else None,
        "regime": regime,
        "regime_color": regime_color,
        "sentiment": round(sentiment, 2) if sentiment else None,
        "momentum": round(momentum, 2) if momentum else None,
        "recommendation": recommendation,
        "analysis": analysis,
        "provider": provider,
        "timestamp": datetime.now().isoformat()
    })

'''

# Reemplazar la función
new_content = content[:start_idx] + new_function + content[end_idx:]

# Guardar
with open('app/main.py', 'w') as f:
    f.write(new_content)

print("✅ Función api_analyze actualizada para usar Groq")
