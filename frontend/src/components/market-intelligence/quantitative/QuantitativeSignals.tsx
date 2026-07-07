import React from 'react';
import { QuantitativeMetrics } from '../../../types/market-intelligence';

interface QuantitativeSignalsProps {
  metrics: QuantitativeMetrics;
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    padding: '16px 20px',
    background: '#1e293b',
    borderRadius: 10,
    border: '1px solid #334155',
    marginBottom: 16,
  },
  sectionHeader: {
    marginBottom: 14,
    paddingBottom: 10,
    borderBottom: '1px solid #334155',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 700,
    color: '#e2e8f0',
    display: 'block',
    letterSpacing: '0.5px',
  },
  sectionSubtitle: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
    display: 'block',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
    gap: 12,
  },
  card: {
    background: '#0f172a',
    borderRadius: 8,
    padding: '10px 14px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  cardLabel: {
    fontSize: 10,
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: '0.8px',
    fontWeight: 600,
  },
  cardValue: {
    fontSize: 20,
    fontWeight: 700,
    marginTop: 2,
  },
};

export const QuantitativeSignals: React.FC<QuantitativeSignalsProps> = ({ metrics }) => {
  const cards = [
    { label: 'SENTIMENT', value: metrics.sentiment },
    { label: 'MOMENTUM', value: metrics.momentum },
    { label: 'DIVERGENCE', value: metrics.divergence },
    { label: 'SOURCES', value: metrics.sourcesCount },
  ];

  const getColor = (label: string, value: number) => {
    if (label === 'SOURCES') return '#e2e8f0';
    if (value > 0) return '#22c55e';
    if (value < 0) return '#ef4444';
    return '#eab308';
  };

  const getPrefix = (label: string, value: number) => {
    if (label === 'SOURCES') return '';
    if (value > 0) return '+';
    return '';
  };

  const getDisplayValue = (label: string, value: number) => {
    if (label === 'SOURCES') return value;
    return value.toFixed(3);
  };

  return (
    <div style={styles.container}>
      <div style={styles.sectionHeader}>
        <span style={styles.sectionTitle}>📊 QUANTITATIVE SIGNALS</span>
        <span style={styles.sectionSubtitle}>
          Datos objetivos calculados directamente de fuentes primarias
        </span>
      </div>

      <div style={styles.grid}>
        {cards.map((card) => (
          <div key={card.label} style={styles.card}>
            <span style={styles.cardLabel}>{card.label}</span>
            <span
              style={{
                ...styles.cardValue,
                color: getColor(card.label, card.value),
              }}
            >
              {getPrefix(card.label, card.value)}
              {getDisplayValue(card.label, card.value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default QuantitativeSignals;
