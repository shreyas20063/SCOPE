"""
Results Display Components for Audio Fourier Analysis
Handles display of audio analysis results, plots, and metrics
"""

import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox, QGridLayout)


class AudioResultsDisplay:
    """
    Manages display of Fourier analysis results for audio signals
    """

    def __init__(self, plotter):
        self.plotter = plotter
        self.setup_tabs()

        self.current_signal1 = None
        self.current_signal2 = None
        self.current_results = {}
        self.sample_rate = 44100
        self.name1 = "Audio 1"
        self.name2 = "Audio 2"

    def setup_tabs(self):
        """Setup audio analysis tabs"""
        self.audio1_tab = QWidget()
        layout1 = QVBoxLayout(self.audio1_tab)
        self.audio1_fig, self.audio1_canvas = self.plotter.create_figure_canvas()
        layout1.addWidget(self.audio1_canvas)

        metrics_group1 = QGroupBox("Audio 1 Quality Metrics")
        metrics_layout1 = QGridLayout(metrics_group1)
        self.audio1_mse_label = QLabel("MSE: -")
        self.audio1_corr_label = QLabel("Correlation: -")
        self.audio1_snr_label = QLabel("SNR (dB): -")
        metrics_layout1.addWidget(QLabel("Mean Squared Error:"), 0, 0)
        metrics_layout1.addWidget(self.audio1_mse_label, 0, 1)
        metrics_layout1.addWidget(QLabel("Correlation:"), 1, 0)
        metrics_layout1.addWidget(self.audio1_corr_label, 1, 1)
        metrics_layout1.addWidget(QLabel("SNR (dB):"), 2, 0)
        metrics_layout1.addWidget(self.audio1_snr_label, 2, 1)
        layout1.addWidget(metrics_group1)

        self.audio2_tab = QWidget()
        layout2 = QVBoxLayout(self.audio2_tab)
        self.audio2_fig, self.audio2_canvas = self.plotter.create_figure_canvas()
        layout2.addWidget(self.audio2_canvas)

        metrics_group2 = QGroupBox("Audio 2 Quality Metrics")
        metrics_layout2 = QGridLayout(metrics_group2)
        self.audio2_mse_label = QLabel("MSE: -")
        self.audio2_corr_label = QLabel("Correlation: -")
        self.audio2_snr_label = QLabel("SNR (dB): -")
        metrics_layout2.addWidget(QLabel("Mean Squared Error:"), 0, 0)
        metrics_layout2.addWidget(self.audio2_mse_label, 0, 1)
        metrics_layout2.addWidget(QLabel("Correlation:"), 1, 0)
        metrics_layout2.addWidget(self.audio2_corr_label, 1, 1)
        metrics_layout2.addWidget(QLabel("SNR (dB):"), 2, 0)
        metrics_layout2.addWidget(self.audio2_snr_label, 2, 1)
        layout2.addWidget(metrics_group2)

        self.hybrid_tab = QWidget()
        layout3 = QVBoxLayout(self.hybrid_tab)
        self.hybrid_fig, self.hybrid_canvas = self.plotter.create_figure_canvas()
        layout3.addWidget(self.hybrid_canvas)

        hybrid_group = QGroupBox("Hybrid Signal Analysis")
        hybrid_layout = QGridLayout(hybrid_group)
        self.hybrid1_corr_label = QLabel("Hybrid 1 → Audio 2: -")
        self.hybrid2_corr_label = QLabel("Hybrid 2 → Audio 1: -")
        hybrid_layout.addWidget(QLabel("Correlations:"), 0, 0, 1, 2)
        hybrid_layout.addWidget(self.hybrid1_corr_label, 1, 0, 1, 2)
        hybrid_layout.addWidget(self.hybrid2_corr_label, 2, 0, 1, 2)

        explanation = QLabel(
            "Hybrid signals demonstrate phase importance:\n"
            "• Mag1 + Phase2 follows the structure of Audio 2\n"
            "• Mag2 + Phase1 follows the structure of Audio 1\n"
            "Phase primarily governs perceived structure over magnitude."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("QLabel { background-color: #f1f4ff; color: #000000; padding: 10px; border-radius: 5px; }")
        hybrid_layout.addWidget(explanation, 3, 0, 1, 2)
        layout3.addWidget(hybrid_group)

    def update_results(self, signal1, signal2, results, sample_rate,
                       name1="Audio 1", name2="Audio 2"):
        """
        Update all audio displays with new results
        """
        self.current_signal1 = signal1
        self.current_signal2 = signal2
        self.current_results = results
        self.sample_rate = sample_rate
        self.name1 = name1
        self.name2 = name2

        self._update_audio_display(
            fig=self.audio1_fig,
            canvas=self.audio1_canvas,
            signal=signal1,
            magnitude=results['mag1_display'],
            magnitude_ref=results['mag1_orig'],
            phase=results['phase1_display'],
            reconstructed=results['signal1_recon'],
            title_prefix=f"{self.name1} | "
        )
        self._update_audio_display(
            fig=self.audio2_fig,
            canvas=self.audio2_canvas,
            signal=signal2,
            magnitude=results['mag2_display'],
            magnitude_ref=results['mag2_orig'],
            phase=results['phase2_display'],
            reconstructed=results['signal2_recon'],
            title_prefix=f"{self.name2} | "
        )
        self._update_hybrid_display(results)
        self._update_metrics(results)

    def _update_audio_display(self, fig, canvas, signal, magnitude, phase, reconstructed,
                              title_prefix, magnitude_ref):
        self.plotter.plot_audio_components(
            fig,
            signal,
            magnitude,
            phase,
            reconstructed,
            self.sample_rate,
            title_prefix=title_prefix,
            magnitude_ref=magnitude_ref
        )
        canvas.draw()

    def _update_hybrid_display(self, results):
        self.plotter.plot_audio_hybrid_comparison(
            self.hybrid_fig,
            self.current_signal1,
            self.current_signal2,
            results['hybrid_mag1_phase2'],
            results['hybrid_mag2_phase1'],
            self.sample_rate,
            name1=self.name1,
            name2=self.name2
        )
        self.hybrid_canvas.draw()

        corr1 = np.corrcoef(results['hybrid_mag1_phase2'], self.current_signal2)[0, 1]
        corr2 = np.corrcoef(results['hybrid_mag2_phase1'], self.current_signal1)[0, 1]
        self.hybrid1_corr_label.setText(f"Hybrid 1 → {self.name2}: {corr1:.4f}")
        self.hybrid2_corr_label.setText(f"Hybrid 2 → {self.name1}: {corr2:.4f}")

    def _update_metrics(self, results):
        quality1 = results['quality1']
        quality2 = results['quality2']

        self.audio1_mse_label.setText(f"{quality1['mse']:.6f}")
        self.audio1_corr_label.setText(f"{quality1['correlation']:.4f}")
        snr1 = quality1['snr_db']
        self.audio1_snr_label.setText(f"{snr1:.2f}" if np.isfinite(snr1) else "∞")

        self.audio2_mse_label.setText(f"{quality2['mse']:.6f}")
        self.audio2_corr_label.setText(f"{quality2['correlation']:.4f}")
        snr2 = quality2['snr_db']
        self.audio2_snr_label.setText(f"{snr2:.2f}" if np.isfinite(snr2) else "∞")
