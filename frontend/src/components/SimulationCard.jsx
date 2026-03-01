import React from 'react'
import { Link } from 'react-router-dom'

function SimulationCard({ id, name, description, category, categoryColor, thumbnail }) {
  const color = categoryColor || '#64748b'

  return (
    <Link
      to={`/simulation/${id}`}
      className="simulation-card"
      style={{ '--card-accent': color }}
    >
      <div className="card-accent-line" />
      <div className="card-header">
        <span className="card-thumbnail">{thumbnail}</span>
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
