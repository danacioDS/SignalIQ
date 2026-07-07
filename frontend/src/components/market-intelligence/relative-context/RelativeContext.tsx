import React from 'react';
import { RelativeContextData } from '../../../types/market-intelligence';
import SectorComparison from './SectorComparison';
import SectorRanking from './SectorRanking';

interface RelativeContextProps {
  data: RelativeContextData;
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    padding: '16px 20px',
    background: '#1e293b',
    borderRadius: 10,
    border: '1px solid #334155',
  },
  insight: {
    marginTop: 12,
    paddingTop: 12,
    borderTop: '1px solid #334155',
    fontSize: 13,
    color: '#94a3b8',
    lineHeight: 1.5,
  },
  insightIcon: {
    marginRight: 6,
  },
};

export const RelativeContext: React.FC<RelativeContextProps> = ({ data }) => {
  return (
    <div style={styles.container}>
      <SectorComparison
        sectorName={data.sectorName}
        comparison={data.comparison}
      />
      <SectorRanking
        ranking={data.sectorRanking}
        sectorName={data.sectorName}
      />
      <div style={styles.insight}>
        <span style={styles.insightIcon}>💡</span>
        {data.insight}
      </div>
    </div>
  );
};

export default RelativeContext;
