"""
Main Application Window for Signal Processing Lab
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import COLORS
from gui.aliasing_demo import DemoWindow_Aliasing
from gui.quantization_demo import DemoWindow_Quantization
from gui.image_demo import DemoWindow_Image


class SignalProcessingLab(QMainWindow):
    """Main application window for the Signal Processing Lab."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aliasing and Quantization Simulator")
        self.resize(1400, 850)
        self.setMinimumSize(1200, 800)

        # Set main window background
        self.setStyleSheet(f"background-color: {COLORS['bg']};")

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 20, 40, 20)
        main_layout.setSpacing(20)

        # Add title
        title = QLabel("Aliasing and Quantization Simulator")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 26px;
                font-weight: bold;
            }}
        """)
        main_layout.addWidget(title)

        # Create container for cards
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['panel']};
                border: 1px solid {COLORS['border']};
                border-radius: 15px;
            }}
        """)
        container_layout = QGridLayout(container)
        container_layout.setSpacing(15)
        container_layout.setContentsMargins(15, 15, 15, 15)

        # Information for the three demo cards
        cards_info = [
            {
                "title": "Audio Aliasing Demo",
                "desc": "Understand the Nyquist theorem and aliasing effects when sampling below the Nyquist rate.",
                "color": COLORS['accent'],
                "command": self.launch_aliasing_demo
            },
            {
                "title": "Audio Quantization Demo",
                "desc": "Compare three quantization techniques: Standard, Dither, and Robert's Method.",
                "color": COLORS['success'],
                "command": self.launch_quantization_demo
            },
            {
                "title": "Image Quantization Demo",
                "desc": "Visualize quantization effects on images with interactive bit depth control.",
                "color": COLORS['warning'],
                "command": self.launch_image_demo
            }
        ]

        # Create and place each card in the grid
        for i, card in enumerate(cards_info):
            self.create_card(container, container_layout, card, i)

        main_layout.addWidget(container, 1)

        # Footer Frame for file info and status
        footer_frame = QFrame()
        footer_frame.setStyleSheet(f"background-color: {COLORS['bg']};")
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(0, 0, 0, 0)

        # Required files label
        footer_label = QLabel("Sample files included: audio_sample.wav | test_image.jpg")
        footer_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        footer_layout.addWidget(footer_label)

        footer_layout.addStretch()

        # Status indicator label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px; font-weight: bold;")
        footer_layout.addWidget(self.status_label)

        main_layout.addWidget(footer_frame)

        # Store demo windows
        self.demo_windows = []

    def create_card(self, parent, layout, card_info, index):
        """Creates a single demo launch card."""
        card = QFrame(parent)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 15px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(15, 15, 15, 15)

        # Card Title
        lbl_title = QLabel(card_info["title"])
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 18px;
                font-weight: bold;
            }}
        """)
        card_layout.addWidget(lbl_title)

        # Card Description
        lbl_desc = QLabel(card_info["desc"])
        lbl_desc.setAlignment(Qt.AlignLeft)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 13px;
            }}
        """)
        lbl_desc.setMaximumWidth(300)
        card_layout.addWidget(lbl_desc)

        card_layout.addStretch()

        # Launch Button
        btn = QPushButton("Launch Demo")
        btn.setMinimumWidth(140)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {card_info["color"]};
                color: white;
                border: none;
                padding: 10px;
                font-weight: bold;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_dark']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['accent_dark']};
            }}
        """)
        btn.clicked.connect(card_info["command"])
        card_layout.addWidget(btn, alignment=Qt.AlignCenter)

        layout.addWidget(card, 0, index)

    def update_status(self, text, color_key='success'):
        """Updates the status label text and color."""
        color_map = {
            'success': COLORS['success'],
            'warning': COLORS['warning'],
            'danger': COLORS['danger'],
            'info': COLORS['accent']
        }
        icon_map = {
            'success': '',
            'warning': '',
            'danger': '',
            'info': ''
        }
        self.status_label.setText(f"{icon_map.get(color_key, '')} {text}")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color_map.get(color_key, COLORS['text_primary'])};
                font-size: 12px;
                font-weight: bold;
            }}
        """)

    # --- Launch Methods for Demos ---
    def launch_aliasing_demo(self):
        """Launches the Audio Aliasing demo window."""
        self.update_status("Loading Aliasing Demo...", 'info')
        demo = DemoWindow_Aliasing(title="Audio Aliasing Demonstration")
        demo.show()
        self.demo_windows.append(demo)
        self.update_status("Aliasing Demo Running", 'success')

    def launch_quantization_demo(self):
        """Launches the Audio Quantization demo window."""
        self.update_status("Loading Quantization Demo...", 'info')
        demo = DemoWindow_Quantization(title="Audio Quantization Demonstration")
        demo.show()
        self.demo_windows.append(demo)
        self.update_status("Quantization Demo Running", 'success')

    def launch_image_demo(self):
        """Launches the Image Quantization demo window."""
        self.update_status("Loading Image Demo...", 'info')
        demo = DemoWindow_Image(title="Image Quantization Demonstration")
        demo.show()
        self.demo_windows.append(demo)
        self.update_status("Image Demo Running", 'success')
