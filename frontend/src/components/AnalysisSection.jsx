/**
 * AnalysisSection Component
 *
 * Displays analysis, observations, and exploration suggestions
 * below the interactive simulation area.
 */

import React from 'react'
import './AnalysisSection.css'

function AnalysisSection({ observations, tryThis, relatedConcepts }) {
  if (!observations && !tryThis && !relatedConcepts) return null

  return (
    <section className="analysis-section">
      <div className="analysis-header">
        <h2>Analysis & Exploration</h2>
      </div>

      <div className="analysis-body">
        {observations && observations.length > 0 && (
          <div className="analysis-block">
            <h3>Key Observations</h3>
            <ul className="analysis-list">
              {observations.map((obs, i) => (
                <li key={i}>{obs}</li>
              ))}
            </ul>
          </div>
        )}

        {tryThis && tryThis.length > 0 && (
          <div className="analysis-block">
            <h3>Try This</h3>
            <ul className="analysis-list try-this-list">
              {tryThis.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        )}

        {relatedConcepts && relatedConcepts.length > 0 && (
          <div className="analysis-block">
            <h3>Related Concepts</h3>
            <div className="related-tags">
              {relatedConcepts.map((concept, i) => (
                <span key={i} className="related-tag">{concept}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}

export default AnalysisSection
