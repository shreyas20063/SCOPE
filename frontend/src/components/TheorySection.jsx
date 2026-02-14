/**
 * TheorySection Component
 *
 * Displays the theory/educational content for a simulation.
 * Rendered above the interactive simulation area.
 * Uses Tiempos Text for warm, readable body text.
 */

import React from 'react'
import './TheorySection.css'

function TheorySection({ title, content, equations }) {
  if (!content && !equations) return null

  return (
    <section className="theory-section">
      <div className="theory-header">
        <h2>{title || 'Theory'}</h2>
      </div>

      <div className="theory-body">
        {content && (
          <div className="theory-text">
            {Array.isArray(content) ? (
              content.map((paragraph, i) => (
                <p key={i}>{paragraph}</p>
              ))
            ) : (
              <p>{content}</p>
            )}
          </div>
        )}

        {equations && equations.length > 0 && (
          <div className="theory-equations">
            {equations.map((eq, i) => (
              <div key={i} className="theory-equation">
                <code>{eq.formula}</code>
                {eq.description && <span>{eq.description}</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}

export default TheorySection
