/**
 * App.jsx
 *
 * Main application component with dark theme and navigation.
 */

import React, { useEffect, useState, useCallback } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import SimulationPage from './pages/SimulationPage'
import WebsiteLaunchAnimation from './components/WebsiteLaunchAnimation'
import ErrorBoundary from './components/ErrorBoundary'
import ThemeToggle from './components/ThemeToggle'
import KeyboardShortcutsModal, { useKeyboardShortcuts } from './components/KeyboardShortcuts'
import { HubProvider } from './contexts/HubContext'
import HubButton from './components/HubButton'
import HubPanel from './components/HubPanel'

const LAUNCH_KEY = 'sig_sys_launch_seen';

function App() {
  // Show launch animation only on first visit to homepage this session
  const [showLaunch, setShowLaunch] = useState(() => {
    if (typeof window === 'undefined') return false;
    const seen = sessionStorage.getItem(LAUNCH_KEY);
    // Only show on homepage (root path)
    return !seen && window.location.pathname === '/';
  });

  const [showShortcuts, setShowShortcuts] = useState(false);
  const [hubOpen, setHubOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  const toggleHub = useCallback(() => setHubOpen(prev => !prev), []);

  const handleLaunchComplete = useCallback(() => {
    sessionStorage.setItem(LAUNCH_KEY, '1');
    setShowLaunch(false);
  }, []);

  // Initialize dark theme on first load
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (!savedTheme) {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }, []);

  // Scroll to top on route change
  const location = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);

  // Header shadow on scroll
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Global keyboard shortcuts
  useKeyboardShortcuts({
    onShowShortcuts: useCallback(() => setShowShortcuts(prev => !prev), []),
  });

  return (
    <HubProvider>
    <div className="app">
      {/* Website launch animation (once per session, homepage only) */}
      {showLaunch && (
        <WebsiteLaunchAnimation onComplete={handleLaunchComplete} />
      )}

      {/* Skip to main content link for accessibility */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <header className={`app-header ${scrolled ? 'scrolled' : ''}`}>
        <Link to="/" className="logo">
          <h1>Signals & Systems</h1>
        </Link>
        <nav className="nav-links" role="navigation" aria-label="Main navigation">
          <Link to="/">Home</Link>
          <div className="header-toolbar">
            <button
              className="toolbar-button"
              onClick={() => setShowShortcuts(true)}
              aria-label="Keyboard shortcuts"
              title="Keyboard shortcuts (?)"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="4" width="20" height="16" rx="2" ry="2" />
                <path d="M6 8h.001" />
                <path d="M10 8h.001" />
                <path d="M14 8h.001" />
                <path d="M18 8h.001" />
                <path d="M8 12h.001" />
                <path d="M12 12h.001" />
                <path d="M16 12h.001" />
                <path d="M7 16h10" />
              </svg>
            </button>
            <HubButton isOpen={hubOpen} onToggle={toggleHub} />
            <ThemeToggle />
          </div>
        </nav>
      </header>

      <main id="main-content" className="app-main" role="main">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/simulation/:id" element={<SimulationPage />} />
          </Routes>
        </ErrorBoundary>
      </main>

      {/* Keyboard shortcuts modal */}
      <KeyboardShortcutsModal
        isOpen={showShortcuts}
        onClose={() => setShowShortcuts(false)}
      />

      {/* Hub panel */}
      <HubPanel isOpen={hubOpen} onClose={() => setHubOpen(false)} />

      <footer className="app-footer" role="contentinfo">
        <div className="footer-content">
          <span>Made by Shreyas Reddy</span>
        </div>
      </footer>
    </div>
    </HubProvider>
  )
}

export default App
