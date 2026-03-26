import React, { useState, useEffect, useMemo, useCallback } from 'react'
import api from '../services/api'
import SimulationCard from '../components/SimulationCard'
import HeroCanvas from '../components/HeroCanvas'
import { useIntersectionObserver } from '../hooks/useIntersectionObserver'

const SECTIONS = [
  { key: 'tools', name: 'Design Pipeline', subtitle: 'TF input \u2192 Block diagrams \u2192 SFG \u2192 Stability analysis \u2192 Controller design \u2192 3D visualization', color: '#14b8a6' },
  { key: 'analytical', name: 'Analytical Tools', subtitle: 'Interactive solvers, explorers, and analysis workbenches', color: '#3b82f6' },
  { key: 'simulations', name: 'System Simulations', subtitle: 'Physical systems \u2014 circuits, motors, pendulums, optics', color: '#8b5cf6' },
  { key: 'signals', name: 'Signal Explorations', subtitle: 'Signals, sampling, Fourier, Z-transforms, Laplace, and more', color: '#06b6d4' },
]

function ScrollReveal({ children, delay = 0 }) {
  const [ref, isVisible] = useIntersectionObserver({ threshold: 0.05 })
  return (
    <div
      ref={ref}
      className={isVisible ? 'scroll-reveal visible' : 'scroll-reveal'}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  )
}

function SkeletonCard({ index }) {
  return (
    <div className="skeleton-card" style={{ animationDelay: `${index * 80}ms` }}>
      <div className="skeleton-card-header">
        <div className="skeleton-line skeleton-thumbnail" />
        <div className="skeleton-line skeleton-badge" />
      </div>
      <div className="skeleton-line skeleton-h3" />
      <div className="skeleton-line skeleton-p" />
      <div className="skeleton-line skeleton-p short" />
      <div className="skeleton-card-footer">
        <div className="skeleton-line skeleton-btn" />
      </div>
    </div>
  )
}

function SectionHeader({ section, count }) {
  return (
    <div className="section-header" style={{ '--section-color': section.color }}>
      <div className="section-header-text">
        <h3 className="section-title">{section.name}</h3>
        <p className="section-subtitle">{section.subtitle}</p>
      </div>
      <span className="section-count">{count}</span>
    </div>
  )
}

function LandingPage() {
  const [simulations, setSimulations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedSection, setSelectedSection] = useState(null)
  const [mousePos, setMousePos] = useState({ x: -1, y: -1 })

  const handleHeroMouse = useCallback((e) => {
    const rect = e.currentTarget.getBoundingClientRect()
    setMousePos({
      x: (e.clientX - rect.left) / rect.width,
      y: (e.clientY - rect.top) / rect.height,
    })
  }, [])

  const handleHeroLeave = useCallback(() => {
    setMousePos({ x: -1, y: -1 })
  }, [])

  useEffect(() => {
    const fetchSimulations = async () => {
      try {
        const result = await api.getSimulations()
        if (result.success) {
          setSimulations(result.data)
        } else {
          setError(result.error || 'Failed to load simulations')
        }
        setLoading(false)
      } catch (err) {
        console.error('Error fetching simulations:', err)
        setError('Failed to load simulations. Is the backend running?')
        setLoading(false)
      }
    }

    fetchSimulations()
  }, [])

  const filteredSimulations = useMemo(() => {
    return simulations.filter((sim) => {
      const matchesSearch = !searchTerm ||
        sim.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        sim.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        sim.tags?.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))

      const matchesSection = !selectedSection || sim.section === selectedSection

      return matchesSearch && matchesSection
    })
  }, [simulations, searchTerm, selectedSection])

  // Group filtered sims by section, sorted by section_order within each
  const groupedSections = useMemo(() => {
    const groups = {}
    for (const sim of filteredSimulations) {
      const key = sim.section || 'signals'
      if (!groups[key]) groups[key] = []
      groups[key].push(sim)
    }
    // Sort within each section by section_order
    for (const key in groups) {
      groups[key].sort((a, b) => (a.section_order || 99) - (b.section_order || 99))
    }
    // Return sections in defined order, skipping empty ones
    return SECTIONS
      .filter(s => groups[s.key]?.length > 0)
      .map(s => ({ ...s, sims: groups[s.key] }))
  }, [filteredSimulations])

  if (error) {
    return (
      <div className="landing-page">
        <div className="error-container">
          <span className="error-icon">⚠️</span>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="landing-page">
      <section className="hero" onMouseMove={handleHeroMouse} onMouseLeave={handleHeroLeave}>
        <HeroCanvas mousePos={mousePos} />
        <h2>SCOPE</h2>
        <p>Interactive simulations for learning signal processing, control systems, and transforms.</p>
        <div className="hero-accent" />
      </section>

      <ScrollReveal>
        <section className="filters-section">
          <div className="search-bar">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Search simulations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <button className="clear-btn" onClick={() => setSearchTerm('')}>×</button>
            )}
          </div>

          <div className="category-filters">
            <button
              className={`category-btn ${!selectedSection ? 'active' : ''}`}
              style={!selectedSection ? { '--category-color': 'var(--primary-color)' } : undefined}
              onClick={() => setSelectedSection(null)}
            >
              All
            </button>
            {SECTIONS.map((sec) => (
              <button
                key={sec.key}
                className={`category-btn ${selectedSection === sec.key ? 'active' : ''}`}
                style={selectedSection === sec.key ? { '--category-color': sec.color } : undefined}
                onClick={() => setSelectedSection(selectedSection === sec.key ? null : sec.key)}
              >
                {sec.name}
              </button>
            ))}
          </div>
        </section>
      </ScrollReveal>

      <section className="results-info">
        <p>Showing {filteredSimulations.length} of {simulations.length} simulations</p>
      </section>

      {loading ? (
        <section className="simulations-grid">
          {Array.from({ length: 9 }).map((_, i) => (
            <SkeletonCard key={i} index={i} />
          ))}
        </section>
      ) : filteredSimulations.length === 0 ? (
        <div className="no-results">
          <span>🔎</span>
          <p>No simulations found matching your criteria</p>
          <button onClick={() => { setSearchTerm(''); setSelectedSection(null); }}>
            Clear filters
          </button>
        </div>
      ) : (
        <div className="sections-container">
          {groupedSections.map((section) => (
            <ScrollReveal key={section.key}>
              <div className="section-group">
                <SectionHeader section={section} count={section.sims.length} />
                <div className="simulations-grid">
                  {section.sims.map((sim, index) => (
                    <ScrollReveal key={sim.id} delay={(index % 6) * 60}>
                      <SimulationCard
                        id={sim.id}
                        name={sim.name}
                        description={sim.description}
                        category={sim.category}
                        categoryColor={sim.category_info?.color}
                        thumbnail={sim.thumbnail}
                      />
                    </ScrollReveal>
                  ))}
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      )}
    </div>
  )
}

export default LandingPage
