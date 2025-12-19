"""
Amplifier Feedback Simulator - Main Entry Point

Course: Signals and Systems (EE204T)
Professor: Ameer Mulla
Students: Prathamesh Nerpagar, Duggimpudi Shreyas Reddy

Project Description:
This simulation demonstrates the behavior of different amplifier configurations
including simple amplifiers, negative feedback systems, crossover distortion,
and compensated amplifier systems. The tool provides real-time visualization of:
- Input and output signal waveforms in time domain
- Gain stability analysis across power amplifier variations
- Linearity characteristics and distortion effects
- Audio processing and playback capabilities

The simulator helps understand how negative feedback improves amplifier stability,
reduces distortion, and maintains consistent gain despite component variations.
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox

import config
from core.audio_processor import AudioProcessor
from gui.gui import AmplifierGUI
from utils.helpers import ImageLoader, AudioPlayer


class AmplifierSimulator(QMainWindow):
    """Main application controller"""

    def __init__(self):
        super().__init__()

        # Setup window
        self.setWindowTitle(config.WINDOW_TITLE)
        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)

        # Initialize components
        self.audio_processor = AudioProcessor()
        self.audio_player = AudioPlayer()
        self.circuit_images = ImageLoader.load_images()

        # Create GUI
        self.gui = AmplifierGUI(
            self,
            self.audio_processor,
            self.audio_player,
            self.circuit_images
        )
        self.setCentralWidget(self.gui)

        # Connect callbacks
        self.gui.on_parameter_change = self.run_simulation
        self.gui.on_load_audio = self.load_audio
        self.gui.on_play_audio = self.play_audio
        self.gui.on_reset = self.reset_parameters

        # Initialize with test signal
        label_text = self.audio_processor.generate_test_signal('pure_sine')
        self.gui.update_file_label(label_text)
        self.run_simulation()
    
    def run_simulation(self):
        """Run the complete simulation pipeline"""
        self.gui.update_circuit_image()
        
        params = self.gui.get_parameters()
        self.audio_processor.process_audio(
            params['mode'], 
            params['K'], 
            params['F0'], 
            params['beta'], 
            params['VT']
        )
        
        self.gui.update_plots()
    
    def load_audio(self, file_path):
        """Load audio file"""
        if not file_path:
            return

        success, message, filename = self.audio_processor.load_audio_file(file_path)

        if success:
            self.gui.update_file_label(f"Loaded: {filename}")
            if "trimmed" in message.lower():
                QMessageBox.information(self, "Audio Trimmed", message)
            self.run_simulation()
        else:
            QMessageBox.critical(self, "Error Loading File", message)
            # Fall back to test signal
            label_text = self.audio_processor.generate_test_signal('pure_sine')
            self.gui.update_file_label(label_text)
            self.run_simulation()

    def play_audio(self):
        """Play the processed audio output"""
        success, audio_data, message = self.audio_processor.prepare_audio_for_playback()

        if success:
            self.audio_player.play(
                audio_data,
                self.audio_processor.sample_rate,
                self.gui.play_button,
                lambda error: QMessageBox.critical(self, "Playback Error", error)
            )
        else:
            QMessageBox.warning(self, "Cannot Play Audio", message)

    def reset_parameters(self):
        """Reset all parameters to defaults"""
        self.audio_player.stop()

        self.gui.set_parameters(
            config.K_DEFAULT,
            config.F0_DEFAULT,
            config.BETA_DEFAULT,
            'simple'
        )

        self.gui.reset_output_limit()

        label_text = self.audio_processor.generate_test_signal('pure_sine')
        self.gui.update_file_label(label_text)

        self.run_simulation()

    def closeEvent(self, event):
        """Clean up on application exit"""
        self.audio_player.stop()
        event.accept()


def main():
    """Main entry point"""
    print("Starting Amplifier Simulator...")
    print("Please ensure circuit diagram images are in the assets directory:")
    print("  - assets/simple.png")
    print("  - assets/feedback.png")
    print("  - assets/crossover.png")
    print("  - assets/compensated.png")
    print()

    app = QApplication(sys.argv)
    window = AmplifierSimulator()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
