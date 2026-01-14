import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { DashboardPage } from './pages/DashboardPage';
import { OAuthCallback } from './components/OAuthCallback';
import './App.css';

export function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/strava/authorize" element={<OAuthCallback />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
