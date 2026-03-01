import React, { useState, useEffect, useMemo, useCallback } from 'react'
import api from '../services/api'
import SimulationCard from '../components/SimulationCard'
import HeroCanvas from '../components/HeroCanvas'
import { useIntersectionObserver } from '../hooks/useIntersectionObserver'

const CATEGORIES = [
  { name: 'All', color: null },
  { name: 'Signal Processing', color: '#06b6d4' },
  { name: 'Circuits', color: '#8b5cf6' },
  { name: 'Control Systems', color: '#f59e0b' },
  { name: 'Transforms', color: '#10b981' },
  { name: 'Optics', color: '#ec4899' },
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

function LandingPage() {
  const [simulations, setSimulations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState(CATEGORIES[0])
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
      const matchesSearch = sim.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        sim.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        sim.tags?.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))

      const matchesCategory = selectedCategory.name === 'All' || sim.category === selectedCategory.name

      return matchesSearch && matchesCategory
    })
  }, [simulations, searchTerm, selectedCategory])

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
        <h2>Signals & Systems</h2>
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
            {CATEGORIES.map((cat) => (
              <button
                key={cat.name}
                className={`category-btn ${selectedCategory.name === cat.name ? 'active' : ''}`}
                style={selectedCategory.name === cat.name && cat.color ? { '--category-color': cat.color } : undefined}
                onClick={() => setSelectedCategory(cat)}
              >
                {cat.name}
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
          <button onClick={() => { setSearchTerm(''); setSelectedCategory(CATEGORIES[0]); }}>
            Clear filters
          </button>
        </div>
      ) : (
        <section className="simulations-grid">
          {filteredSimulations.map((sim, index) => (
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
        </section>
      )}
    </div>
  )
}

export default LandingPage
