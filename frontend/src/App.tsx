import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import MarketIntelligence from './pages/MarketIntelligence';

// Importar el Dashboard existente
// (Asegúrate de que la ruta sea correcta)
import Dashboard from './pages/Dashboard';

const App: React.FC = () => {
  return (
    <Router>
      <div style={{ 
        padding: '20px',
        backgroundColor: '#0f172a',
        minHeight: '100vh'
      }}>
        <nav style={{ 
          marginBottom: '20px',
          display: 'flex',
          gap: '20px',
          borderBottom: '1px solid #334155',
          paddingBottom: '12px'
        }}>
          <Link 
            to="/" 
            style={{ 
              color: '#94a3b8',
              textDecoration: 'none',
              fontWeight: '600',
              fontSize: '14px',
              padding: '4px 12px',
              borderRadius: '4px',
            }}
          >
            📊 Dashboard
          </Link>
          <Link 
            to="/intelligence" 
            style={{ 
              color: '#6c63ff',
              textDecoration: 'none',
              fontWeight: '600',
              fontSize: '14px',
              padding: '4px 12px',
              borderRadius: '4px',
            }}
          >
            🧠 Market Intelligence
          </Link>
        </nav>
        
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/intelligence" element={<MarketIntelligence />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
