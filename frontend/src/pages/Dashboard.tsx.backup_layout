/**
 * Dashboard.tsx
 * SignalIQ - Instrument Cluster Dashboard (Production Ready v2)
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { C } from '../components/styles';
import { NDIVelocimeter } from '../components/NDIVelocimeter';
import { TickerFocusStrip } from '../components/TickerFocusStrip';
import NarrativePanel from '../components/NarrativePanel';
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

// ==================== CONFIGURACIÓN ====================
// ✅ URL CORRECTA PARA PRODUCCIÓN
const API_BASE = 'https://signaliq-api.onrender.com';
const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutos

const api = {
  signals: (tickers: string[]) => 
    `${API_BASE}/api/signals-live?tickers=${tickers.join(',')}`,
  prices: (ticker: string) => 
    `${API_BASE}/api/prices/${ticker}`,
};

// ==================== CONSTANTES ====================
const sectorColors: Record<string, string> = {
  Technology: '#6c63ff',
  Automotive: '#f59e0b',
  Financial: '#3b82f6',
  Energy: '#10b981',
  Consumer: '#ef4444',
  Healthcare: '#8b5cf6',
  Semiconductors: '#ec4899',
};

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

const defaultTickers = [
  'NVDA','AAPL','MSFT','TSLA','GOOGL',
  'META','AMD','AMZN','JPM','KO'
];

// ==================== COMPONENTE PRINCIPAL ====================
export default function Dashboard() {
  // Estado
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [priceHistory, setPriceHistory] = useState<any[]>([]);
  const [isMobile, setIsMobile] = useState(false);
  
  // Refs para evitar re-renders innecesarios
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // ==================== DETECCIÓN DE MÓVIL ====================
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 600);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // ==================== FETCH SIGNALS (SIN DEPENDENCIAS) ====================
  const fetchSignals = useCallback(async () => {
    try {
      setLoading(true);
      setError('');

      const res = await fetch(api.signals(defaultTickers));

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();

      if (data?.success && Array.isArray(data.signals) && data.signals.length > 0) {
        const formatted = data.signals.map((item: any) => {
          const ndi = item.ndi || 0;
          return {
            ticker: item.ticker,
            ndi,
            sentiment: ndi * 0.6 + 0.2,
            momentum: ndi * 0.4,
            price: item.current_price || 0,
            sector: sectorMap[item.ticker] || 'Other',
            confidence: item.confidence || 70,
          };
        });

        setSignals(formatted);
        
        // Solo setear ticker si no hay uno seleccionado
        if (formatted.length > 0 && !selectedTicker) {
          setSelectedTicker(formatted[0].ticker);
        }
      } else {
        setSignals([]);
        setError('No data available from the API.');
      }
    } catch (err) {
      console.error('Error fetching signals:', err);
      setError('⚠️ Could not load market data.');
      setSignals([]);
    } finally {
      setLoading(false);
    }
  }, [selectedTicker]);

  // ==================== SETUP SIGNALS (SOLO UNA VEZ) ====================
  useEffect(() => {
    fetchSignals();

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    intervalRef.current = setInterval(fetchSignals, REFRESH_INTERVAL);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [fetchSignals]);

  // ==================== FETCH PRICE HISTORY ====================
  useEffect(() => {
    const fetchPriceHistory = async () => {
      if (!selectedTicker) return;

      try {
        const res = await fetch(api.prices(selectedTicker));
        if (!res.ok) return;
        const data = await res.json();
        if (data?.price_history?.length) {
          setPriceHistory(data.price_history);
        }
      } catch (err) {
        console.error('Error fetching price history:', err);
      }
    };

    fetchPriceHistory();
  }, [selectedTicker]);

  // ==================== CÁLCULOS ====================
  const sectorAverages = signals.reduce((acc: any, s) => {
    if (!acc[s.sector]) acc[s.sector] = { total: 0, count: 0 };
    acc[s.sector].total += s.ndi;
    acc[s.sector].count += 1;
    return acc;
  }, {});

  const sectorPerformance = Object.keys(sectorAverages).map((sector) => ({
    sector,
    avgNDI: sectorAverages[sector].count > 0
      ? sectorAverages[sector].total / sectorAverages[sector].count
      : 0,
    color: sectorColors[sector] || C.muted,
  }));

  const selectedSignal = signals.find((s) => s.ticker === selectedTicker);
  const signal = selectedSignal || signals[0] || {
    ticker: 'NVDA',
    ndi: 0,
    sentiment: 0,
    momentum: 0,
    price: 0,
    sector: 'Unknown',
    confidence: 0,
  };

  const analysis = useSignalAnalysis(signal);
  const tickerList = signals.map(s => s.ticker);
  const ndiMap = Object.fromEntries(signals.map(s => [s.ticker, s.ndi]));

  // ==================== RENDER ====================
  if (loading && signals.length === 0) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '60vh',
        color: C.muted,
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 24, marginBottom: 8 }}>📊</div>
          Loading market data...
        </div>
      </div>
    );
  }

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
      {/* HEADER */}
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
          {selectedTicker && ` • ${selectedTicker}`}
        </p>
      </div>

      {/* PRICE CHART */}
      <div style={{
        background: C.card,
        border: `1px solid ${C.cardBorder}`,
        borderRadius: 12,
        padding: isMobile ? 10 : 16,
        marginBottom: 12,
        width: '100%',
        maxWidth: 800,
      }}>
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
              <Tooltip contentStyle={{ 
                background: C.sidebar, 
                border: `1px solid ${C.cardBorder}`, 
                borderRadius: 8 
              }} />
              <Area 
                type="monotone" 
                dataKey="close" 
                name="Price" 
                stroke={C.accent} 
                strokeWidth={2} 
                fill="url(#gPrice)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ textAlign: 'center', padding: '12px 0', color: C.muted }}>
            {loading ? 'Loading price data...' : 'No price data available'}
          </div>
        )}
      </div>

      {/* TICKER SELECTOR */}
      <div style={{ width: '100%', maxWidth: 800 }}>
        <TickerFocusStrip
          tickers={tickerList}
          selectedTicker={selectedTicker || ''}
          onSelect={setSelectedTicker}
          ndiMap={ndiMap}
        />
      </div>

      {/* ERROR */}
      {error && (
        <div style={{ 
          background: C.redBg, 
          borderRadius: 8, 
          padding: 8, 
          marginTop: 8, 
          width: '100%', 
          maxWidth: 800 
        }}>
          <p style={{ fontSize: 11, color: C.red, margin: 0 }}>{error}</p>
        </div>
      )}

      {/* GAUGE */}
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

      {/* NARRATIVE */}
      <div style={{ width: '100%', maxWidth: 800 }}>
        <NarrativePanel
          ticker={signal.ticker}
          ndi={analysis.ndi}
          regime={analysis.regime}
          sentiment={signal.sentiment}
          momentum={signal.momentum}
          price={signal.price}
          explanation={analysis.explanation}
        />
      </div>

      {/* SECTOR PERFORMANCE */}
      <div style={{
        background: C.card,
        border: `1px solid ${C.cardBorder}`,
        borderRadius: 12,
        padding: isMobile ? 12 : 16,
        marginTop: 12,
        width: '100%',
        maxWidth: 800,
      }}>
        <h3 style={{ 
          fontSize: isMobile ? 11 : 13, 
          fontWeight: 600, 
          margin: '0 0 10px 0', 
          color: C.text 
        }}>
          📊 Sector Performance (Avg NDI)
        </h3>
        {sectorPerformance.length > 0 ? (
          sectorPerformance.map((s) => (
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
              <div style={{
                flex: 1,
                height: isMobile ? 4 : 6,
                background: C.bg,
                borderRadius: 4,
                overflow: 'hidden',
              }}>
                <div style={{
                  width: `${Math.min((s.avgNDI + 1) / 2.5 * 100, 100)}%`,
                  height: '100%',
                  background: s.color,
                  borderRadius: 4,
                  transition: 'width 0.6s ease',
                }} />
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
          ))
        ) : (
          <div style={{ textAlign: 'center', color: C.muted, padding: 8 }}>
            No sector data available
          </div>
        )}
      </div>
    </div>
  );
}