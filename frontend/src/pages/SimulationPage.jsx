/**
 * SimulationPage
 *
 * Page component for displaying individual simulations.
 * Layout: Theory Section → Interactive Simulation → Analysis Section
 */

import React, { useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { useSimulation } from '../hooks/useSimulation';
import SimulationViewer from '../components/SimulationViewer';
import TheorySection from '../components/TheorySection';
import AnalysisSection from '../components/AnalysisSection';
import Spinner from '../components/Spinner';
import ErrorMessage from '../components/ErrorMessage';
import { decodeParams } from '../utils/urlParams';

function SimulationPage() {
  const { id } = useParams();
  const location = useLocation();

  const {
    simulation,
    currentParams,
    plots,
    metadata,
    isLoading,
    isUpdating,
    error,
    isRunning,
    updateParam,
    resetToDefaults,
    handleButtonAction,
    stepForward,
    stepBackward,
    setParamsFromUrl,
  } = useSimulation(id);

  // Load parameters from URL on mount
  useEffect(() => {
    if (simulation?.controls && location.search) {
      // Build defaults object from simulation controls
      const defaults = {};
      simulation.controls.forEach(control => {
        if (control.type === 'slider' || control.type === 'number') {
          defaults[control.id] = control.default ?? control.min;
        } else if (control.type === 'checkbox') {
          defaults[control.id] = control.default ?? false;
        } else if (control.type === 'dropdown') {
          defaults[control.id] = control.default ?? control.options?.[0]?.value;
        }
      });

      const urlParams = decodeParams(location.search, defaults);
      if (Object.keys(urlParams).length > 0 && setParamsFromUrl) {
        setParamsFromUrl(urlParams);
      }
    }
  }, [simulation?.controls, location.search, setParamsFromUrl]);

  // Show loading state
  if (isLoading && !simulation) {
    return (
      <div className="simulation-page">
        <Spinner message="Loading simulation..." size="large" fullScreen />
      </div>
    );
  }

  // Show error state
  if (error && !simulation) {
    return (
      <div className="simulation-page">
        <ErrorMessage
          error={error}
          title="Failed to load simulation"
          showBackButton
        />
      </div>
    );
  }

  // Extract theory and analysis data from simulation catalog
  const theory = simulation?.theory;
  const analysis = simulation?.analysis;

  // Show simulation viewer with theory + analysis sections
  return (
    <div className="simulation-page">
      {/* Theory Section — scrollable content above the sim */}
      {theory && (
        <TheorySection
          title={theory.title}
          content={theory.content}
          equations={theory.equations}
        />
      )}

      {/* Interactive Simulation */}
      <SimulationViewer
        simulation={simulation}
        plots={plots}
        metadata={metadata}
        currentParams={currentParams}
        onParamChange={updateParam}
        onReset={resetToDefaults}
        onButtonClick={handleButtonAction}
        onStepForward={stepForward}
        onStepBackward={stepBackward}
        isLoading={isLoading}
        isUpdating={isUpdating}
        isRunning={isRunning}
      />

      {/* Analysis Section — scrollable content below the sim */}
      {analysis && (
        <AnalysisSection
          observations={analysis.observations}
          tryThis={analysis.try_this}
          relatedConcepts={analysis.related_concepts}
        />
      )}
    </div>
  );
}

export default SimulationPage;
