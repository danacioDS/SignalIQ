import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell
} from 'recharts';

interface Signal {
  ticker: string;
  ndi: number;
  confidence: string;
  bubble_risk_score: number;
  regime: string;
  recommendation: string;
}

interface MarketSummary {
  total_tickers: number;
  high_confidence_count: number;
  avg_ndi: number;
  avg_bubble_risk: number;
  market_regime: string;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:10000';

function App() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [summary, setSummary] = useState<MarketSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/signals`);
      setSignals(response.data.signals);
      setSummary(response.data.market_summary);
      setError(null);
    } catch (err) {
      setError('Error connecting to SignalIQ API');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getNDIColor = (ndi: number) => {
    if (ndi > 1.0) return '#EF4444';
    if (ndi > 0.5) return '#F59E0B';
    if (ndi < -1.0) return '#10B981';
    return '#6B7280';
  };

  const getConfidenceBadge = (confidence: string) => {
    const colors = {
      High: 'bg-red-100 text-red-800',
      Medium: 'bg-yellow-100 text-yellow-800',
      Low: 'bg-green-100 text-green-800'
    };
    return colors[confidence as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading SignalIQ...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <div className="bg-black border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-white">
                SIGNAL<span className="text-blue-500">IQ</span>
              </h1>
              <p className="text-gray-400 text-sm">Narrative Divergence Index</p>
            </div>
            <div className="text-right">
              <div className="text-gray-400 text-xs">MARKET REGIME</div>
              <div className={`text-sm font-semibold ${
                summary?.market_regime === 'Divergence Warning' ? 'text-red-400' : 'text-green-400'
              }`}>
                {summary?.market_regime || 'Loading...'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6">
            <p className="text-gray-400 text-sm">High Confidence</p>
            <p className="text-3xl font-bold text-white">{summary?.high_confidence_count || 0}</p>
            <p className="text-xs text-gray-500">out of {summary?.total_tickers || 0}</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-6">
            <p className="text-gray-400 text-sm">Avg NDI</p>
            <p className={`text-3xl font-bold ${(summary?.avg_ndi || 0) > 0.5 ? 'text-red-500' : 'text-green-500'}`}>
              {summary?.avg_ndi?.toFixed(2) || '0.00'}
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg p-6">
            <p className="text-gray-400 text-sm">Bubble Risk</p>
            <p className="text-3xl font-bold text-white">{summary?.avg_bubble_risk?.toFixed(0) || '0'}</p>
            <p className="text-xs text-gray-500">/100</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-6">
            <p className="text-gray-400 text-sm">Risk Level</p>
            <p className="text-3xl font-bold text-white">
              {(summary?.avg_bubble_risk || 0) > 60 ? 'HIGH' : 'MODERATE'}
            </p>
          </div>
        </div>

        {/* Signals Table */}
        <div className="bg-gray-800 rounded-lg overflow-hidden mb-8">
          <div className="px-6 py-4 border-b border-gray-700">
            <h2 className="text-lg font-semibold text-white">Institutional Signals</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-900">
                <tr className="text-left text-gray-400 text-sm">
                  <th className="px-6 py-3">Ticker</th>
                  <th className="px-6 py-3">NDI</th>
                  <th className="px-6 py-3">Confidence</th>
                  <th className="px-6 py-3">Bubble Risk</th>
                  <th className="px-6 py-3">Regime</th>
                  <th className="px-6 py-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {signals.map((signal) => (
                  <tr key={signal.ticker} className="hover:bg-gray-750">
                    <td className="px-6 py-4 font-medium text-white">{signal.ticker}</td>
                    <td className="px-6 py-4">
                      <span className={`font-mono font-bold ${
                        signal.ndi > 0 ? 'text-red-400' : 'text-green-400'
                      }`}>
                        {signal.ndi > 0 ? '+' : ''}{signal.ndi.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceBadge(signal.confidence)}`}>
                        {signal.confidence}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-700 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              signal.bubble_risk_score > 60 ? 'bg-red-500' :
                              signal.bubble_risk_score > 40 ? 'bg-yellow-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${signal.bubble_risk_score}%` }}
                          />
                        </div>
                        <span className="text-sm">{signal.bubble_risk_score.toFixed(0)}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-300 text-sm">{signal.regime}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        signal.recommendation.includes('REDUCE') ? 'bg-red-900 text-red-300' :
                        signal.recommendation.includes('BUY') ? 'bg-green-900 text-green-300' :
                        'bg-gray-700 text-gray-300'
                      }`}>
                        {signal.recommendation.includes('REDUCE') ? 'REDUCE' :
                         signal.recommendation.includes('BUY') ? 'BUY' : 'HOLD'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Chart */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-white font-semibold mb-4">NDI Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={signals}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="ticker" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: 'none' }}
                labelStyle={{ color: '#F3F4F6' }}
              />
              <Bar dataKey="ndi">
                {signals.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getNDIColor(entry.ndi)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

export default App;
