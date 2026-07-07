import React from 'react';

interface FavoriteTickersProps {
  tickers: string[];
  selected: string;
  onSelect: (ticker: string) => void;
  ndiMap: Record<string, number>;
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: 'flex',
    gap: '6px',
    flexWrap: 'wrap',
  },
  button: {
    padding: '6px 14px',
    borderRadius: 6,
    border: '1px solid #334155',
    background: '#0f172a',
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    fontFamily: 'monospace',
  },
  buttonActive: {
    background: '#6c63ff',
    borderColor: '#6c63ff',
    color: '#fff',
    boxShadow: '0 2px 8px rgba(108, 99, 255, 0.3)',
  },
  ndiBadge: {
    fontSize: 10,
    color: '#64748b',
    marginLeft: 4,
  },
};

export const FavoriteTickers: React.FC<FavoriteTickersProps> = ({
  tickers,
  selected,
  onSelect,
  ndiMap,
}) => {
  return (
    <div style={styles.container}>
      {tickers.map((ticker) => (
        <button
          key={ticker}
          onClick={() => onSelect(ticker)}
          style={{
            ...styles.button,
            ...(selected === ticker ? styles.buttonActive : {}),
          }}
        >
          {ticker}
          {ndiMap[ticker] !== undefined && (
            <span style={styles.ndiBadge}>
              ({ndiMap[ticker].toFixed(2)})
            </span>
          )}
        </button>
      ))}
    </div>
  );
};

export default FavoriteTickers;
