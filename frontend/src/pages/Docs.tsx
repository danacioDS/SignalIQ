import React from 'react';
import { C } from '../components/styles';
import EconomicFoundation from '../components/EconomicFoundation';
import Methodology from '../components/Methodology';
import TechStack from '../components/TechStack';
import Architecture from '../components/Architecture';

export default function Docs() {
  const [section, setSection] = React.useState('foundation');

  const sections = [
    { id: 'foundation', label: '📚 Economic Foundation', component: EconomicFoundation },
    { id: 'methodology', label: '📈 Methodology', component: Methodology },
    { id: 'tech', label: '⚙️ Tech Stack', component: TechStack },
    { id: 'architecture', label: '🏗️ Architecture', component: Architecture },
  ];

  const ActiveComponent = sections.find(s => s.id === section)?.component || EconomicFoundation;

  return (
    <div style={{ padding: "24px 32px", maxWidth: 1200 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>📚 Docs</h1>
      
      <div style={{
        display: 'flex',
        gap: 8,
        flexWrap: 'wrap',
        marginBottom: 24,
        borderBottom: `1px solid ${C.cardBorder}`,
        paddingBottom: 12,
      }}>
        {sections.map((s) => (
          <button
            key={s.id}
            onClick={() => setSection(s.id)}
            style={{
              background: section === s.id ? C.accentBg : 'transparent',
              color: section === s.id ? C.text : C.muted,
              border: 'none',
              padding: '8px 16px',
              borderRadius: 8,
              fontSize: 13,
              cursor: 'pointer',
              fontWeight: section === s.id ? 600 : 400,
              transition: 'all 0.2s',
            }}
          >
            {s.label}
          </button>
        ))}
      </div>

      <ActiveComponent />
    </div>
  );
}
