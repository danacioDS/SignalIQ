import React from 'react';
import { C } from './styles';

interface NDIGaugeProps {
  ndi: number | null | undefined;
  size?: number;
}

export const NDIGauge: React.FC<NDIGaugeProps> = ({ ndi = 0, size = 300 }) => {
  const safeNdi = typeof ndi === 'number' && !isNaN(ndi) ? ndi : 0;
  const clampedNdi = Math.max(-3, Math.min(3, safeNdi));
  
  const percentage = (clampedNdi + 3) / 6;
  const angle = 180 * percentage;

  const width = size;
  const height = size * 0.52;
  const centerX = width / 2;
  const centerY = height * 0.88;
  const radius = size * 0.38;
  const strokeWidth = size * 0.06;

  const needleLength = radius * 0.78;
  const rad = (angle - 180) * (Math.PI / 180);
  const needleX = centerX + needleLength * Math.cos(rad);
  const needleY = centerY + needleLength * Math.sin(rad);

  const getRegimeInfo = (value: number) => {
    if (value > 2.0) return { color: '#ef4444', label: 'Extreme Overheating', icon: '🔴' };
    if (value > 1.5) return { color: '#f97316', label: 'Overheating', icon: '🟠' };
    if (value > 0.5) return { color: '#eab308', label: 'Watching', icon: '🟡' };
    if (value > -0.5) return { color: '#22c55e', label: 'Equilibrium', icon: '🟢' };
    if (value > -1.5) return { color: '#3b82f6', label: 'Buy Opportunity', icon: '🔵' };
    if (value > -2.0) return { color: '#3b4ef6fa', label: 'Buy Opportunity', icon: '🔵' };
    return { color: '#6b21a8', label: 'Capitulation', icon: '💎' };
  };

  const regime = getRegimeInfo(safeNdi);

  // SOLO UNA BANDA - 7 segmentos de colores
  const segments = [
    { start: 0.00, end: 0.30, color: '#3b82f6' },
    { start: 0.30, end: 0.60, color: '#22c55e' },
    { start: 0.60, end: 0.80, color: '#eab308' },
    { start: 0.80, end: 1.00, color: '#f97316' },
  ];

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      backgroundColor: 'transparent',
      padding: '8px',
      width: '100%',
    }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        {/* Fondo del arco */}
        <path
          d={`M ${centerX - radius} ${centerY} A ${radius} ${radius} 0 0 1 ${centerX + radius} ${centerY}`}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth={strokeWidth + 8}
          strokeLinecap="round"
        />

        {/* ÚNICA BANDA - 7 segmentos de colores */}
        {segments.map((seg, idx) => {
          const startAngle = 180 * seg.start;
          const endAngle = 180 * seg.end;
          const startRad = (startAngle - 180) * (Math.PI / 180);
          const endRad = (endAngle - 180) * (Math.PI / 180);
          
          const x1 = centerX + radius * Math.cos(startRad);
          const y1 = centerY + radius * Math.sin(startRad);
          const x2 = centerX + radius * Math.cos(endRad);
          const y2 = centerY + radius * Math.sin(endRad);
          
          return (
            <path
              key={idx}
              d={`M ${x1} ${y1} A ${radius} ${radius} 0 0 1 ${x2} ${y2}`}
              fill="none"
              stroke={seg.color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              opacity="0.7"
            />
          );
        })}

        {/* SOLO LA AGUJA - sin doble banda */}
        <line
          x1={centerX}
          y1={centerY}
          x2={needleX}
          y2={needleY}
          stroke="#e5e7eb"
          strokeWidth="2.5"
          strokeLinecap="round"
          style={{ filter: 'drop-shadow(0 2px 8px rgba(0,0,0,0.4))' }}
        />

        {/* Círculo central */}
        <circle cx={centerX} cy={centerY} r="10" fill="#1a1a2e" stroke="#e5e7eb" strokeWidth="2" />
        <circle cx={centerX} cy={centerY} r="4" fill={regime.color} />

        {/* Marcas de referencia */}
        {[-2, -1, 0, 1, 2].map((mark) => {
          const pos = (mark + 3) / 6;
          const markAngle = 180 * pos;
          const markRad = (markAngle - 180) * (Math.PI / 180);
          const r1 = radius - strokeWidth/2;
          const r2 = radius - strokeWidth/2 - 10;
          
          return (
            <line
              key={mark}
              x1={centerX + r1 * Math.cos(markRad)}
              y1={centerY + r1 * Math.sin(markRad)}
              x2={centerX + r2 * Math.cos(markRad)}
              y2={centerY + r2 * Math.sin(markRad)}
              stroke="rgba(255,255,255,0.2)"
              strokeWidth="1.5"
            />
          );
        })}

        {/* Valor NDI */}
        <text
          x={centerX}
          y={centerY - radius * 0.35}
          textAnchor="middle"
          fill={regime.color}
          fontSize={size * 0.08}
          fontWeight="700"
          style={{ textShadow: `0 0 20px ${regime.color}30` }}
        >
          {safeNdi.toFixed(2)}
        </text>
        <text
          x={centerX}
          y={centerY - radius * 0.22}
          textAnchor="middle"
          fill="#6b7280"
          fontSize={size * 0.025}
          fontWeight="500"
          letterSpacing="1"
        >
          NDI VALUE
        </text>
      </svg>

      {/* Panel inferior */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        marginTop: '4px',
        padding: '10px 20px',
        backgroundColor: `${regime.color}15`,
        borderRadius: '12px',
        border: `1px solid ${regime.color}25`,
        width: 'auto',
        minWidth: '180px',
        justifyContent: 'center',
        backdropFilter: 'blur(4px)',
      }}>
        <span style={{ fontSize: '20px' }}>{regime.icon}</span>
        <span style={{ 
          color: regime.color, 
          fontSize: '15px', 
          fontWeight: '600',
          letterSpacing: '0.3px',
        }}>
          {regime.label}
        </span>
        <span style={{
          width: '10px',
          height: '10px',
          borderRadius: '50%',
          backgroundColor: regime.color,
          boxShadow: `0 0 16px ${regime.color}50`,
        }} />
      </div>
    </div>
  );
};

export default NDIGauge;
