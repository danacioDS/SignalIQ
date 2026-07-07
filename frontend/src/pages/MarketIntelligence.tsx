import React, { useState } from 'react';
import { Header } from '../components/market-intelligence/Header';
import { TickerStatus } from '../components/market-intelligence/TickerStatus';
import { TickerSelector } from '../components/market-intelligence/ticker/TickerSelector';
import { QuantitativeSignals } from '../components/market-intelligence/quantitative/QuantitativeSignals';
import { NarrativeBreakdown } from '../components/market-intelligence/quantitative/NarrativeBreakdown';
import { InterpretativeDivider } from '../components/market-intelligence/InterpretativeDivider';
import { NarrativeExhaustion } from '../components/market-intelligence/interpretation/NarrativeExhaustion';
import { AIInterpretation } from '../components/market-intelligence/interpretation/AIInterpretation';
import { NewsSummary } from '../components/market-intelligence/news/NewsSummary';
import { RelativeContext } from '../components/market-intelligence/relative-context/RelativeContext';
import { useTickerAnalysis } from '../hooks/useTickerAnalysis';

const FAVORITE_TICKERS = ['NVDA', 'AAPL', 'MSFT', 'TSLA'];

const styles: { [key: string]: React.CSSProperties } = {
  pageWrapper: {
    padding: '24px 32px',
    maxWidth: 1200,
    margin: '0 auto',
    minHeight: '100vh',
    backgroundColor: '#0f172a',
  },
  loading: {
    textAlign: 'center',
    color: '#94a3b8',
    fontSize: 14,
    marginTop: 40,
    fontFamily: 'monospace',
  },
  error: {
    textAlign: 'center',
    color: '#ef4444',
    fontSize: 14,
    marginTop: 40,
    fontFamily: 'monospace',
  },
};

const MarketIntelligence: React.FC = () => {
  const [selectedTicker, setSelectedTicker] = useState<string>('NVDA');
  const { data, loading, error } = useTickerAnalysis(selectedTicker);

  // Construir mapa de NDI para favoritos
  const ndiMap: Record<string, number> = {};
  // Podríamos obtener de datos previos o de API

  const handleTickerSelect = (ticker: string) => {
    setSelectedTicker(ticker);
  };

  if (loading) {
    return (
      <div style={styles.pageWrapper}>
        <div style={styles.loading}>Cargando análisis para {selectedTicker}...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.pageWrapper}>
        <div style={styles.error}>⚠️ Error: {error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={styles.pageWrapper}>
        <div style={styles.loading}>No hay datos disponibles</div>
      </div>
    );
  }

  return (
    <div style={styles.pageWrapper}>
      <Header updatedAt={data.updatedAt} />

      <TickerSelector
        favorites={FAVORITE_TICKERS}
        selected={selectedTicker}
        onSelect={handleTickerSelect}
        ndiMap={ndiMap}
      />

      <TickerStatus
        ticker={data.ticker}
        ndi={data.ndi}
        statusLabel={data.statusLabel}
        statusColor={data.statusColor}
        updatedAt={data.updatedAt}
      />

      <QuantitativeSignals metrics={data.quantitativeMetrics} />
      <NarrativeBreakdown data={data.narrativeBreakdown} />

      <InterpretativeDivider />

      <NarrativeExhaustion data={data.narrativeExhaustion} />
      <AIInterpretation
        interpretation={data.aiInterpretation}
        disclaimer="⚠️ Interpretación generada por IA. No constituye recomendación de inversión."
      />

      <NewsSummary data={data.newsSummary} ticker={data.ticker} />
      <RelativeContext data={data.relativeContext} />
    </div>
  );
};

export default MarketIntelligence;
