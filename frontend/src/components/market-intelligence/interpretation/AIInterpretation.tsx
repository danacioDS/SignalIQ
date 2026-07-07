import React, { useState } from 'react';

interface AIInterpretationProps {
  interpretation: string;
  disclaimer: string;
}

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
    cursor: 'pointer',
    userSelect: 'none',
  },
  title: {
    fontSize: 14,
    fontWeight: 600,
    color: '#e2e8f0',
  },
  toggle: {
    fontSize: 18,
    color: '#94a3b8',
  },
  content: {
    marginTop: 10,
    paddingTop: 12,
    borderTop: '1px solid #334155',
  },
  interpretation: {
    fontSize: 14,
    color: '#e2e8f0',
    lineHeight: 1.6,
    margin: 0,
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
    fontSize: 14,
  },
  disclaimerText: {
    fontSize: 11,
    color: '#94a3b8',
    lineHeight: 1.4,
  },
};

export const AIInterpretation: React.FC<AIInterpretationProps> = ({
  interpretation,
  disclaimer,
}) => {
  const [expanded, setExpanded] = useState(true);

  return (
    <div style={styles.container}>
      <div style={styles.header} onClick={() => setExpanded(!expanded)}>
        <span style={styles.title}>🤖 AI Interpretation</span>
        <span style={styles.toggle}>{expanded ? '−' : '+'}</span>
      </div>

      {expanded && (
        <>
          <div style={styles.content}>
            <p style={styles.interpretation}>{interpretation}</p>
          </div>

          <div style={styles.disclaimer}>
            <span style={styles.disclaimerIcon}>⚠️</span>
            <span style={styles.disclaimerText}>{disclaimer}</span>
          </div>
        </>
      )}
    </div>
  );
};

export default AIInterpretation;
