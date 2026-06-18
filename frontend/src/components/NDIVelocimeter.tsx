/**
 * NDIVelocimeter.tsx
 * Velocímetro semicircular con panel lateral NDI Framework
 */

import React, { useEffect, useRef } from 'react';
import { C } from './styles';
import {
  getNeedleAngle,
  getRegimeFromNDI,
  getRegimeLabel,
  getRegimeColor,
  getRegimeIcon,
  NDI_RANGE,
} from '../utils/velocimeterUtils';

interface NDIVelocimeterProps {
  ndi: number;
  size?: number;
  className?: string;
}

export const NDIVelocimeter: React.FC<NDIVelocimeterProps> = ({
  ndi,
  size = 460,
  className,
}) => {
  const needleRef = useRef<SVGGElement>(null);
  
  // Obtener el régimen REAL usando la función correcta
  const regime = getRegimeFromNDI(ndi);
  const label = getRegimeLabel(regime);
  const color = getRegimeColor(regime);
  const icon = getRegimeIcon(regime);
  const angle = getNeedleAngle(ndi);

  const centerX = size / 2;
  const centerY = size / 2 + size * 0.06;
  const radius = size * 0.36;
  const needleLength = radius * 0.82;

  const needleX = centerX + needleLength * Math.sin((angle * Math.PI) / 180);
  const needleY = centerY - needleLength * Math.cos((angle * Math.PI) / 180);

  useEffect(() => {
    if (needleRef.current) {
      needleRef.current.style.transition = 'transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)';
    }
  }, [ndi]);

  const scaleMarks = [
    { value: -2.0, label: '-2.0' },
    { value: -1.5, label: '-1.5' },
    { value: -1.0, label: '-1.0' },
    { value: -0.5, label: '-0.5' },
    { value: 0.0, label: '0.0' },
    { value: 0.5, label: '0.5' },
    { value: 1.0, label: '1.0' },
    { value: 1.5, label: '1.5' },
    { value: 2.0, label: '2.0' },
  ];

  // Panel lateral - regímenes con valores
  const regimeLevels = [
    { value: 2.0, label: 'Extreme Overheating', color: '#ef4444', icon: '🔴', key: 'EXTREME_OVERHEATING' },
    { value: 1.5, label: 'Overheating', color: '#f97316', icon: '🟠', key: 'OVERHEATING' },
    { value: 0.5, label: 'Watching', color: '#eab308', icon: '🟡', key: 'WATCHING' },
    { value: 0.0, label: 'Stable', color: '#22c55e', icon: '🟢', key: 'STABLE' },
    { value: -0.5, label: 'Aligned', color: '#22c55e', icon: '🟢', key: 'ALIGNED' },
    { value: -1.5, label: 'Strong Undervalued', color: '#3b82f6', icon: '🔵', key: 'STRONG_UNDERVALUED' },
    { value: -2.0, label: 'Extreme Undervalued', color: '#1d4ed8', icon: '🔵', key: 'EXTREME_UNDERVALUED' },
  ];

  // Encontrar el régimen actual usando el key exacto
  const currentRegimeIndex = regimeLevels.findIndex(r => r.key === regime);

  return (
    <div className={className} style={{ display: 'flex', gap: 32, alignItems: 'stretch', justifyContent: 'center' }}>
      
      {/* ===== VELOCÍMETRO ===== */}
      <div style={{ flex: '0 0 auto', textAlign: 'center' }}>
        <svg
          width={size}
          height={size * 0.58}
          viewBox={`0 0 ${size} ${size * 0.58}`}
          style={{ overflow: 'visible' }}
        >
          <defs>
            <linearGradient id="ndiArcGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#1d4ed8" stopOpacity="1" />
              <stop offset="16%" stopColor="#3b82f6" stopOpacity="1" />
              <stop offset="33%" stopColor="#22c55e" stopOpacity="1" />
              <stop offset="50%" stopColor="#22c55e" stopOpacity="1" />
              <stop offset="66%" stopColor="#eab308" stopOpacity="1" />
              <stop offset="83%" stopColor="#f97316" stopOpacity="1" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="1" />
            </linearGradient>
            <filter id="needleShadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="4" floodOpacity="0.3" />
            </filter>
          </defs>

          <path
            d={`
              M ${centerX - radius * 0.90} ${centerY}
              A ${radius * 0.90} ${radius * 0.90} 0 0 1 ${centerX + radius * 0.90} ${centerY}
            `}
            fill="none"
            stroke="url(#ndiArcGradient)"
            strokeWidth={size * 0.05}
            strokeLinecap="round"
            opacity={0.85}
          />

          {scaleMarks.map(({ value }) => {
            const angle = getNeedleAngle(value);
            const innerRadius = radius * 0.72;
            const outerRadius = radius * 0.80;
            const x1 = centerX + innerRadius * Math.sin((angle * Math.PI) / 180);
            const y1 = centerY - innerRadius * Math.cos((angle * Math.PI) / 180);
            const x2 = centerX + outerRadius * Math.sin((angle * Math.PI) / 180);
            const y2 = centerY - outerRadius * Math.cos((angle * Math.PI) / 180);
            const isActive = Math.abs(value - ndi) < 0.05;

            return (
              <line
                key={value}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="#ffffff"
                strokeWidth={isActive ? size * 0.018 : size * 0.008}
                strokeLinecap="round"
                opacity={isActive ? 1 : 0.3}
              />
            );
          })}

          {scaleMarks.map(({ value, label }) => {
            const angle = getNeedleAngle(value);
            const textRadius = radius * 0.60;
            const x = centerX + textRadius * Math.sin((angle * Math.PI) / 180);
            const y = centerY - textRadius * Math.cos((angle * Math.PI) / 180);
            const isActive = Math.abs(value - ndi) < 0.05;

            return (
              <text
                key={value}
                x={x}
                y={y + size * 0.025}
                textAnchor="middle"
                fontSize={size * 0.032}
                fill="#ffffff"
                fontWeight={isActive ? 'bold' : 'normal'}
                opacity={isActive ? 1 : 0.5}
              >
                {label}
              </text>
            );
          })}

          <g
            ref={needleRef}
            style={{
              transformOrigin: `${centerX}px ${centerY}px`,
              transform: `rotate(${angle}deg)`,
            }}
          >
            <line
              x1={centerX - size * 0.04}
              y1={centerY}
              x2={needleX}
              y2={needleY}
              stroke="#ffffff"
              strokeWidth={size * 0.018}
              strokeLinecap="round"
              filter="url(#needleShadow)"
            />
            <circle
              cx={centerX}
              cy={centerY}
              r={size * 0.035}
              fill="#ffffff"
              stroke={color}
              strokeWidth={size * 0.012}
              filter="url(#needleShadow)"
            />
            <circle
              cx={centerX}
              cy={centerY}
              r={size * 0.015}
              fill={color}
              opacity={0.6}
            />
          </g>

          <text
            x={centerX}
            y={centerY - size * 0.07}
            textAnchor="middle"
            fontSize={size * 0.075}
            fontWeight="bold"
            fill={color}
            filter="drop-shadow(0 1px 4px rgba(0,0,0,0.2))"
          >
            {icon} {label}
          </text>

          <rect
            x={centerX - size * 0.12}
            y={centerY + size * 0.02}
            width={size * 0.24}
            height={size * 0.06}
            rx={size * 0.015}
            fill="rgba(0,0,0,0.85)"
            stroke={color}
            strokeWidth={size * 0.004}
          />
          <text
            x={centerX}
            y={centerY + size * 0.065}
            textAnchor="middle"
            fontSize={size * 0.045}
            fontWeight="bold"
            fill={color}
          >
            {ndi > 0 ? `+${ndi.toFixed(3)}` : ndi.toFixed(3)}
          </text>

          <text
            x={centerX}
            y={centerY + size * 0.12}
            textAnchor="middle"
            fontSize={size * 0.02}
            fill={C.muted}
            opacity={0.5}
          >
            NDI Value
          </text>
        </svg>
      </div>

      {/* ===== PANEL LATERAL: NDI FRAMEWORK ===== */}
      <div style={{
        width: 200,
        padding: '16px 20px',
        background: C.card,
        borderRadius: 12,
        border: `1px solid ${C.cardBorder}`,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
      }}>
        <h4 style={{ fontSize: 13, fontWeight: 600, color: C.text, margin: '0 0 4px 0' }}>
          📊 NDI Framework
        </h4>
        <p style={{ fontSize: 10, color: C.muted, margin: '0 0 12px 0' }}>
          NDI = Sentiment − Momentum
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {regimeLevels.map((level, index) => {
            const isCurrent = index === currentRegimeIndex;
            
            return (
              <div
                key={level.value}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '3px 6px',
                  borderRadius: 4,
                  background: isCurrent ? `${level.color}25` : 'transparent',
                  borderLeft: isCurrent ? `3px solid ${level.color}` : '3px solid transparent',
                }}
              >
                <span style={{ fontSize: 12, color: level.color, width: 20 }}>{level.icon}</span>
                <span style={{
                  fontSize: 11,
                  color: isCurrent ? level.color : C.muted,
                  fontWeight: isCurrent ? 700 : 400,
                  flex: 1,
                }}>
                  {level.label}
                </span>
                <span style={{
                  fontSize: 10,
                  color: isCurrent ? '#ffffff' : C.muted,
                  fontWeight: isCurrent ? 700 : 400,
                  width: 30,
                  textAlign: 'right',
                }}>
                  {level.value.toFixed(1)}
                </span>
                {isCurrent && (
                  <span style={{ 
                    fontSize: 16, 
                    color: level.color,
                    fontWeight: 'bold',
                  }}>
                    ←
                  </span>
                )}
              </div>
            );
          })}
        </div>

        <div style={{
          marginTop: 12,
          padding: '8px 12px',
          background: `${color}25`,
          borderRadius: 8,
          border: `2px solid ${color}`,
          textAlign: 'center',
        }}>
          <span style={{ fontSize: 14, fontWeight: 700, color: color }}>
            {icon} {label}
          </span>
          <span style={{ fontSize: 12, color: C.text, marginLeft: 8 }}>
            NDI: {ndi > 0 ? `+${ndi.toFixed(3)}` : ndi.toFixed(3)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default NDIVelocimeter;
