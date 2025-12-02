"""
Main Application Window for Signal Processing Lab
"""

import customtkinter as ctk
from config import COLORS, setup_appearance
from aliasing_demo import DemoWindow_Aliasing
from quantization_demo import DemoWindow_Quantization
from image_demo import DemoWindow_Image

# Setup appearance
setup_appearance()


class SignalProcessingLab(ctk.CTk):
    """Main application window for the Signal Processing Lab."""
    def __init__(self):
        super().__init__()
        self.title("🎵 Aliasing and Quantization Simulator")
        self.geometry("1400x850")
        self.minsize(1200, 800)
        self.configure(bg=COLORS['bg'])
        self._setup_UI()

    def _setup_UI(self):
        """Sets up the main user interface elements."""
        # Main Title Label
        title = ctk.CTkLabel(
            self, 
            text="Aliasing and Quantization Simulator",
            font=ctk.CTkFont(size=26, weight="bold"), 
            text_color=COLORS['text_primary']
        )
        title.pack(pady=(20, 20))

        # Main Container Frame for Cards
        container = ctk.CTkFrame(
            self, 
            fg_color=COLORS['panel'], 
            corner_radius=15, 
            border_width=1, 
            border_color=COLORS['border']
        )
        container.pack(fill='both', expand=True, padx=40, pady=20)
        container.grid_columnconfigure((0, 1, 2), weight=1, uniform='col')
        container.grid_rowconfigure(0, weight=1)

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
            self.create_card(container, card, i)

        # Footer Frame for file info and status
        footer_frame = ctk.CTkFrame(self, fg_color=COLORS['bg'])
        footer_frame.pack(fill='x', padx=40, pady=(0, 15))

        # Required files label
        footer_label = ctk.CTkLabel(
            footer_frame,
            text="📁 Sample files included: audio_sample.wav | test_image.jpg",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        )
        footer_label.pack(side='left')

        # Status indicator label
        self.status_label = ctk.CTkLabel(
            footer_frame,
            text="✅ Ready",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['success']
        )
        self.status_label.pack(side='right')

    def create_card(self, parent, card_info, index):
        """Creates a single demo launch card."""
        card = ctk.CTkFrame(
            parent, 
            fg_color=COLORS['bg'], 
            corner_radius=12, 
            border_width=1, 
            border_color=COLORS['border']
        )
        card.grid(row=0, column=index, padx=15, pady=15, sticky='nsew')

        # Card Title
        lbl_title = ctk.CTkLabel(
            card, 
            text=card_info["title"],
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text_primary']
        )
        lbl_title.pack(pady=(15, 10), padx=15)

        # Card Description
        lbl_desc = ctk.CTkLabel(
            card, 
            text=card_info["desc"],
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary'],
            wraplength=300, 
            justify='left'
        )
        lbl_desc.pack(padx=15, pady=(0, 25))

        # Launch Button
        btn = ctk.CTkButton(
            card, 
            text="▶ Launch Demo",
            width=140,
            fg_color=card_info["color"],
            hover_color=COLORS['accent_dark'],
            corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            command=card_info["command"]
        )
        btn.pack(pady=(0, 15))

    def update_status(self, text, color_key='success'):
        """Updates the status label text and color."""
        color_map = {
            'success': COLORS['success'], 
            'warning': COLORS['warning'], 
            'danger': COLORS['danger'], 
            'info': COLORS['accent']
        }
        icon_map = {
            'success': '✅', 
            'warning': '⚠️', 
            'danger': '❌', 
            'info': 'ℹ️'
        }
        self.status_label.configure(
            text=f"{icon_map.get(color_key, '')} {text}",
            text_color=color_map.get(color_key, COLORS['text_primary'])
        )
        self.status_label.update_idletasks()

    # --- Launch Methods for Demos ---
    def launch_aliasing_demo(self):
        """Launches the Audio Aliasing demo window."""
        self.update_status("Loading Aliasing Demo...", 'info')
        DemoWindow_Aliasing(self, "📊 Audio Aliasing Demonstration")
        self.update_status("Aliasing Demo Running", 'success')

    def launch_quantization_demo(self):
        """Launches the Audio Quantization demo window."""
        self.update_status("Loading Quantization Demo...", 'info')
        DemoWindow_Quantization(self, "🎚️ Audio Quantization Demonstration")
        self.update_status("Quantization Demo Running", 'success')

    def launch_image_demo(self):
        """Launches the Image Quantization demo window."""
        self.update_status("Loading Image Demo...", 'info')
        DemoWindow_Image(self, "🖼️ Image Quantization Demonstration")
        self.update_status("Image Demo Running", 'success')