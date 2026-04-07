import React from 'react'
import { Link } from 'react-router-dom'

function SimulationCard({ id, name, description, category, categoryColor, thumbnail, viewMode }) {
  const color = categoryColor || '#64748b'

  if (viewMode === 'compact') {
    return (
      <Link
        to={`/simulation/${id}`}
        className="simulation-card compact-card"
        style={{ '--card-accent': color }}
      >
        <div className="compact-card-accent" style={{ backgroundColor: color }} />
        <span className="compact-card-name">{name}</span>
      </Link>
    )
  }

  if (viewMode === 'list') {
    return (
      <Link
        to={`/simulation/${id}`}
        className="simulation-card list-card"
        style={{ '--card-accent': color }}
      >
        <div className="list-card-accent" style={{ backgroundColor: color }} />
        <span
          className="category-badge"
          style={{ backgroundColor: color }}
        >
          {category}
        </span>
        <div className="list-card-text">
          <h3>{name}</h3>
          <p>{description}</p>
        </div>
        <span className="launch-btn">Launch →</span>
      </Link>
    )
  }

  return (
    <Link
      to={`/simulation/${id}`}
      className="simulation-card"
      style={{ '--card-accent': color }}
    >
      <div className="card-accent-line" />
      <div className="card-header">
        <span
          className="category-badge"
          style={{ backgroundColor: color }}
        >
          {category}
        </span>
      </div>

      <div className="card-content">
        <h3>{name}</h3>
        <p>{description}</p>
      </div>

      <div className="card-footer">
        <span className="launch-btn">Launch →</span>
      </div>
    </Link>
  )
}

export default SimulationCard
