import React from 'react';
import { NarrativeBreakdownData } from '../../../types/market-intelligence';

interface NarrativeBreakdownProps {
  data: NarrativeBreakdownData;
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    padding: '16px 20px',
    background: '#1e293b',
    borderRadius: 10,
    border: '1px solid #334155',
    marginBottom: 16,
  },
  title: {
    fontSize: 12,
    fontWeight: 700,
    color: '#94a3b8',
    letterSpacing: '0.5px',
    display: 'block',
    marginBottom: 12,
  },
  row: {
    marginBottom: 10,
  },
  rowLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: 13,
    marginBottom: 3,
  },
  rowValue: {
    color: '#94a3b8',
  },
  barContainer: {
    height: 6,
    background: '#0f172a',
    borderRadius: 3,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    transition: 'width 0.4s ease-out',
    borderRadius: 3,
  },
  biasContainer: {
    marginTop: 14,
    paddingTop: 14,
    borderTop: '1px solid #334155',
  },
  biasLabel: {
    fontSize: 13,
    fontWeight: 600,
    color: '#e2e8f0',
    display: 'block',
    marginBottom: 6,
  },
  biasTrack: {
    height: 24,
    borderRadius: 6,
    overflow: 'hidden',
    display: 'flex',
    fontSize: 10,
    fontWeight: 600,
    color: '#fff',
    textAlign: 'center',
  },
  biasSegment: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'width 0.4s ease-out',
    minWidth: 30,
  },
  biasLegend: {
    display: 'flex',
    gap: 16,
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 6,
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 4,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
  },
};

export const NarrativeBreakdown: React.FC<NarrativeBreakdownProps> = ({ data }) => {
  const renderBar = (pct: number, color: string) => (
    <div style={styles.barContainer}>
      <div style={{ ...styles.barFill, width: `${Math.min(pct, 100)}%`, background: color }} />
    </div>
  );

  return (
    <div style={styles.container}>
      <span style={styles.title}>📊 DESGLOSE NARRATIVO</span>

      <div style={styles.row}>
        <div style={styles.rowLabel}>
          <span>Consenso</span>
          <span style={styles.rowValue}>
            {data.consensusPercentage}% ({data.consensusLabel})
          </span>
        </div>
        {renderBar(data.consensusPercentage, '#22c55e')}
      </div>

      <div style={styles.row}>
        <div style={styles.rowLabel}>
          <span>Intensidad</span>
          <span style={styles.rowValue}>
            {data.intensityPercentage}% ({data.intensityLabel})
          </span>
        </div>
        {renderBar(data.intensityPercentage, '#3b82f6')}
      </div>

      <div style={styles.row}>
        <div style={styles.rowLabel}>
          <span>Dispersión</span>
          <span style={styles.rowValue}>
            {data.dispersionValue.toFixed(2)} ({data.dispersionLabel})
          </span>
        </div>
        {renderBar(data.dispersionValue * 100, '#6b7280')}
      </div>

      <div style={styles.biasContainer}>
        <span style={styles.biasLabel}>Sesgo de Medios / Orientación</span>
        <div style={styles.biasTrack}>
          <div
            style={{
              ...styles.biasSegment,
              width: `${data.mediaBias.centerBizPercentage}%`,
              background: '#6c63ff',
            }}
          >
            {data.mediaBias.centerBizPercentage >= 25 &&
              `${data.mediaBias.centerBizPercentage}% Center/Biz`}
          </div>
          <div
            style={{
              ...styles.biasSegment,
              width: `${data.mediaBias.leftPercentage}%`,
              background: '#ef4444',
            }}
          >
            {data.mediaBias.leftPercentage >= 25 && `${data.mediaBias.leftPercentage}% Left`}
          </div>
          <div
            style={{
              ...styles.biasSegment,
              width: `${data.mediaBias.rightPercentage}%`,
              background: '#3b82f6',
            }}
          >
            {data.mediaBias.rightPercentage >= 25 && `${data.mediaBias.rightPercentage}% Right`}
          </div>
        </div>
        <div style={styles.biasLegend}>
          <span style={styles.legendItem}>
            <span style={{ ...styles.dot, background: '#6c63ff' }} /> Corporativo/Negocios (
            {data.mediaBias.centerBizPercentage}%)
          </span>
          <span style={styles.legendItem}>
            <span style={{ ...styles.dot, background: '#ef4444' }} /> Crítico/Alternativo (
            {data.mediaBias.leftPercentage + data.mediaBias.rightPercentage}%)
          </span>
        </div>
      </div>
    </div>
  );
};

export default NarrativeBreakdown;
