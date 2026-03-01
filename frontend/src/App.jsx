/**
 * App.jsx
 *
 * Main application component with dark theme and navigation.
 */

import React, { useEffect, useState, useCallback } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import SimulationPage from './pages/SimulationPage'
import WebsiteLaunchAnimation from './components/WebsiteLaunchAnimation'

const LAUNCH_KEY = 'sig_sys_launch_seen';

function App() {
  // Show launch animation only on first visit to homepage this session
  const [showLaunch, setShowLaunch] = useState(() => {
    if (typeof window === 'undefined') return false;
    const seen = sessionStorage.getItem(LAUNCH_KEY);
    // Only show on homepage (root path)
    return !seen && window.location.pathname === '/';
  });

  const handleLaunchComplete = useCallback(() => {
    sessionStorage.setItem(LAUNCH_KEY, '1');
    setShowLaunch(false);
  }, []);

  // Initialize dark theme on first load
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'dark');
  }, []);

  return (
    <div className="app">
      {/* Website launch animation (once per session, homepage only) */}
      {showLaunch && (
        <WebsiteLaunchAnimation onComplete={handleLaunchComplete} />
      )}

      {/* Skip to main content link for accessibility */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <header className="app-header">
        <Link to="/" className="logo">
          <h1>Signals & Systems</h1>
        </Link>
        <nav className="nav-links" role="navigation" aria-label="Main navigation">
          <Link to="/">Home</Link>
        </nav>
      </header>

      <main id="main-content" className="app-main" role="main">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/simulation/:id" element={<SimulationPage />} />
        </Routes>
      </main>

      <footer className="app-footer" role="contentinfo">
        <div className="footer-content">
          <span>Made by Shreyas Reddy</span>
        </div>
      </footer>
    </div>
  )
}

export default App
