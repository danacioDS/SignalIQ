import React from 'react';
import { C } from './styles';
import {
  getNeedleAngle,
  getRegimeFromNDI,
  getRegimeLabel,
  getRegimeColor,
  getRegimeIcon,
} from '../utils/velocimeterUtils';

interface NDIVelocimeterProps {
  ndi: number | null | undefined;
  size?: number;
}

export const NDIVelocimeter: React.FC<NDIVelocimeterProps> = ({ ndi = 0, size = 300 }) => {
  // Asegurar que ndi es un número
  const safeNdi = typeof ndi === 'number' && !isNaN(ndi) ? ndi : 0;
  
  const regime = getRegimeFromNDI(safeNdi);
  const label = getRegimeLabel(regime);
  const color = getRegimeColor(regime);
  const icon = getRegimeIcon(regime);
  const angle = getNeedleAngle(safeNdi);

  const centerX = size / 2;
  const centerY = size / 2;
  const radius = size * 0.38;
  const strokeWidth = size * 0.08;

  // Calcular posición del extremo de la aguja
  const needleLength = radius * 0.85;
  const rad = (angle - 90) * (Math.PI / 180);
  const needleX = centerX + needleLength * Math.cos(rad);
  const needleY = centerY + needleLength * Math.sin(rad);

  // Colores del arco (degradado de 7 colores)
  
  const arcColors = [
    { stop: 0, color: '#1a237e' },    // -3.0: Extreme Undervalued
    { stop: 0.17, color: '#1565c0' }, // -2.0: Strong Undervalued
    { stop: 0.33, color: '#42a5f5' }, // -1.5: Aligned
    { stop: 0.50, color: '#66bb6a' }, // -0.5: Stable
    { stop: 0.67, color: '#ffee58' }, // 0.5: Watching
    { stop: 0.83, color: '#ff9800' }, // 1.5: Overheating
    { stop: 1.0, color: '#d32f2f' },  // 2.0: Extreme Overheating
  ];

  // Mapear NDI a posición en el arco (de -3 a +3)
  const ndiPos = Math.max(0, Math.min(1, (safeNdi + 5) / 6));

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center',
      backgroundColor: C.card,
      borderRadius: '20px',
      padding: '24px 20px 20px 20px',
      border: `1px solid ${C.cardBorder}`,
      boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
    }}>
      <svg width={size} height={size * 0.85} viewBox={`0 0 ${size} ${size * 0.85}`}>
        {/* Fondo del arco */}

        <circle
          cx={centerX}
          cy={centerY}
          r={radius}
          fill="none"
          stroke="url(#arcGradient)"
          strokeWidth={strokeWidth}
          strokeDasharray={`${ndiPos * 2 * Math.PI * radius} ${(1 - ndiPos) * 2 * Math.PI * radius}`}
          strokeDashoffset={0}
          transform={`rotate(-90 ${centerX} ${centerY})`}
          strokeLinecap="round"
          opacity={0.95}
        />

        {/* Degradado del arco */}
        <defs>
          <linearGradient id="arcGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            {arcColors.map(({ stop, color }) => (
              <stop key={stop} offset={`${stop * 100}%`} stopColor={color} />
            ))}
          </linearGradient>
          
          {/* Sombra para la aguja */}
          <filter id="needleShadow">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.5"/>
          </filter>
        </defs>

        {/* Arco con degradado */}
        <circle
          cx={centerX}
          cy={centerY}
          r={radius}
          fill="none"
          stroke="url(#arcGradient)"
          strokeWidth={strokeWidth}
          strokeDasharray={`${ndiPos * 2 * Math.PI * radius} ${(1 - ndiPos) * 2 * Math.PI * radius}`}
          strokeDashoffset={0}
          transform={`rotate(-90 ${centerX} ${centerY})`}
          strokeLinecap="round"
          opacity={0.95}
        />

        {/* Aguja con sombra */}
        <g filter="url(#needleShadow)">
          <line
            x1={centerX}
            y1={centerY}
            x2={needleX}
            y2={needleY}
            stroke={C.text}
            strokeWidth="3.5"
            strokeLinecap="round"
          />
        </g>

        {/* Círculo central */}
        <circle cx={centerX} cy={centerY} r="10" fill={C.text} opacity="0.9" />
        <circle cx={centerX} cy={centerY} r="5" fill={C.bg} />

        {/* Líneas de referencia */}
        <line
          x1={centerX - radius * 0.95}
          y1={centerY + radius * 0.05}
          x2={centerX - radius * 1.05}
          y2={centerY + radius * 0.05}
          stroke={C.muted}
          strokeWidth="2"
          opacity="0.3"
        />
        <line
          x1={centerX + radius * 0.95}
          y1={centerY + radius * 0.05}
          x2={centerX + radius * 1.05}
          y2={centerY + radius * 0.05}
          stroke={C.muted}
          strokeWidth="2"
          opacity="0.3"
        />
        <line
          x1={centerX}
          y1={centerY - radius * 0.95}
          x2={centerX}
          y2={centerY - radius * 1.05}
          stroke={C.muted}
          strokeWidth="2"
          opacity="0.3"
        />

        {/* Etiqueta: Overheating (arriba izquierda) */}
        <text
          x={centerX - radius * 0.55}
          y={centerY - radius * 0.35}
          textAnchor="middle"
          fill={C.muted}
          fontSize={size * 0.045}
          fontWeight="bold"
          opacity="0.7"
        >
          🔥 Overheating
        </text>

        {/* Etiqueta: Accumulation (abajo derecha) */}
        <text
          x={centerX + radius * 0.55}
          y={centerY + radius * 0.55}
          textAnchor="middle"
          fill={C.muted}
          fontSize={size * 0.045}
          fontWeight="bold"
          opacity="0.7"
        >
          💎 Accumulation
        </text>

        {/* Valor NDI en el centro */}
        <text
          x={centerX}
          y={centerY + radius * 0.25}
          textAnchor="middle"
          fill={color}
          fontSize={size * 0.09}
          fontWeight="bold"
        >
          {safeNdi.toFixed(3)}
        </text>
        <text
          x={centerX}
          y={centerY + radius * 0.38}
          textAnchor="middle"
          fill={C.muted}
          fontSize={size * 0.035}
        >
          NDI Value
        </text>
      </svg>

      {/* Panel inferior con régimen */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '14px', 
        marginTop: '8px',
        padding: '10px 20px',
        backgroundColor: C.accentBg,
        borderRadius: '12px',
        border: `1px solid ${C.cardBorder}`,
        width: '100%',
        justifyContent: 'center',
      }}>
        <span style={{ fontSize: '28px' }}>{icon}</span>
        <div>
          <div style={{ color: C.text, fontSize: '18px', fontWeight: 'bold' }}>
            {label}
          </div>
          <div style={{ color: C.muted, fontSize: '13px' }}>
            NDI: {safeNdi.toFixed(3)} • {regime.replace('_', ' ')}
          </div>
        </div>
        <div style={{
          width: '16px',
          height: '16px',
          borderRadius: '50%',
          backgroundColor: color,
          marginLeft: 'auto',
          boxShadow: `0 0 12px ${color}40`,
        }} />
      </div>
    </div>
  );
};

export default NDIVelocimeter;
