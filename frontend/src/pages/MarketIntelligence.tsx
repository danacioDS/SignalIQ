import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config/api';
import { MarketIntelligenceTable } from '../components/MarketIntelligenceTable';
import { NewsPanel } from '../components/NewsPanel';

interface TickerData {
  ticker: string;
  price: number;
  sentiment: number;
  momentum: number;
  ndi: number;
  regime: string;
  confidence: number;
  headlines?: string[];
  news_count?: number;
}

interface AnalysisResponse {
  sentiment: string;
  momentum: string;
  regime: string;
  interpretation: string;
  risk_outlook: string;
}

interface MetricsData {
  ndi_mean: number;
  ndi_std: number;
  ndi_range: number;
  sentiment_ndi_corr: number;
  momentum_ndi_corr: number;
  confidence_mean: number;
  regime_counts: Record<string, number>;
  market_alignment: number;
}

interface MetricsResponse {
  generated_at: string;
  source: string;
  tickers: TickerData[];
  metrics: MetricsData;
}

interface TickerNewsResponse {
  ticker: string;
  headlines: string[];
  news_count: number;
}

const MarketIntelligence: React.FC = () => {
  const [data, setData] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTicker, setSelectedTicker] = useState<string>('');
  const [newsData, setNewsData] = useState<Record<string, TickerNewsResponse>>({});
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  useEffect(() => {
    fetchMetrics();
  }, []);

  useEffect(() => {
    if (selectedTicker) {
      fetchNews(selectedTicker);
    }
  }, [selectedTicker]);

  useEffect(() => {
    if (selectedTicker && newsData[selectedTicker]) {
      fetchAnalysis(selectedTicker);
    }
  }, [selectedTicker, newsData]);

  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/metrics`);
      if (!response.ok) throw new Error('Failed to fetch metrics');
      const result = await response.json();
      setData(result);

      if (result.tickers && result.tickers.length > 0) {
        const top5 = [...result.tickers]
          .sort((a, b) => b.sentiment - a.sentiment)
          
        if (top5.length > 0) {
          setSelectedTicker(top5[0].ticker);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const fetchNews = async (ticker: string) => {
    if (newsData[ticker]) return;

    try {
      const response = await fetch(`${API_BASE}/api/ticker/${ticker}`);
      if (!response.ok) throw new Error('Failed to fetch news');
      const result = await response.json();
      setNewsData((prev) => ({
        ...prev,
        [ticker]: {
          ticker: result.ticker || ticker,
          headlines: result.headlines || [],
          news_count: result.news_count || 0,
        },
      }));
    } catch (err) {
      console.error(`Error fetching news for ${ticker}:`, err);
    }
  };

  const fetchAnalysis = async (ticker: string) => {
    const selectedData = data?.tickers?.find((t) => t.ticker === ticker);
    if (!selectedData) return;

    setAnalysisLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/market-intelligence/analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: ticker,
          sentiment: selectedData.sentiment || 0,
          momentum: selectedData.momentum || 0,
          ndi: selectedData.ndi || 0,
          regime: selectedData.regime || 'UNKNOWN',
          news: newsData[ticker]?.headlines || [],
        }),
      });
      if (!response.ok) throw new Error('Failed to fetch analysis');
      const result = await response.json();
      setAnalysis(result.analysis);
    } catch (err) {
      console.error(`Error fetching analysis for ${ticker}:`, err);
      setAnalysis(null);
    } finally {
      setAnalysisLoading(false);
    }
  };

  if (loading) return <div className="text-white p-8">Loading market intelligence...</div>;
  if (error) return <div className="text-red-500 p-8">Error: {error}</div>;
  if (!data) return null;

  const { tickers } = data;

  const top5Tickers = [...tickers]
    .sort((a, b) => b.sentiment - a.sentiment)
    

  const selectedNews = selectedTicker ? newsData[selectedTicker] : null;
  const selectedData = tickers.find((t) => t.ticker === selectedTicker);

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">🧠 Market Intelligence</h1>
          <p className="text-gray-400">Advanced NDI market analytics</p>
        </div>
        <div className="text-right">
          <p className="text-gray-400 text-sm">
            Updated: {new Date(data.generated_at).toLocaleTimeString()}
          </p>
          <p className="text-gray-500 text-sm">Source: {data.source}</p>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 mb-6">
        <h3 className="text-white text-lg font-semibold mb-4">
          📊 Ticker Intelligence (All Tickers (by Sentiment))
        </h3>
        <MarketIntelligenceTable
          tickers={top5Tickers}
          onSelectTicker={setSelectedTicker}
          selectedTicker={selectedTicker}
        />
      </div>

      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-white text-lg font-semibold">📰 News Panel</h3>
          <select
            value={selectedTicker}
            onChange={(e) => setSelectedTicker(e.target.value)}
            className="bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {tickers.map((t) => (
              <option key={t.ticker} value={t.ticker}>
                {t.ticker}
              </option>
            ))}
          </select>
        </div>
        <NewsPanel
          ticker={selectedTicker}
          headlines={selectedNews?.headlines || []}
          newsCount={selectedNews?.news_count}
        />

        {/* AI Analysis */}
        <div className="mt-4 pt-4 border-t border-gray-700">
          <h4 className="text-white text-sm font-semibold mb-2">🤖 AI Analysis</h4>
          {analysisLoading ? (
            <p className="text-gray-400 text-sm">Analyzing {selectedTicker}...</p>
          ) : analysis ? (
            <div className="space-y-1 text-sm">
              <p className="text-gray-300"><span className="text-gray-500">Sentiment:</span> {analysis.sentiment}</p>
              <p className="text-gray-300"><span className="text-gray-500">Momentum:</span> {analysis.momentum}</p>
              <p className="text-gray-300"><span className="text-gray-500">NDI / Regime:</span> {analysis.regime}</p>
              <p className="text-gray-300"><span className="text-gray-500">Market Interpretation:</span> {analysis.interpretation}</p>
              <p className="text-gray-300"><span className="text-gray-500">Risk / Outlook:</span> {analysis.risk_outlook}</p>
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No analysis available for {selectedTicker}</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default MarketIntelligence;
