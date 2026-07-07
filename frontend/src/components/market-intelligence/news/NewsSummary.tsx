import React from 'react';
import { NewsSummaryData } from '../../../types/market-intelligence';

interface NewsSummaryProps {
  data: NewsSummaryData;
  ticker: string;
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
    fontSize: 12,
    fontWeight: 700,
    color: '#94a3b8',
    letterSpacing: '0.5px',
    display: 'block',
    marginBottom: 12,
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  itemCard: {
    background: '#0f172a',
    border: '1px solid #334155',
    borderRadius: 8,
    padding: '10px 14px',
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  metaRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  source: {
    fontSize: 11,
    fontWeight: 700,
    color: '#6c63ff',
  },
  stars: {
    fontSize: 11,
    color: '#eab308',
    letterSpacing: '1px',
  },
  bodyRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 16,
  },
  headline: {
    fontSize: 13,
    color: '#e2e8f0',
    margin: 0,
    lineHeight: 1.4,
    fontWeight: 500,
  },
  sentimentBadge: {
    fontSize: 11,
    fontWeight: 700,
    padding: '2px 8px',
    borderRadius: 4,
    whiteSpace: 'nowrap',
  },
  summary: {
    marginTop: 12,
    paddingTop: 10,
    borderTop: '1px solid #334155',
    display: 'flex',
    gap: 16,
    fontSize: 12,
    color: '#94a3b8',
  },
  summaryItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 4,
  },
  summaryValue: {
    fontWeight: 600,
  },
};

const renderStars = (count: number) => {
  return '★'.repeat(count) + '☆'.repeat(5 - count);
};

export const NewsSummary: React.FC<NewsSummaryProps> = ({ data, ticker }) => {
  return (
    <div style={styles.container}>
      <span style={styles.title}>📰 NOTICIAS RELEVANTES ({ticker})</span>

      <div style={styles.list}>
        {data.items.map((item) => {
          const isPositive = item.sentimentScore > 0;

          return (
            <div key={item.id} style={styles.itemCard}>
              <div style={styles.metaRow}>
                <span style={styles.source}>[{item.source}]</span>
                <span style={styles.stars}>{renderStars(item.relevanceStars)}</span>
              </div>
              <div style={styles.bodyRow}>
                <p style={styles.headline}>{item.headline}</p>
                <span
                  style={{
                    ...styles.sentimentBadge,
                    color: isPositive ? '#22c55e' : '#ef4444',
                    background: isPositive
                      ? 'rgba(34, 197, 94, 0.1)'
                      : 'rgba(239, 68, 68, 0.1)',
                  }}
                >
                  {isPositive ? '▲' : '▼'} {isPositive ? '+' : ''}
                  {item.sentimentScore.toFixed(2)}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div style={styles.summary}>
        <span style={styles.summaryItem}>
          📊 <span style={{ color: '#22c55e' }}>{data.positiveCount} positiva</span>
        </span>
        <span style={styles.summaryItem}>
          <span style={{ color: '#ef4444' }}>{data.negativeCount} negativa</span>
        </span>
        <span style={styles.summaryItem}>
          Promedio:{' '}
          <span
            style={{
              ...styles.summaryValue,
              color: data.averageSentiment > 0 ? '#22c55e' : '#ef4444',
            }}
          >
            {data.averageSentiment > 0 ? '+' : ''}
            {data.averageSentiment.toFixed(2)}
          </span>
        </span>
      </div>
    </div>
  );
};

export default NewsSummary;
