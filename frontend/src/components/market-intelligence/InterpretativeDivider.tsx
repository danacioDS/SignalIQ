import React from 'react';

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    padding: '12px 0',
    margin: '8px 0',
  },
  lineContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  line: {
    flex: 1,
    height: 1,
    background: '#334155',
    borderBottom: '2px solid transparent',
  },
  label: {
    fontSize: 11,
    fontWeight: 700,
    color: '#64748b',
    letterSpacing: '1.5px',
    whiteSpace: 'nowrap',
    padding: '0 8px',
  },
};

export const InterpretativeDivider: React.FC = () => {
  return (
    <div style={styles.container}>
      <div style={styles.lineContainer}>
        <span style={styles.line} />
        <span style={styles.label}>INTERPRETATIVE LAYER</span>
        <span style={styles.line} />
      </div>
    </div>
  );
};

export default InterpretativeDivider;
