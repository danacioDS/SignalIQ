import React from 'react';
import { C } from './styles';

interface NDIThermometerProps {
  ndi: number | null | undefined;
  height?: number;
  width?: number;
  label?: string;
}

export const NDIThermometer: React.FC<NDIThermometerProps> = ({ 
  ndi = 0, 
  height = 280, 
  width = 50,
  label = 'NDI'
}) => {
  const safeNdi = typeof ndi === 'number' && !isNaN(ndi) ? ndi : 0;
  const clampedNdi = Math.max(-3, Math.min(3, safeNdi));
  const percentage = ((clampedNdi + 3) / 6) * 100;
  
  const getColor = (value: number) => {
    if (value > 2.0) return '#d32f2f';
    if (value > 1.5) return '#ff9800';
    if (value > 0.5) return '#ffee58';
    if (value > -0.5) return '#66bb6a';
    if (value > -1.5) return '#42a5f5';
    if (value > -2.0) return '#1565c0';
    return '#1a237e';
  };
  
  const color = getColor(safeNdi);
  
  const getRegime = (value: number) => {
    if (value > 2.0) return '🔴 Extreme Overheating';
    if (value > 1.5) return '🟠 Overheating';
    if (value > 0.5) return '🟡 Watching';
    if (value > -0.5) return '🟢 Stable';
    if (value > -1.5) return '🔵 Aligned';
    if (value > -2.0) return '🔵 Strong Undervalued';
    return '🔵 Extreme Undervalued';
  };

  const regime = getRegime(safeNdi);
  const bubblePosition = 100 - percentage;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      backgroundColor: C.card,
      borderRadius: '16px',
      padding: '20px',
      border: `1px solid ${C.cardBorder}`,
      boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
      width: '100%',
    }}>
      <div style={{
        fontSize: '14px',
        fontWeight: 'bold',
        color: C.text,
        marginBottom: '12px',
      }}>
        {label}
      </div>

      <div style={{
        position: 'relative',
        width: width,
        height: height,
        backgroundColor: C.bg,
        borderRadius: '30px',
        border: `2px solid ${C.cardBorder}`,
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'linear-gradient(to top, #1a237e, #1565c0, #42a5f5, #66bb6a, #ffee58, #ff9800, #d32f2f)',
          opacity: 0.3,
        }} />

        <div style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          width: '100%',
          height: `${percentage}%`,
          background: `linear-gradient(to top, 
            ${percentage > 50 ? '#d32f2f' : '#66bb6a'}, 
            ${percentage > 30 ? '#ff9800' : '#42a5f5'}
          )`,
          borderRadius: '30px',
          transition: 'height 0.5s ease',
          opacity: 0.9,
        }} />

        {[2.0, 1.5, 0.5, -0.5, -1.5, -2.0].map((mark) => {
          const pos = ((mark + 3) / 6) * 100;
          return (
            <div
              key={mark}
              style={{
                position: 'absolute',
                bottom: `${pos}%`,
                left: 0,
                width: '100%',
                height: '1px',
                backgroundColor: 'rgba(255,255,255,0.2)',
                borderTop: '1px dashed rgba(255,255,255,0.1)',
              }}
            />
          );
        })}

        <div style={{
          position: 'absolute',
          bottom: `${bubblePosition}%`,
          left: '50%',
          transform: 'translateX(-50%)',
          width: '44px',
          height: '44px',
          borderRadius: '50%',
          backgroundColor: color,
          border: `3px solid ${C.text}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: '11px',
          fontWeight: 'bold',
          zIndex: 10,
          boxShadow: `0 0 20px ${color}80`,
          transition: 'bottom 0.5s ease',
        }}>
          {safeNdi.toFixed(2)}
        </div>
      </div>

      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        width: '100%',
        marginTop: '8px',
        fontSize: '11px',
        color: C.muted,
      }}>
        <span>🔥 Overheating</span>
        <span>💎 Accumulation</span>
      </div>

      <div style={{
        marginTop: '12px',
        padding: '8px 16px',
        backgroundColor: C.accentBg,
        borderRadius: '8px',
        border: `1px solid ${C.cardBorder}`,
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        width: '100%',
        justifyContent: 'center',
      }}>
        <span style={{ fontSize: '18px' }}>📍</span>
        <span style={{ color: C.text, fontSize: '14px' }}>
          {regime}
        </span>
        <span style={{
          width: '12px',
          height: '12px',
          borderRadius: '50%',
          backgroundColor: color,
          marginLeft: '4px',
        }} />
      </div>
    </div>
  );
};

export default NDIThermometer;
