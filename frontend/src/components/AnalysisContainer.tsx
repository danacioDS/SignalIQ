import React from 'react';
import { useSignalAnalysis } from '../hooks/useSignalAnalysis';
import { NDIVelocimeter } from './NDIVelocimeter';
import NarrativePanel from './NarrativePanel';

interface AnalysisContainerProps {
  signal: {
    ticker: string;
    ndi: number;
    sentiment: number;
    momentum: number;
    price: number;
    sector: string;
    confidence: number;
  } | null;
}

export const AnalysisContainer: React.FC<AnalysisContainerProps> = ({ signal }) => {
  // Siempre llamar al hook, con datos por defecto si es null
  const defaultSignal = {
    ticker: 'NVDA',
    ndi: 0,
    sentiment: 0,
    momentum: 0,
    price: 0,
    sector: 'Unknown',
    confidence: 0,
  };

  const analysis = useSignalAnalysis(signal || defaultSignal);

  if (!signal) {
    return <div>No signal selected</div>;
  }

  return (
    <>
      <NDIVelocimeter ndi={analysis.ndi} size={420} />
      <NarrativePanel
        ticker={signal.ticker}
        ndi={analysis.ndi}
        regime={analysis.regime}
        sentiment={signal.sentiment}
        momentum={signal.momentum}
        price={signal.price}
        explanation={analysis.explanation}
      />
    </>
  );
};

export default AnalysisContainer;
