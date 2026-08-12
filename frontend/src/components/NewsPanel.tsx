import React from 'react';

interface NewsPanelProps {
  ticker: string;
  headlines: string[];
  newsCount?: number;
}

export const NewsPanel: React.FC<NewsPanelProps> = ({ ticker, headlines, newsCount }) => {
  const topHeadlines = headlines?.slice(0, 3) || [];

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h4 className="text-white text-sm font-semibold mb-2">
        📰 News Panel • {ticker}
      </h4>
      {topHeadlines.length > 0 ? (
        <div className="space-y-2">
          {topHeadlines.map((headline, index) => (
            <div key={index} className="text-gray-300 text-sm border-b border-gray-700 pb-2">
              {index + 1}. 📰 {headline}
            </div>
          ))}
          {newsCount && newsCount > 3 && (
            <p className="text-gray-500 text-xs mt-1">+ {newsCount - 3} more news</p>
          )}
        </div>
      ) : (
        <p className="text-gray-400 text-sm">No news available for {ticker}</p>
      )}
    </div>
  );
};
