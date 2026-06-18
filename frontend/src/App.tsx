import React from 'react';
import { C } from './components/styles';
import Dashboard from './pages/Dashboard';
import Intelligence from './pages/Intelligence';
import Data from './pages/Data';
import About from './pages/About';
import EconomicFoundation from './components/EconomicFoundation';
import Methodology from './components/Methodology';
import TechStack from './components/TechStack';
import Architecture from './components/Architecture';
import './App.css';

function App() {
  const [active, setActive] = React.useState('dashboard');

  const navItems = [
    { id: 'dashboard', label: '📊 Dashboard' },
    { id: 'intelligence', label: '🧠 Intelligence' },
    { id: 'data', label: '📡 Data' },
    { id: 'foundation', label: '📚 Economic Foundation' },
    { id: 'methodology', label: '📈 Methodology' },
    { id: 'techstack', label: '⚙️ Tech Stack' },
    { id: 'architecture', label: '🏗️ Architecture' },
    { id: 'about', label: '📖 About' },
  ];

  const components: Record<string, React.ComponentType> = {
    dashboard: Dashboard,
    intelligence: Intelligence,
    data: Data,
    foundation: EconomicFoundation,
    methodology: Methodology,
    techstack: TechStack,
    architecture: Architecture,
    about: About,
  };

  const ActiveComponent = components[active] || Dashboard;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', background: C.bg, color: C.text }}>
      <nav style={{
        background: C.card,
        borderBottom: `1px solid ${C.cardBorder}`,
        padding: '12px 24px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        flexWrap: 'wrap',
      }}>
        <span style={{ fontWeight: 700, fontSize: 18, color: C.accent, marginRight: 8 }}>◈ SignalIQ</span>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActive(item.id)}
              style={{
                color: active === item.id ? C.text : C.muted,
                background: active === item.id ? C.accentBg : 'transparent',
                border: 'none',
                fontSize: 13,
                padding: '5px 10px',
                borderRadius: 4,
                cursor: 'pointer',
                transition: 'all 0.2s',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={(e) => { if (active !== item.id) e.currentTarget.style.color = C.text; }}
              onMouseLeave={(e) => { if (active !== item.id) e.currentTarget.style.color = C.muted; }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      <div style={{ flex: 1, padding: '16px' }}>
        <ActiveComponent />
      </div>
    </div>
  );
}

export default App;
