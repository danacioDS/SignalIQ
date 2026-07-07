import React, { useState, useCallback } from 'react';
import { searchTickers } from '../../../api/market-intelligence';
import SearchResults from './SearchResults';

interface TickerSearchProps {
  onSelect: (ticker: string) => void;
  excludedTickers?: string[];
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    flex: 1,
    minWidth: 200,
  },
  input: {
    width: '100%',
    padding: '8px 14px',
    borderRadius: 6,
    border: '1px solid #334155',
    background: '#0f172a',
    color: '#e2e8f0',
    fontSize: 13,
    outline: 'none',
    fontFamily: 'monospace',
    transition: 'border-color 0.2s',
  },
  inputFocus: {
    borderColor: '#6c63ff',
  },
  resultsContainer: {
    position: 'relative',
  },
};

export const TickerSearch: React.FC<TickerSearchProps> = ({
  onSelect,
  excludedTickers = [],
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<string[]>([]);
  const [isFocused, setIsFocused] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSearch = useCallback(async (value: string) => {
    setQuery(value);
    if (value.length < 1) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const searchResults = await searchTickers(value);
      const filtered = searchResults.filter(
        (t) => !excludedTickers.includes(t)
      );
      setResults(filtered);
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [excludedTickers]);

  const handleSelect = (ticker: string) => {
    setQuery('');
    setResults([]);
    onSelect(ticker);
  };

  return (
    <div style={styles.container}>
      <input
        style={{
          ...styles.input,
          ...(isFocused ? styles.inputFocus : {}),
        }}
        type="text"
        placeholder="🔍 Buscar ticker..."
        value={query}
        onChange={(e) => handleSearch(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setTimeout(() => setIsFocused(false), 200)}
      />
      <div style={styles.resultsContainer}>
        <SearchResults
          results={results}
          loading={loading}
          onSelect={handleSelect}
          isVisible={isFocused && results.length > 0}
        />
      </div>
    </div>
  );
};

export default TickerSearch;
