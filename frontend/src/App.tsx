import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { DashboardPage } from './pages/DashboardPage';
import { AthletePage } from './pages/AthletePage';
import { OAuthCallback } from './components/OAuthCallback';
import './App.css';

export function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/athlete" element={<AthletePage />} />
          <Route path="/auth/callback" element={<OAuthCallback />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
