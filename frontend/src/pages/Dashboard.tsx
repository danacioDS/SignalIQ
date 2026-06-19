/**
 * Dashboard.tsx
 * Layout final del Instrument Cluster - Versión Centrada
 */

import { useState, useEffect } from 'react';
import { C } from '../components/styles';
import { NDIVelocimeter } from '../components/NDIVelocimeter';
import { TickerFocusStrip } from '../components/TickerFocusStrip';
import { NarrativePanel } from '../components/NarrativePanel';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useSignalAnalysis } from '../hooks/useSignalAnalysis';

const sectorColors: Record<string, string> = {
  Technology: '#6c63ff',
  Automotive: '#f59e0b',
  Financial: '#3b82f6',
  Energy: '#10b981',
  Consumer: '#ef4444',
  Healthcare: '#8b5cf6',
  Semiconductors: '#ec4899',
};

export default function Dashboard() {
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedTicker, setSelectedTicker] = useState('NVDA');
  const [priceHistory, setPriceHistory] = useState<any[]>([]);

  const sectorMap: Record<string, string> = {
    NVDA: 'Technology',
    AAPL: 'Technology',
    MSFT: 'Technology',
    GOOGL: 'Technology',
    META: 'Technology',
    AMD: 'Technology',
    AMZN: 'Technology',
    TSLA: 'Automotive',
    JPM: 'Financial',
    BAC: 'Financial',
    GS: 'Financial',
    XOM: 'Energy',
    CVX: 'Energy',
    COP: 'Energy',
    KO: 'Consumer',
    WMT: 'Consumer',
    PG: 'Consumer',
    JNJ: 'Healthcare',
    UNH: 'Healthcare',
    TSM: 'Semiconductors',
    INTC: 'Semiconductors',
  };

  const defaultTickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN', 'JPM', 'KO'];

  useEffect(() => {
    const fetchSignals = async () => {
      try {
        setLoading(true);
        setError('');
        const response = await fetch(
          `https://signaliq-api.onrender.com/api/signals-live?tickers=${defaultTickers.join(',')}`
        );
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        if (data.success && data.signals && data.signals.length > 0) {
          const formatted = data.signals.map((item: any) => {
            const ndi = item.ndi || 0;
            const sentiment = ndi * 0.6 + 0.2;
            const momentum = ndi * 0.4;
            
            return {
              ticker: item.ticker,
              ndi: ndi,
              sentiment: sentiment,
              momentum: momentum,
              price: item.current_price || 0,
              sector: sectorMap[item.ticker] || 'Other',
              confidence: item.confidence || 70,
            };
          });
          setSignals(formatted);
          if (formatted.length > 0) {
            setSelectedTicker(formatted[0].ticker);
          }
        } else {
          setError('No data available from the API.');
          setSignals([]);
        }
      } catch (err) {
        console.error('Error fetching signals:', err);
        setError('⚠️ Could not load market data.');
        setSignals([]);
      } finally {
        setLoading(false);
      }
    };

    fetchSignals();
    const interval = setInterval(fetchSignals, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchPriceHistory = async () => {
      if (!selectedTicker) return;
      try {
        const response = await fetch(
          `https://signaliq-api.onrender.com/api/prices/${selectedTicker}`
        );
        if (response.ok) {
          const data = await response.json();
          if (data.price_history && data.price_history.length > 0) {
            setPriceHistory(data.price_history);
          }
        }
      } catch (err) {
        console.error('Error fetching price history:', err);
      }
    };

    fetchPriceHistory();
  }, [selectedTicker]);

  const sectorAverages = signals.reduce((acc, s) => {
    if (!acc[s.sector]) acc[s.sector] = { total: 0, count: 0 };
    acc[s.sector].total += s.ndi;
    acc[s.sector].count += 1;
    return acc;
  }, {} as Record<string, { total: number; count: number }>);

  const sectorPerformance = Object.keys(sectorAverages).map((sector) => ({
    sector,
    avgNDI: sectorAverages[sector].total / sectorAverages[sector].count,
    color: sectorColors[sector] || C.muted,
  }));

  const selectedSignal = signals.find((s) => s.ticker === selectedTicker);
  const tickerList = signals.map((s) => s.ticker);
  const ndiMap = Object.fromEntries(signals.map((s) => [s.ticker, s.ndi]));

  const getFallbackSignal = () => {
    if (signals.length > 0) {
      return signals[0];
    }
    return {
      ticker: 'NVDA',
      ndi: 0,
      sentiment: 0,
      momentum: 0,
      price: 0,
      sector: 'Unknown',
      confidence: 0,
    };
  };

  const signalInput = selectedSignal || getFallbackSignal();
  const analysis = useSignalAnalysis(signalInput);

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '60vh',
          color: C.muted,
        }}
      >
        Loading market data...
      </div>
    );
  }

  const displayTicker = signalInput.ticker;
  const displaySentiment = signalInput.sentiment;
  const displayMomentum = signalInput.momentum;
  const displayPrice = signalInput.price;

  // Detectar si es móvil
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 600;

  return (
    <div style={{ 
      padding: isMobile ? '10px 10px' : '20px 32px', 
      maxWidth: 900, 
      margin: '0 auto',
      width: '100%',
      boxSizing: 'border-box',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
    }}>
      {/* Header centrado */}
      <div style={{ 
        marginBottom: 8, 
        textAlign: 'center',
        width: '100%',
      }}>
        <h1 style={{ 
          fontSize: isMobile ? 18 : 22, 
          fontWeight: 700, 
          margin: 0, 
          color: C.text 
        }}>
          📊 SignalIQ
        </h1>
        <p style={{ 
          fontSize: isMobile ? 10 : 12, 
          color: C.muted, 
          margin: '2px 0 0' 
        }}>
          NDI = Sentiment − Momentum • {signals.length} tickers live
        </p>
      </div>

      {/* Price Evolution */}
      <div
        style={{
          background: C.card,
          border: `1px solid ${C.cardBorder}`,
          borderRadius: 12,
          padding: isMobile ? 10 : 16,
          marginBottom: 12,
          width: '100%',
          maxWidth: 800,
        }}
      >
        <h3 style={{ 
          fontSize: isMobile ? 11 : 13, 
          fontWeight: 600, 
          margin: '0 0 8px 0', 
          color: C.text 
        }}>
          📈 Price Evolution {selectedTicker ? `(${selectedTicker})` : ''}
        </h3>
        {priceHistory.length > 0 ? (
          <ResponsiveContainer width="100%" height={isMobile ? 120 : 180}>
            <AreaChart data={priceHistory}>
              <defs>
                <linearGradient id="gPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={C.accent} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={C.accent} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
              <XAxis 
                dataKey="date" 
                tick={{ fill: C.muted, fontSize: isMobile ? 7 : 9 }} 
                axisLine={false} 
                tickLine={false} 
              />
              <YAxis 
                tick={{ fill: C.muted, fontSize: isMobile ? 7 : 9 }} 
                axisLine={false} 
                tickLine={false} 
                domain={['auto', 'auto']} 
              />
              <Tooltip contentStyle={{ background: C.sidebar, border: `1px solid ${C.cardBorder}`, borderRadius: 8 }} />
              <Area type="monotone" dataKey="close" name="Price" stroke={C.accent} strokeWidth={2} fill="url(#gPrice)" />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ textAlign: 'center', padding: '12px 0', color: C.muted }}>
            No price data available
          </div>
        )}
      </div>

      {/* Ticker Selector - centrado */}
      <div style={{ width: '100%', maxWidth: 800 }}>
        <TickerFocusStrip
          tickers={tickerList}
          selectedTicker={selectedTicker}
          onSelect={setSelectedTicker}
          ndiMap={ndiMap}
        />
      </div>

      {error && (
        <div style={{ background: C.redBg, borderRadius: 8, padding: 8, marginTop: 8, width: '100%', maxWidth: 800 }}>
          <p style={{ fontSize: 11, color: C.red, margin: 0 }}>{error}</p>
        </div>
      )}

      {/* Velocímetro - centrado con contenedor */}
      <div style={{ 
        marginTop: 10,
        marginBottom: 6,
        display: 'flex', 
        justifyContent: 'center',
        alignItems: 'center',
        width: '100%',
        maxWidth: 800,
      }}>
        <NDIVelocimeter 
          ndi={analysis.ndi} 
          size={isMobile ? 280 : 380} 
        />
      </div>

      {/* Narrative Panel */}
      <div style={{ width: '100%', maxWidth: 800 }}>
        <NarrativePanel
          ticker={displayTicker}
          ndi={analysis.ndi}
          regime={analysis.regime}
          sentiment={displaySentiment}
          momentum={displayMomentum}
          price={displayPrice}
          explanation={analysis.explanation}
        />
      </div>

      {/* Sector Performance */}
      <div
        style={{
          background: C.card,
          border: `1px solid ${C.cardBorder}`,
          borderRadius: 12,
          padding: isMobile ? 12 : 16,
          marginTop: 12,
          width: '100%',
          maxWidth: 800,
        }}
      >
        <h3 style={{ 
          fontSize: isMobile ? 11 : 13, 
          fontWeight: 600, 
          margin: '0 0 10px 0', 
          color: C.text 
        }}>
          📊 Sector Performance (Avg NDI)
        </h3>
        {sectorPerformance.map((s) => (
          <div
            key={s.sector}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: isMobile ? 6 : 10,
              marginBottom: isMobile ? 3 : 5,
            }}
          >
            <span style={{ 
              width: isMobile ? 65 : 90, 
              fontSize: isMobile ? 9 : 11, 
              color: C.muted 
            }}>
              {s.sector}
            </span>
            <div
              style={{
                flex: 1,
                height: isMobile ? 4 : 6,
                background: C.bg,
                borderRadius: 4,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${Math.min((s.avgNDI + 1) / 2.5 * 100, 100)}%`,
                  height: '100%',
                  background: s.color,
                  borderRadius: 4,
                  transition: 'width 0.6s ease',
                }}
              />
            </div>
            <span style={{ 
              width: 30, 
              fontSize: isMobile ? 9 : 11, 
              color: C.text, 
              textAlign: 'right' 
            }}>
              {s.avgNDI.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}