import React from 'react';

interface SearchResultsProps {
  results: string[];
  loading: boolean;
  onSelect: (ticker: string) => void;
  isVisible: boolean;
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    position: 'absolute',
    top: 4,
    left: 0,
    right: 0,
    background: '#1e293b',
    border: '1px solid #334155',
    borderRadius: 6,
    maxHeight: 200,
    overflowY: 'auto',
    zIndex: 100,
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
  },
  item: {
    padding: '8px 14px',
    cursor: 'pointer',
    fontSize: 13,
    color: '#e2e8f0',
    fontFamily: 'monospace',
    transition: 'background 0.15s',
  },
  itemHover: {
    background: '#334155',
  },
  loadingItem: {
    padding: '8px 14px',
    fontSize: 13,
    color: '#94a3b8',
    textAlign: 'center',
  },
  emptyItem: {
    padding: '8px 14px',
    fontSize: 13,
    color: '#64748b',
    textAlign: 'center',
  },
};

export const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  loading,
  onSelect,
  isVisible,
}) => {
  if (!isVisible) return null;

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingItem}>Buscando...</div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.emptyItem}>No se encontraron resultados</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {results.map((ticker, index) => (
        <div
          key={ticker}
          style={{
            ...styles.item,
            ...(index === results.length - 1 ? { borderBottom: 'none' } : {}),
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#334155';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
          }}
          onClick={() => onSelect(ticker)}
        >
          {ticker}
        </div>
      ))}
    </div>
  );
};

export default SearchResults;
