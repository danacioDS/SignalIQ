import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import MarketIntelligence from './pages/MarketIntelligence';
import EconomicFoundation from './pages/EconomicFoundation';
import Data from './pages/Data';
import TechStack from './pages/TechStack';
import About from './pages/About';

const App: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: '📊 Dashboard' },
    { path: '/intelligence', label: '🧠 Market Intelligence' },
    { path: '/economic', label: '📚 Economic Foundation' },
    { path: '/data', label: '📡 Data' },
    { path: '/tech', label: '⚙️ Tech Stack' },
    { path: '/about', label: '📖 About' },
  ];

  return (
    <div style={{ 
      backgroundColor: '#0f172a',
      minHeight: '100vh',
      color: '#e2e8f0'
    }}>
      {/* Barra de navegación - ANCHO COMPLETO */}
      <nav style={{ 
        padding: '16px 32px',
        borderBottom: '1px solid #334155',
        display: 'flex',
        gap: '4px',
        flexWrap: 'wrap',
        backgroundColor: '#0f172a',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        width: '100%',
        boxSizing: 'border-box',
      }}>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              style={{
                color: isActive ? '#6c63ff' : '#94a3b8',
                textDecoration: 'none',
                fontWeight: isActive ? '700' : '500',
                fontSize: '14px',
                padding: '8px 18px',
                borderRadius: '6px',
                background: isActive ? 'rgba(108, 99, 255, 0.15)' : 'transparent',
                transition: 'all 0.2s',
                borderBottom: isActive ? '2px solid #6c63ff' : '2px solid transparent',
              }}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Contenido */}
      <div style={{ padding: '24px 32px', maxWidth: '1400px', margin: '0 auto' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/intelligence" element={<MarketIntelligence />} />
          <Route path="/economic" element={<EconomicFoundation />} />
          <Route path="/data" element={<Data />} />
          <Route path="/tech" element={<TechStack />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </div>
    </div>
  );
};

// Wrapper con Router
const AppWrapper: React.FC = () => {
  return (
    <Router>
      <App />
    </Router>
  );
};

export default AppWrapper;
