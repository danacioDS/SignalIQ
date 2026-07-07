import React from 'react';
import FavoriteTickers from './FavoriteTickers';
import TickerSearch from './TickerSearch';

interface TickerSelectorProps {
  favorites: string[];
  selected: string;
  onSelect: (ticker: string) => void;
  ndiMap: Record<string, number>;
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: 'flex',
    gap: 12,
    padding: '8px 12px',
    background: '#1e293b',
    borderRadius: 8,
    border: '1px solid #334155',
    marginBottom: 16,
    flexWrap: 'wrap',
    alignItems: 'center',
  },
  label: {
    fontSize: 11,
    fontWeight: 600,
    color: '#64748b',
    letterSpacing: '0.5px',
    marginRight: 4,
  },
};

export const TickerSelector: React.FC<TickerSelectorProps> = ({
  favorites,
  selected,
  onSelect,
  ndiMap,
}) => {
  return (
    <div style={styles.container}>
      <span style={styles.label}>Favoritos:</span>
      <FavoriteTickers
        tickers={favorites}
        selected={selected}
        onSelect={onSelect}
        ndiMap={ndiMap}
      />
      <TickerSearch
        onSelect={onSelect}
        excludedTickers={favorites}
      />
    </div>
  );
};

export default TickerSelector;
