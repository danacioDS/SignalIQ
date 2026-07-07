import React from 'react';

interface TickerStatusProps {
  ticker: string;
  ndi: number;
  statusLabel: string;
  statusColor: 'red' | 'orange' | 'yellow' | 'green' | 'blue';
  updatedAt: string;
}

const statusColors = {
  red: { bg: 'rgba(239, 68, 68, 0.15)', border: '#ef4444', text: '#ef4444' },
  orange: { bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b', text: '#f59e0b' },
  yellow: { bg: 'rgba(234, 179, 8, 0.15)', border: '#eab308', text: '#eab308' },
  green: { bg: 'rgba(34, 197, 94, 0.15)', border: '#22c55e', text: '#22c55e' },
  blue: { bg: 'rgba(59, 130, 246, 0.15)', border: '#3b82f6', text: '#3b82f6' },
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '14px 20px',
    background: '#1e293b',
    borderRadius: 10,
    border: '1px solid #334155',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  left: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  ticker: {
    fontSize: 22,
    fontWeight: 700,
    color: '#e2e8f0',
  },
  badge: {
    fontSize: 13,
    fontWeight: 700,
    padding: '4px 14px',
    borderRadius: 20,
    border: '1px solid',
    letterSpacing: '0.3px',
  },
  right: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  ndiLabel: {
    fontSize: 14,
    fontWeight: 600,
    color: '#94a3b8',
  },
  ndiValue: {
    fontSize: 20,
    fontWeight: 700,
  },
  updatedAt: {
    fontSize: 12,
    color: '#64748b',
    marginLeft: 4,
  },
};

export const TickerStatus: React.FC<TickerStatusProps> = ({
  ticker,
  ndi,
  statusLabel,
  statusColor,
  updatedAt,
}) => {
  const colors = statusColors[statusColor];

  return (
    <div style={styles.container}>
      <div style={styles.left}>
        <span style={styles.ticker}>{ticker}</span>
        <span
          style={{
            ...styles.badge,
            background: colors.bg,
            borderColor: colors.border,
            color: colors.text,
          }}
        >
          {statusLabel}
        </span>
      </div>
      <div style={styles.right}>
        <span style={styles.ndiLabel}>NDI:</span>
        <span style={{ ...styles.ndiValue, color: colors.text }}>
          {ndi.toFixed(3)}
        </span>
        <span style={styles.updatedAt}>• {updatedAt}</span>
      </div>
    </div>
  );
};

export default TickerStatus;
