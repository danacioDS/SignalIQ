/**
 * Market Intelligence - Hook para análisis de tickers
 */

import { useState, useEffect, useCallback } from 'react';
import { fetchTickerAnalysis } from '../api/market-intelligence';
import { TickerAnalysisResponse } from '../types/market-intelligence';

export const useTickerAnalysis = (ticker: string) => {
  const [data, setData] = useState<TickerAnalysisResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!ticker) {
      setData(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await fetchTickerAnalysis(ticker);
      setData(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al cargar los datos';
      setError(message);
      console.error('Error fetching ticker analysis:', err);
    } finally {
      setLoading(false);
    }
  }, [ticker]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { 
    data, 
    loading, 
    error, 
    refetch: fetchData 
  };
};
