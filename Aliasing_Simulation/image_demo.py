"""
Image Quantization Demonstration Window
Visualizes quantization effects on images with interactive bit depth control
"""

import numpy as np
import matplotlib.pyplot as plt
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from PIL import Image
from config import COLORS


class DemoWindow_Image(ctk.CTkToplevel):
    """Toplevel window for the Image Quantization demonstration."""
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.geometry("1160x790")
        self.configure(bg=COLORS['bg'])

        # Plot Frame
        self.plot_frame = ctk.CTkFrame(self, fg_color=COLORS['bg'])
        self.plot_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)

        # Matplotlib Figure and Canvas
        self.fig = plt.figure(figsize=(10.5, 6.5), facecolor=COLORS['bg'])
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill='both', expand=True, padx=8, pady=8)

        # Matplotlib Toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
        toolbar.pack(side='bottom', fill='x')

        # Control Panel Frame
        self.control_panel = ctk.CTkFrame(self, fg_color=COLORS['panel'], corner_radius=14)
        self.control_panel.pack(fill='x', padx=35, pady=(0, 22))

        # Bit Depth Slider
        self.slider_label = ctk.CTkLabel(
            self.control_panel, 
            text="Bit Depth:", 
            font=ctk.CTkFont(size=14)
        )
        self.slider_label.pack(side='left', padx=(20,10), pady=12)
        
        self.slider = ctk.CTkSlider(
            self.control_panel, 
            from_=1, 
            to=8, 
            number_of_steps=7, 
            width=300, 
            command=self.slider_update
        )
        self.slider.set(3)
        self.slider.pack(side='left', padx=(0,16), pady=16)
        
        self.slider_value_label = ctk.CTkLabel(
            self.control_panel, 
            text="3", 
            width=28, 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.slider_value_label.pack(side='left', padx=(0,24), pady=10)

        # Instance Variables & Image Loading
        self.bits = 3
        try:
            img = Image.open('test_image.jpg').convert('L')
            self.gray = np.array(img).astype(np.float32) / 255.0
            print("Loaded test_image.jpg")
        except Exception as e:
            print(f"Failed to load test_image.jpg ({e}). Generating fallback gradient.")
            x = np.linspace(0, 1, 256, dtype=np.float32)
            y = np.linspace(0, 1, 256, dtype=np.float32)
            X, Y = np.meshgrid(x, y)
            self.gray = (X + Y) / 2.0

        # Initialize plot elements
        self.ax_orig = self.ax_standard = self.ax_dither = self.ax_roberts = None
        self.ax_hist_std = self.ax_hist_dith = self.ax_hist_rob = self.ax_compare = None
        self.im_orig = self.im_standard = self.im_dither = self.im_roberts = None

        self._setup_plot()
        self._update_plot()

    def slider_update(self, value):
        """Callback for the bit depth slider."""
        self.bits = int(round(value))
        self.slider_value_label.configure(text=str(self.bits))
        self._update_plot()

    # Quantization Functions
    def uniform_quantize(self, image, bits):
        """Mid-tread quantizer for image range [0, 1]"""
        levels = 2 ** bits
        if levels <= 1:
            return np.clip(np.round(image), 0.0, 1.0)
        
        step = 1.0 / (levels - 1)
        quantized = np.round(image / step) * step
        return np.clip(quantized, 0.0, 1.0)

    def quantize_with_dither(self, image, bits):
        """Mid-tread quantizer with dither"""
        levels = 2 ** bits
        if levels <= 1:
            dither = np.random.uniform(-0.5, 0.5, size=image.shape).astype(np.float32)
            return np.clip(np.round(image + dither), 0.0, 1.0)
        
        step = 1.0 / (levels - 1)
        dither = np.random.uniform(-step/2.0, step/2.0, size=image.shape).astype(np.float32)
        quantized = np.round((image + dither) / step) * step
        return np.clip(quantized, 0.0, 1.0)

    def roberts_method(self, image, bits):
        """Mid-tread quantizer with subtractive dither (Robert's)"""
        levels = 2 ** bits
        if levels <= 1:
            dither = np.random.uniform(-0.5, 0.5, size=image.shape).astype(np.float32)
            quantized_output = np.clip(np.round(image + dither), 0.0, 1.0)
            final_image = quantized_output - dither
            return np.clip(final_image, 0.0, 1.0)

        step = 1.0 / (levels - 1)
        dither = np.random.uniform(-step/2.0, step/2.0, size=image.shape).astype(np.float32)
        quantized_output = np.round((image + dither) / step) * step
        final_image = quantized_output - dither
        return np.clip(final_image, 0.0, 1.0)

    def _setup_plot(self):
        """Initial setup of the Matplotlib plot axes."""
        plt.style.use('seaborn-v0_8-whitegrid')

        if self.ax_orig is None:
            gs = self.fig.add_gridspec(
                3, 3, 
                hspace=0.45, 
                wspace=0.3, 
                bottom=0.1, 
                top=0.95, 
                left=0.05, 
                right=0.97
            )
            self.ax_orig = self.fig.add_subplot(gs[0, 0])
            self.ax_standard = self.fig.add_subplot(gs[0, 1])
            self.ax_dither = self.fig.add_subplot(gs[0, 2])
            self.ax_roberts = self.fig.add_subplot(gs[1, 0])
            self.ax_hist_std = self.fig.add_subplot(gs[1, 1])
            self.ax_hist_dith = self.fig.add_subplot(gs[1, 2])
            self.ax_hist_rob = self.fig.add_subplot(gs[2, 0])
            self.ax_compare = self.fig.add_subplot(gs[2, 1:])
            self.axes_created = True
        else:
            self.axes_created = False

        all_axes = [
            self.ax_orig, self.ax_standard, self.ax_dither, self.ax_roberts,
            self.ax_hist_std, self.ax_hist_dith, self.ax_hist_rob, self.ax_compare
        ]

        for ax in all_axes:
            if ax is not None:
                if self.axes_created:
                    ax.set_facecolor(COLORS['bg'])
                    ax.grid(True, alpha=0.2, color=COLORS['grid'])
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.xaxis.label.set_color(COLORS['text_primary'])
                    ax.yaxis.label.set_color(COLORS['text_primary'])
                    ax.title.set_color(COLORS['text_primary'])
                    ax.tick_params(axis='x', colors=COLORS['text_secondary'])
                    ax.tick_params(axis='y', colors=COLORS['text_secondary'])
                else:
                    ax.clear()
                    ax.grid(True, alpha=0.2, color=COLORS['grid'])

        # Setup image displays
        cmap_val = 'gray'
        vmin_val, vmax_val = 0.0, 1.0
        
        if self.im_orig is None:
            self.im_orig = self.ax_orig.imshow(self.gray, cmap=cmap_val, vmin=vmin_val, vmax=vmax_val)
            self.im_standard = self.ax_standard.imshow(self.gray, cmap=cmap_val, vmin=vmin_val, vmax=vmax_val)
            self.im_dither = self.ax_dither.imshow(self.gray, cmap=cmap_val, vmin=vmin_val, vmax=vmax_val)
            self.im_roberts = self.ax_roberts.imshow(self.gray, cmap=cmap_val, vmin=vmin_val, vmax=vmax_val)
        else:
            self.im_orig.set_data(self.gray)
            self.im_standard.set_data(self.gray)
            self.im_dither.set_data(self.gray)
            self.im_roberts.set_data(self.gray)

        # Set titles
        self.ax_orig.set_title('Original (8-bit)', fontweight='bold', fontsize=11)
        self.ax_orig.axis('off')
        self.ax_standard.set_title('Standard Q', fontweight='bold', fontsize=11)
        self.ax_standard.axis('off')
        self.ax_dither.set_title('Dither', fontweight='bold', fontsize=11)
        self.ax_dither.axis('off')
        self.ax_roberts.set_title("Robert's", fontweight='bold', fontsize=11)
        self.ax_roberts.axis('off')

        self.ax_hist_std.set_title('Standard Histogram', fontsize=10, fontweight='bold')
        self.ax_hist_dith.set_title('Dither Histogram', fontsize=10, fontweight='bold')
        self.ax_hist_rob.set_title("Robert's Histogram", fontsize=10, fontweight='bold')
        self.ax_compare.set_title('Error Comparison', fontweight='bold', fontsize=12)

        for ax in [self.ax_hist_std, self.ax_hist_dith, self.ax_hist_rob]:
            ax.set_xlabel('Intensity', fontsize=9)
            ax.set_ylabel('Count', fontsize=9)

        self.ax_compare.set_xlabel('Quantization Method', fontweight='bold', fontsize=11)
        self.ax_compare.set_ylabel('Mean Squared Error (MSE)', fontweight='bold', fontsize=11)

        try:
            self.fig.tight_layout(rect=[0, 0.03, 1, 0.97])
        except ValueError:
            print("Warning: Initial tight_layout failed.")

    def _update_plot(self):
        """Updates the image plots based on current bit depth."""
        if not hasattr(self, 'ax_orig') or self.ax_orig is None:
            print("Error: Plot setup incomplete.")
            return

        bits = self.bits
        img = self.gray

        # Apply quantization
        standard = self.uniform_quantize(img, bits)
        dithered = self.quantize_with_dither(img, bits)
        roberts = self.roberts_method(img, bits)

        # Update Image Displays
        if self.im_standard:
            self.im_standard.set_data(standard)
        if self.ax_standard:
            self.ax_standard.set_title(
                f'Standard Q [{bits} bits]', 
                fontweight='bold', 
                fontsize=11, 
                color=COLORS['text_primary']
            )

        if self.im_dither:
            self.im_dither.set_data(dithered)
        if self.ax_dither:
            self.ax_dither.set_title(
                f'Dither [{bits} bits]', 
                fontweight='bold', 
                fontsize=11, 
                color=COLORS['text_primary']
            )

        if self.im_roberts:
            self.im_roberts.set_data(roberts)
        if self.ax_roberts:
            self.ax_roberts.set_title(
                f"Robert's [{bits} bits]", 
                fontweight='bold', 
                fontsize=11, 
                color=COLORS['text_primary']
            )

        # Update Histograms
        hist_axes = [self.ax_hist_std, self.ax_hist_dith, self.ax_hist_rob]
        hist_data = [standard, dithered, roberts]
        hist_colors = [COLORS['danger'], COLORS['success'], COLORS['accent']]
        hist_titles = ['Standard Histogram', 'Dither Histogram', "Robert's Histogram"]
        bins = min(max(2**(bits+1), 32), 256)

        for i, ax in enumerate(hist_axes):
            if ax is not None:
                ax.clear()
                ax.set_facecolor(COLORS['bg'])
                ax.grid(True, alpha=0.2, color=COLORS['grid'])
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                
                ax.hist(
                    hist_data[i].ravel(), 
                    bins=bins, 
                    color=hist_colors[i], 
                    alpha=0.75, 
                    edgecolor=COLORS['panel'], 
                    linewidth=0.5, 
                    range=(0,1)
                )
                
                ax.set_title(hist_titles[i], fontsize=10, fontweight='bold', color=COLORS['text_primary'])
                ax.set_xlabel('Intensity', fontsize=9, color=COLORS['text_primary'])
                ax.set_ylabel('Count', fontsize=9, color=COLORS['text_primary'])
                ax.set_xlim(0, 1)
                ax.tick_params(axis='x', colors=COLORS['text_secondary'])
                ax.tick_params(axis='y', colors=COLORS['text_secondary'])

        # Update Comparison Bar Chart
        ax_comp = self.ax_compare
        if ax_comp is not None:
            ax_comp.clear()
            ax_comp.set_facecolor(COLORS['bg'])
            ax_comp.grid(True, alpha=0.2, color=COLORS['grid'], axis='y')
            ax_comp.spines['top'].set_visible(False)
            ax_comp.spines['right'].set_visible(False)

            # Calculate MSE
            error_std = np.mean((img - standard) ** 2)
            error_dith = np.mean((img - dithered) ** 2)
            error_rob = np.mean((img - roberts) ** 2)

            methods = ['Standard Q', 'Dither', "Robert's"]
            mse = [error_std, error_dith, error_rob]
            bar_colors = [COLORS['danger'], COLORS['success'], COLORS['accent']]

            bars = ax_comp.bar(
                methods, 
                mse, 
                color=bar_colors, 
                alpha=0.8, 
                edgecolor=COLORS['panel'], 
                linewidth=1.0
            )

            # Add value labels
            for bar, val in zip(bars, mse):
                height = bar.get_height()
                ax_comp.text(
                    bar.get_x() + bar.get_width() / 2., 
                    height,
                    f'{val:.6f}',
                    ha='center', 
                    va='bottom',
                    fontsize=9, 
                    fontweight='bold',
                    color=COLORS['text_primary']
                )

            ax_comp.set_ylabel('Mean Squared Error (MSE)', fontweight='bold', fontsize=11, color=COLORS['text_primary'])
            ax_comp.set_xlabel('Quantization Method', fontweight='bold', fontsize=11, color=COLORS['text_primary'])
            ax_comp.set_title(f'Error Comparison ({bits} bits)', fontweight='bold', fontsize=12, color=COLORS['text_primary'])
            ax_comp.tick_params(axis='x', colors=COLORS['text_secondary'])
            ax_comp.tick_params(axis='y', colors=COLORS['text_secondary'])

            max_mse = max(mse) if mse else 0.0001
            ax_comp.set_ylim(0, max_mse * 1.25)

        try:
            self.fig.tight_layout(rect=[0, 0.03, 1, 0.97])
        except ValueError as e:
            print(f"Warning: tight_layout failed: {e}")

        self.canvas.draw_idle()