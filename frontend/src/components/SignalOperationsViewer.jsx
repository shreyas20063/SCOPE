/**
 * SignalOperationsViewer
 *
 * Custom viewer for the Signal Operations Playground simulation.
 * Renders plots via PlotDisplay and adds quiz answer buttons
 * when in quiz mode.
 */

import React, { useCallback } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/SignalOperationsViewer.css';

function SignalOperationsViewer({ metadata, plots, onButtonClick, isUpdating }) {
  const quiz = metadata?.quiz;
  const isQuizMode = metadata?.mode === 'quiz' && quiz;

  const handleAnswerClick = useCallback((index) => {
    if (quiz?.answered || isUpdating) return;
    onButtonClick('check_answer', { answer_index: index });
  }, [onButtonClick, quiz?.answered, isUpdating]);

  return (
    <div className="signal-operations-viewer">
      {/* Formula display */}
      {metadata?.formula_display && metadata.mode === 'explore' && (
        <div className="signal-ops-formula">
          <span className="formula-label">Transform:</span>
          <span className="formula-text">{metadata.formula_display}</span>
        </div>
      )}

      {/* Plots */}
      <PlotDisplay plots={plots} isLoading={false} />

      {/* Quiz answer buttons */}
      {isQuizMode && quiz.options && (
        <div className="quiz-panel">
          <div className="quiz-prompt" role="status" aria-live="polite">
            {quiz.answered
              ? (quiz.correct
                  ? <span className="quiz-result correct">Correct!</span>
                  : <span className="quiz-result incorrect">Incorrect — the answer was: <strong>{quiz.answer}</strong></span>
                )
              : <span className="quiz-instruction">Select the correct transformation:</span>
            }
          </div>
          <div className="quiz-options">
            {quiz.options.map((option, idx) => {
              let className = 'quiz-option-btn';
              if (quiz.answered) {
                if (option === quiz.answer) {
                  className += ' correct';
                } else {
                  className += ' disabled';
                }
              }
              return (
                <button
                  key={idx}
                  className={className}
                  onClick={() => handleAnswerClick(idx)}
                  disabled={isUpdating || quiz.answered}
                  aria-label={`Option ${idx + 1}: ${option}`}
                >
                  {option}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default SignalOperationsViewer;
