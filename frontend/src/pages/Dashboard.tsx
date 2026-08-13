import { getCompanyName } from "../constants/companyNames";
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { C } from '../components/styles';
import { NDIGauge } from '../components/NDIGauge';
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
import { API_BASE, API_ENDPOINTS, DEFAULT_TICKERS } from '../config/api';
const REFRESH_INTERVAL = 5 * 60 * 1000;

// ✅ Headers para autenticación
const getHeaders = () => ({
  'Content-Type': 'application/json',
});

const api = {
  signals: (tickers: string[]) => 
    `${API_BASE}/api/signals-live?tickers=${tickers.join(',')}`,
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
  AMZN: 'Consumer',
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

// ==================== COMPONENTE NDI FRAMEWORK ====================
const NDIFrameworkTable: React.FC<{ ndi: number; regime: string }> = ({ ndi, regime }) => {
  // Definición de colores por régimen (coincide con NDIGauge y Dashboard)
  const regimeColors: Record<string, string> = {
    extreme_overheating: '#ef4444',
    overheating: '#f97316',
    watching: '#eab308',
    stable: '#22c55e',
    aligned: '#3b82f6',
    strong_undervalued: '#7C4DFF',
    extreme_undervalued: '#6b21a8',
  };

  const regimes = [
    { economics: 'Euphoric market, price not rising', ndiRange: 'NDI > 2.0', action: '🔴 SELL', key: 'extreme_overheating' },
    { economics: 'Strong optimism, momentum weakening', ndiRange: '1.5 < NDI ≤ 2.0', action: '🟠 REDUCE', key: 'overheating' },
    { economics: 'Moderate divergence', ndiRange: '0.5 < NDI ≤ 1.5', action: '🟡 MONITOR', key: 'watching' },
    { economics: 'Perfect equilibrium', ndiRange: '-0.5 < NDI ≤ 0.5', action: '🟢 HOLD', key: 'stable' },
    { economics: 'Unjustified pessimism', ndiRange: '-1.5 < NDI ≤ -0.5', action: '🔵 BUY', key: 'aligned' },
    { economics: 'Significant oversold', ndiRange: '-2.0 < NDI ≤ -1.5', action: '🟣 STRONG BUY', key: 'strong_undervalued' },
    { economics: 'Capitulation', ndiRange: 'NDI ≤ -2.0', action: '💎 ACCUMULATE', key: 'extreme_undervalued' },
  ];

  const getRowStyle = (key: string) => {
    let isActive = false;
    if (key === 'extreme_overheating' && ndi > 2.0) isActive = true;
    else if (key === 'overheating' && ndi > 1.5 && ndi <= 2.0) isActive = true;
    else if (key === 'watching' && ndi > 0.5 && ndi <= 1.5) isActive = true;
    else if (key === 'stable' && ndi > -0.5 && ndi <= 0.5) isActive = true;
    else if (key === 'aligned' && ndi > -1.5 && ndi <= -0.5) isActive = true;
    else if (key === 'strong_undervalued' && ndi > -2.0 && ndi <= -1.5) isActive = true;
    else if (key === 'extreme_undervalued' && ndi <= -2.0) isActive = true;
    
    const color = regimeColors[key] || '#888888';
    
    return {
      backgroundColor: isActive ? `${color}20` : 'transparent',
      borderLeft: isActive ? `3px solid ${color}` : '3px solid transparent',
      fontWeight: isActive ? 'bold' : 'normal',
      color: isActive ? color : C.text,
    };
  };

  return (
    <div style={{
      backgroundColor: C.card,
      borderRadius: '12px',
      padding: '16px',
      border: `1px solid ${C.cardBorder}`,
      width: '100%',
    }}>
      <h4 style={{ color: C.text, margin: '0 0 12px 0', fontSize: '14px' }}>
        📊 NDI Framework
      </h4>
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 0.8fr 0.8fr',
        gap: '4px',
        fontSize: '12px',
      }}>
        <div style={{ color: C.muted, fontWeight: 'bold', padding: '4px 8px', borderBottom: `1px solid ${C.cardBorder}` }}>
          Economics
        </div>
        <div style={{ color: C.muted, fontWeight: 'bold', padding: '4px 8px', borderBottom: `1px solid ${C.cardBorder}` }}>
          NDI
        </div>
        <div style={{ color: C.muted, fontWeight: 'bold', padding: '4px 8px', borderBottom: `1px solid ${C.cardBorder}` }}>
          Action
        </div>
        {regimes.map((item) => {
          const style = getRowStyle(item.key);
          return (
            <React.Fragment key={item.key}>
              <div style={{ ...style, padding: '6px 8px' }}>
                {item.economics}
              </div>
              <div style={{ ...style, padding: '6px 8px', fontFamily: 'monospace' }}>
                {item.ndiRange}
              </div>
              <div style={{ ...style, padding: '6px 8px' }}>
                {item.action}
              </div>
            </React.Fragment>
          );
        })}
      </div>
      <div style={{ 
        marginTop: '8px', 
        fontSize: '11px', 
        color: C.muted,
        padding: '4px 8px',
        backgroundColor: C.accentBg,
        borderRadius: '4px',
      }}>
        💡 Current NDI: {ndi.toFixed(3)} - {regime}
      </div>
    </div>
  );
};

// ==================== COMPONENTE PRINCIPAL ====================
export default function Dashboard() {
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [priceHistory, setPriceHistory] = useState<any[]>([]);
  const [isMobile, setIsMobile] = useState(false);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 600);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const fetchSignals = useCallback(async () => {
    try {
      setLoading(true);
      setError('');

      const url = api.signals(defaultTickers);
      console.log('📊 Fetching URL:', url);

      const res = await fetch(url, { headers: getHeaders() });
      console.log('📊 Response status:', res.status);

      if (!res.ok) {
        if (res.status === 401) {
          setError('⚠️ Unauthorized: Invalid API Key. Please check your configuration.');
        }
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      console.log('📊 Data received:', data);

      if (data?.success && Array.isArray(data.signals) && data.signals.length > 0) {
        // ✅ LOS PRECIOS Y price_history YA VIENEN EN data.signals
        console.log('📊 Usando datos de /api/signals-live (una sola llamada)...');

        const formatted = data.signals.map((item: any) => ({
          ticker: item.ticker,
          ndi: item.ndi || 0,
          sentiment: item.sentiment || 0,
          momentum: item.momentum || 0,
          price: item.current_price || item.price || 0,
          sector: sectorMap[item.ticker] || 'Other',
          confidence: item.confidence || 70,
          regime: item.regime || 'No Data',
          companyName: item.companyName || getCompanyName(item.ticker),
          price_history: item.price_history || [], // ⭐ Guardar price_history
          headlines: item.headlines || [],
          news_count: item.news_count || 0,
        }));

        console.log('📊 Datos formateados:', formatted);

        setSignals(formatted);
        
        // ✅ Si hay un ticker seleccionado, actualizar su price_history
        if (selectedTicker) {
          const selectedData = formatted.find((s: any) => s.ticker === selectedTicker);
          if (selectedData?.price_history?.length > 0) {
            const formattedHistory = selectedData.price_history.map((item: any) => ({
              date: item.date,
              close: item.close || item.price || 0
            }));
            setPriceHistory(formattedHistory);
            console.log(`📊 ${selectedTicker} - price_history actualizado: ${formattedHistory.length} puntos`);
          }
        }
        
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

  // ⭐ ACTUALIZAR price_history cuando cambia el ticker seleccionado (usando los datos que ya tenemos)
  useEffect(() => {
    if (!selectedTicker || signals.length === 0) {
      setPriceHistory([]);
      return;
    }

    try {
      const tickerData = signals.find((s: any) => s.ticker === selectedTicker);
      
      if (!tickerData) {
        console.warn(`⚠️ No se encontraron datos para ${selectedTicker}`);
        setPriceHistory([]);
        return;
      }

      const history = tickerData.price_history || [];
      
      if (history.length === 0) {
        console.warn(`⚠️ No hay price_history para ${selectedTicker}`);
        setPriceHistory([]);
        return;
      }

      const formatted = history.map((item: any) => ({
        date: item.date,
        close: item.close || item.price || 0
      }));
      
      setPriceHistory(formatted);
      console.log(`📊 ${selectedTicker} - price_history cargado: ${formatted.length} puntos`);
      
    } catch (error) {
      console.error('Error procesando price_history:', error);
      setPriceHistory([]);
    }
  }, [selectedTicker, signals]);

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
      maxWidth: 1200, 
      margin: '0 auto',
      width: '100%',
      boxSizing: 'border-box',
      backgroundColor: C.bg,
      minHeight: '100vh',
    }}>
      <div style={{ 
        marginBottom: 12, 
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

      {/* ⭐ GRÁFICO DE PRECIOS - AHORA USA price_history DE signals */}
      <div style={{
        background: C.card,
        border: `1px solid ${C.cardBorder}`,
        borderRadius: 12,
        padding: isMobile ? 10 : 16,
        marginBottom: 12,
        width: '100%',
        maxWidth: 1200,
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
                tickFormatter={(value) => `$${value}`}
              />
              <Tooltip 
                contentStyle={{ 
                  background: C.card, 
                  border: `1px solid ${C.cardBorder}`, 
                  borderRadius: 8,
                  color: C.text,
                }} 
                formatter={(value) => [`$${value}`, 'Price']}
              />
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

      <div style={{ width: '100%', maxWidth: 1200, marginBottom: 12 }}>
        <TickerFocusStrip
          tickers={tickerList}
          selectedTicker={selectedTicker || ''}
          onSelect={setSelectedTicker}
          ndiMap={ndiMap}
        />
      </div>

      {error && (
        <div style={{ 
          background: C.redBg, 
          borderRadius: 8, 
          padding: 8, 
          marginTop: 8, 
          width: '100%', 
          maxWidth: 1200 
        }}>
          <p style={{ fontSize: 11, color: C.red, margin: 0 }}>{error}</p>
        </div>
      )}

      <div style={{
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        gap: '20px',
        marginBottom: '16px',
        alignItems: 'flex-start',
        width: '100%',
        maxWidth: 1200,
      }}>
        <div style={{
          flex: '0 0 auto',
          width: isMobile ? '100%' : '320px',
        }}>
          <NDIGauge 
            ndi={analysis.ndi} 
            size={isMobile ? 220 : 260} 
          />
        </div>
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          minWidth: 0,
          width: '100%',
        }}>
          <NDIFrameworkTable 
            ndi={analysis.ndi} 
            regime={analysis.regime} 
          />
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
      </div>

      <div style={{
        background: C.card,
        border: `1px solid ${C.cardBorder}`,
        borderRadius: 12,
        padding: isMobile ? 12 : 16,
        marginTop: 8,
        width: '100%',
        maxWidth: 1200,
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
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
            {sectorPerformance.map((s) => (
              <div
                key={s.sector}
                style={{
                  flex: '1',
                  minWidth: '100px',
                  padding: '10px 14px',
                  background: C.accentBg,
                  borderRadius: 8,
                  textAlign: 'center',
                }}
              >
                <div style={{ color: C.muted, fontSize: isMobile ? 9 : 11 }}>
                  {s.sector}
                </div>
                <div style={{ 
                  color: s.color, 
                  fontSize: isMobile ? 16 : 20, 
                  fontWeight: 'bold' 
                }}>
                  {s.avgNDI.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', color: C.muted, padding: 8 }}>
            No sector data available
          </div>
        )}
      </div>
    </div>
  );
}// Forzar deploy - Thu Aug 13 18:30:29 -04 2026
