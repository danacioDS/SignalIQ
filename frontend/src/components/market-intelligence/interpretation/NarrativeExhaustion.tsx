import React from 'react';
import { NarrativeExhaustionData } from '../../../types/market-intelligence';

interface NarrativeExhaustionProps {
  data: NarrativeExhaustionData;
}

const levelConfig = {
  BAJA: { color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)', label: '🟢 BAJA' },
  MEDIA: { color: '#eab308', bg: 'rgba(234, 179, 8, 0.1)', label: '🟡 MEDIA' },
  ALTA: { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)', label: '🟠 ALTA' },
  CRÍTICA: { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)', label: '🔴 CRÍTICA' },
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    padding: '16px 20px',
    background: '#1e293b',
    borderRadius: 10,
    border: '1px solid #334155',
    marginBottom: 16,
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  titleRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  title: {
    fontSize: 14,
    fontWeight: 600,
    color: '#e2e8f0',
  },
  betaBadge: {
    fontSize: 10,
    fontWeight: 700,
    color: '#6c63ff',
    background: 'rgba(108, 99, 255, 0.15)',
    padding: '2px 10px',
    borderRadius: 12,
    letterSpacing: '0.5px',
  },
  levelBadge: {
    fontSize: 13,
    fontWeight: 700,
    padding: '2px 14px',
    borderRadius: 16,
    border: '1px solid',
  },
  conditionsLabel: {
    fontSize: 12,
    color: '#94a3b8',
    display: 'block',
    marginBottom: 6,
  },
  conditionsList: {
    listStyle: 'none',
    padding: 0,
    margin: '4px 0 0 0',
  },
  conditionItem: {
    fontSize: 13,
    color: '#e2e8f0',
    padding: '4px 0',
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  checkmark: {
    fontSize: 13,
  },
  disclaimer: {
    marginTop: 12,
    paddingTop: 10,
    borderTop: '1px solid #334155',
    display: 'flex',
    gap: 8,
    alignItems: 'flex-start',
  },
  disclaimerIcon: {
    fontSize: 13,
  },
  disclaimerText: {
    fontSize: 11,
    color: '#94a3b8',
    lineHeight: 1.4,
  },
};

export const NarrativeExhaustion: React.FC<NarrativeExhaustionProps> = ({ data }) => {
  const config = levelConfig[data.level];

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={styles.titleRow}>
          <span style={styles.title}>🔬 Narrative Exhaustion</span>
          {data.isBeta && <span style={styles.betaBadge}>🧪 BETA</span>}
        </div>
        <span
          style={{
            ...styles.levelBadge,
            color: config.color,
            borderColor: config.color,
          }}
        >
          {config.label}
        </span>
      </div>

      <div>
        <span style={styles.conditionsLabel}>
          Condiciones observadas ({data.conditionsObserved}/{data.totalConditions}):
        </span>
        <ul style={styles.conditionsList}>
          {data.conditionsDetails.map((condition) => (
            <li key={condition.id} style={styles.conditionItem}>
              <span style={styles.checkmark}>
                {condition.isMet ? '✅' : '⬜'}
              </span>
              {condition.description}
            </li>
          ))}
        </ul>
      </div>

      <div style={styles.disclaimer}>
        <span style={styles.disclaimerIcon}>⚠️</span>
        <span style={styles.disclaimerText}>{data.disclaimer}</span>
      </div>
    </div>
  );
};

export default NarrativeExhaustion;
