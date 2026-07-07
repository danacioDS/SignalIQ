import React from 'react';

interface SectorComparisonProps {
  sectorName: string;
  comparison: {
    tickerSentiment: number;
    sectorSentiment: number;
    sentimentDifference: number;
    sentimentLabel: string;
    tickerConsensus: number;
    sectorConsensus: number;
    consensusDifference: number;
    consensusLabel: string;
    tickerExhaustion: string;
    sectorExhaustion: string;
    exhaustionLabel: string;
  };
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    padding: '16px 20px',
    background: '#1e293b',
    borderRadius: 10,
    border: '1px solid #334155',
    marginBottom: 16,
  },
  title: {
    fontSize: 14,
    fontWeight: 600,
    color: '#e2e8f0',
    display: 'block',
    marginBottom: 12,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: 12,
  },
  comparisonItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  comparisonLabel: {
    fontSize: 11,
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  comparisonRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  comparisonValue: {
    fontSize: 16,
    fontWeight: 600,
    color: '#e2e8f0',
  },
  comparisonDiff: {
    fontSize: 13,
    fontWeight: 600,
  },
};

export const SectorComparison: React.FC<SectorComparisonProps> = ({
  sectorName,
  comparison,
}) => {
  const items = [
    {
      label: 'Sentiment',
      value: comparison.tickerSentiment.toFixed(3),
      diff: comparison.sentimentDifference.toFixed(2),
      labelText: comparison.sentimentLabel,
    },
    {
      label: 'Consensus',
      value: `${comparison.tickerConsensus}%`,
      diff: `${comparison.consensusDifference > 0 ? '+' : ''}${comparison.consensusDifference}%`,
      labelText: comparison.consensusLabel,
    },
    {
      label: 'Exhaustion',
      value: comparison.tickerExhaustion,
      diff: comparison.exhaustionLabel,
      labelText: '',
    },
  ];

  return (
    <div style={styles.container}>
      <span style={styles.title}>📊 vs Sector ({sectorName})</span>
      <div style={styles.grid}>
        {items.map((item) => (
          <div key={item.label} style={styles.comparisonItem}>
            <span style={styles.comparisonLabel}>{item.label}</span>
            <div style={styles.comparisonRow}>
              <span style={styles.comparisonValue}>{item.value}</span>
              <span style={styles.comparisonDiff}>
                {item.diff} {item.labelText}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SectorComparison;
