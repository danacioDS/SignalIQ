import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import EconomicFoundation from './pages/EconomicFoundation';
import Data from './components/Data';
import TechStack from './components/TechStack';
import About from './components/About';
import { C } from './components/styles';

function App() {
  return (
    <Router>
      <div style={{ minHeight: '100vh', background: C.bg, color: C.text }}>
        <Navigation />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/foundation" element={<EconomicFoundation />} />
          <Route path="/data" element={<Data />} />
          <Route path="/techstack" element={<TechStack />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </div>
    </Router>
  );
}

function Navigation() {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: '📊 Dashboard' },
    { path: '/foundation', label: '📚 Economic Foundation' },
    { path: '/data', label: '📡 Data' },
    { path: '/techstack', label: '⚙️ Tech Stack' },
    { path: '/about', label: '📖 About' },
  ];

  return (
    <nav style={{
      display: 'flex',
      gap: 8,
      padding: '12px 24px',
      background: C.card,
      borderBottom: `1px solid ${C.cardBorder}`,
      alignItems: 'center',
      flexWrap: 'wrap',
    }}>
      <div style={{ fontWeight: 700, fontSize: 18, color: C.accent, marginRight: 16 }}>
        ◈ SignalIQ
      </div>
      {navItems.map((item) => {
        const isActive = location.pathname === item.path;
        return (
          <Link
            key={item.path}
            to={item.path}
            style={{
              color: isActive ? C.accent : C.muted,
              textDecoration: 'none',
              fontSize: 13,
              fontWeight: isActive ? 600 : 400,
              padding: '4px 10px',
              borderRadius: 6,
              background: isActive ? 'rgba(108,99,255,0.1)' : 'transparent',
              transition: 'all 0.2s',
            }}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

export default App;
