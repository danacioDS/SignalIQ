import React from 'react';
import { C } from './styles';
import { getRegimeColor, getRegimeIcon, getRegimeFromNDI } from '../utils/velocimeterUtils';

interface NarrativePanelProps {
  ticker: string;
  ndi: number;
  regime: string;
  sentiment: number;
  momentum: number;
  price: number;
  explanation?: {
    paragraph1: string;
    paragraph2: string;
    marketInsight: string;
    riskContext: string;
  };
}

const NarrativePanel: React.FC<NarrativePanelProps> = ({
  ticker = 'NVDA',
  ndi = 0,
  regime = 'STABLE',
  sentiment = 0,
  momentum = 0,
  price = 0,
  explanation,
}) => {
  // Usar ndi para obtener el régimen real (no el string)
  const safeNdi = typeof ndi === 'number' && !isNaN(ndi) ? ndi : 0;
  const regimeKey = getRegimeFromNDI(safeNdi);
  const regimeColor = getRegimeColor(regimeKey);
  const regimeIcon = getRegimeIcon(regimeKey);

  // Valores por defecto para explanation
  const defaultExplanation = {
    paragraph1: `${ticker} is in a ${regime} regime, indicating the market is in equilibrium.`,
    paragraph2: `Sentiment (${typeof sentiment === 'number' ? sentiment.toFixed(3) : 'N/A'}) and momentum (${typeof momentum === 'number' ? momentum.toFixed(3) : 'N/A'}) are aligned.`,
    marketInsight: `Price: $${typeof price === 'number' ? price.toFixed(2) : 'N/A'}. NDI: ${safeNdi.toFixed(3)}.`,
    riskContext: 'Risk: Moderate'
  };

  const exp = explanation || defaultExplanation;

  return (
    <div style={{
      backgroundColor: C.card,
      borderRadius: '12px',
      padding: '20px',
      border: `1px solid ${C.cardBorder}`,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
        <span style={{ fontSize: '24px' }}>{regimeIcon}</span>
        <h3 style={{ color: C.text, margin: 0 }}>{ticker} - {regime}</h3>
        <span style={{ 
          backgroundColor: regimeColor, 
          color: 'white', 
          padding: '2px 10px', 
          borderRadius: '12px',
          fontSize: '12px',
          fontWeight: 'bold'
        }}>
          {Math.abs(safeNdi) > 1.5 ? 'HIGH RISK' : 'MODERATE'}
        </span>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
        <div>
          <div style={{ color: C.muted, fontSize: '12px' }}>NDI</div>
          <div style={{ color: regimeColor, fontSize: '20px', fontWeight: 'bold' }}>
            {safeNdi.toFixed(3)}
          </div>
        </div>
        <div>
          <div style={{ color: C.muted, fontSize: '12px' }}>Sentiment</div>
          <div style={{ color: C.text, fontSize: '16px' }}>
            {typeof sentiment === 'number' ? sentiment.toFixed(3) : 'N/A'}
          </div>
        </div>
        <div>
          <div style={{ color: C.muted, fontSize: '12px' }}>Momentum</div>
          <div style={{ color: C.text, fontSize: '16px' }}>
            {typeof momentum === 'number' ? momentum.toFixed(3) : 'N/A'}
          </div>
        </div>
        <div>
          <div style={{ color: C.muted, fontSize: '12px' }}>Price</div>
          <div style={{ color: C.text, fontSize: '16px' }}>
            {typeof price === 'number' ? `$${price.toFixed(2)}` : 'N/A'}
          </div>
        </div>
      </div>

      <div style={{ 
        backgroundColor: C.accentBg, 
        borderRadius: '8px', 
        padding: '16px',
        marginTop: '8px'
      }}>
        <p style={{ color: C.text, margin: '0 0 8px 0' }}>
          {exp.paragraph1}
        </p>
        <p style={{ color: C.muted, margin: '0 0 8px 0', fontSize: '14px' }}>
          {exp.paragraph2}
        </p>
        <div style={{ display: 'flex', gap: '16px', marginTop: '12px' }}>
          <span style={{ color: C.muted, fontSize: '12px' }}>
            📊 {exp.marketInsight}
          </span>
          <span style={{ color: C.muted, fontSize: '12px' }}>
            ⚠️ {exp.riskContext}
          </span>
        </div>
      </div>
    </div>
  );
};

export default NarrativePanel;
