import React from 'react';
import { SectorRankingItem } from '../../../types/market-intelligence';

interface SectorRankingProps {
  ranking: SectorRankingItem[];
  sectorName: string;
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
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  item: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '4px 8px',
    borderRadius: 4,
    background: '#0f172a',
  },
  rank: {
    fontSize: 12,
    fontWeight: 600,
    color: '#64748b',
    width: 24,
  },
  ticker: {
    fontSize: 14,
    fontWeight: 600,
    color: '#e2e8f0',
    width: 50,
  },
  company: {
    fontSize: 12,
    color: '#94a3b8',
    flex: 1,
  },
  barContainer: {
    flex: 1,
    height: 6,
    background: '#1e293b',
    borderRadius: 3,
    overflow: 'hidden',
    minWidth: 100,
  },
  barFill: {
    height: '100%',
    borderRadius: 3,
    transition: 'width 0.4s ease-out',
  },
  ndiValue: {
    fontSize: 13,
    fontWeight: 600,
    color: '#e2e8f0',
    width: 60,
    textAlign: 'right',
  },
  regimeBadge: {
    fontSize: 10,
    fontWeight: 600,
    padding: '2px 8px',
    borderRadius: 4,
    whiteSpace: 'nowrap',
  },
};

const regimeColors: Record<string, string> = {
  SELL: '#ef4444',
  REDUCE: '#f59e0b',
  MONITOR: '#eab308',
  HOLD: '#22c55e',
  BUY: '#22c55e',
  STRONG_BUY: '#16a34a',
  ACCUMULATE: '#15803d',
};

export const SectorRanking: React.FC<SectorRankingProps> = ({
  ranking,
  sectorName,
}) => {
  const maxNdi = Math.max(...ranking.map((r) => r.ndi), 0.001);

  return (
    <div style={styles.container}>
      <span style={styles.title}>📈 Ranking del Sector ({sectorName})</span>
      <div style={styles.list}>
        {ranking.map((item) => {
          const percentage = ((item.ndi - 0) / (maxNdi - 0)) * 100;
          const color = regimeColors[item.regimeLabel] || '#6c63ff';

          return (
            <div key={item.ticker} style={styles.item}>
              <span style={styles.rank}>#{item.rank}</span>
              <span style={styles.ticker}>{item.ticker}</span>
              <span style={styles.company}>{item.companyName}</span>
              <div style={styles.barContainer}>
                <div
                  style={{
                    ...styles.barFill,
                    width: `${Math.min(percentage, 100)}%`,
                    background: color,
                  }}
                />
              </div>
              <span style={styles.ndiValue}>{item.ndi.toFixed(3)}</span>
              <span
                style={{
                  ...styles.regimeBadge,
                  background: `${color}20`,
                  color,
                }}
              >
                {item.regimeLabel}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SectorRanking;
