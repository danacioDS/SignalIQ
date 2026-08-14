import React from 'react';
import { C } from './styles';
import { getColorFromNDI } from '../utils/velocimeterUtils';

interface TickerFocusStripProps {
  tickers: string[];
  selectedTicker: string;
  onSelect: (ticker: string) => void;
  ndiMap: Record<string, number>;
}

export const TickerFocusStrip: React.FC<TickerFocusStripProps> = ({
  tickers,
  selectedTicker,
  onSelect,
  ndiMap,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '8px',
        justifyContent: 'center',
        padding: '8px 0 16px 0',
        borderBottom: '1px solid ' + C.cardBorder,
        marginBottom: 16,
        width: '100%',
        minHeight: '80px',
        overflow: 'visible',
      }}
    >
      {tickers.map((ticker) => {
        const ndi = ndiMap[ticker] ?? 0;
        const color = getColorFromNDI(ndi);
        const isSelected = ticker === selectedTicker;

        return (
          <button
            key={ticker}
            onClick={() => onSelect(ticker)}
            style={{
              flex: '0 0 auto',
              background: isSelected ? color : 'transparent',
              color: isSelected ? '#ffffff' : C.text,
              border: '2px solid ' + (isSelected ? color : C.cardBorder),
              borderRadius: 8,
              padding: '6px 16px',
              fontSize: 13,
              fontWeight: isSelected ? 'bold' : 'normal',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              opacity: isSelected ? 1 : 0.7,
              whiteSpace: 'nowrap',
            }}
          >
            {ticker}
          </button>
        );
      })}
    </div>
  );
};

export default TickerFocusStrip;
