import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import MarketIntelligence from './pages/MarketIntelligence';

const App: React.FC = () => {
  return (
    <Router>
      <div style={{ padding: '20px' }}>
        <nav style={{ marginBottom: '20px' }}>
          <Link to="/intelligence" style={{ marginRight: '20px' }}>
            🧠 Market Intelligence
          </Link>
        </nav>
        <Routes>
          <Route path="/intelligence" element={<MarketIntelligence />} />
          <Route path="/" element={<div>Dashboard (próximamente)</div>} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
