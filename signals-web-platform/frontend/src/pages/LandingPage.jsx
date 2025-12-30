import React, { useState, useEffect, useMemo } from 'react'
import axios from 'axios'
import SimulationCard from '../components/SimulationCard'

const CATEGORIES = ['All', 'Signal Processing', 'Circuits', 'Control Systems', 'Transforms', 'Optics']

function LandingPage() {
  const [simulations, setSimulations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')

  useEffect(() => {
    const fetchSimulations = async () => {
      try {
        const response = await axios.get('/api/simulations')
        setSimulations(response.data)
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

      const matchesCategory = selectedCategory === 'All' || sim.category === selectedCategory

      return matchesSearch && matchesCategory
    })
  }, [simulations, searchTerm, selectedCategory])

  if (loading) {
    return (
      <div className="landing-page">
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading simulations...</p>
        </div>
      </div>
    )
  }

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
      <section className="hero">
        <h2>Interactive Signal Processing Simulations</h2>
        <p>Explore and visualize signals & systems concepts through hands-on simulations</p>
      </section>

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
          {CATEGORIES.map((category) => (
            <button
              key={category}
              className={`category-btn ${selectedCategory === category ? 'active' : ''}`}
              onClick={() => setSelectedCategory(category)}
            >
              {category}
            </button>
          ))}
        </div>
      </section>

      <section className="results-info">
        <p>Showing {filteredSimulations.length} of {simulations.length} simulations</p>
      </section>

      {filteredSimulations.length === 0 ? (
        <div className="no-results">
          <span>🔎</span>
          <p>No simulations found matching your criteria</p>
          <button onClick={() => { setSearchTerm(''); setSelectedCategory('All'); }}>
            Clear filters
          </button>
        </div>
      ) : (
        <section className="simulations-grid">
          {filteredSimulations.map((sim, index) => (
            <SimulationCard
              key={sim.id}
              id={sim.id}
              name={sim.name}
              description={sim.description}
              category={sim.category}
              categoryColor={sim.category_info?.color}
              thumbnail={sim.thumbnail}
              animationDelay={index * 50}
            />
          ))}
        </section>
      )}
    </div>
  )
}

export default LandingPage
