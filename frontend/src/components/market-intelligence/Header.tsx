import React from 'react';

interface HeaderProps {
  updatedAt?: string;
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    marginBottom: 24,
  },
  titleRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: 700,
    color: '#e2e8f0',
    margin: 0,
    letterSpacing: '-0.5px',
  },
  subtitle: {
    fontSize: 15,
    color: '#94a3b8',
    margin: '4px 0 0 0',
    fontWeight: 400,
  },
  timestamp: {
    fontSize: 12,
    color: '#64748b',
    fontWeight: 500,
  },
};

export const Header: React.FC<HeaderProps> = ({ updatedAt }) => {
  return (
    <div style={styles.container}>
      <div style={styles.titleRow}>
        <h1 style={styles.title}>🧠 MARKET INTELLIGENCE</h1>
        {updatedAt && <span style={styles.timestamp}>Última actualización: {updatedAt}</span>}
      </div>
      <p style={styles.subtitle}>Análisis narrativo profundo de los mercados</p>
    </div>
  );
};

export default Header;
