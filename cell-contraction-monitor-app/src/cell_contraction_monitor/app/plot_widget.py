# cell-contraction-monitor-app/src/cell_contraction_monitor/app/plot_widget.py
import tkinter as tk
from tkinter import ttk
from typing import Optional, Union
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import matplotlib.pyplot as plt


class PlotFrame(ttk.Frame):
    """A frame that embeds a Matplotlib plot for displaying cell contraction data.

    This widget provides real-time plotting capabilities for cell size measurements
    and other quantitative analysis results from the processing pipeline.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.figure = Figure(
            figsize=(6, 4),
            dpi=100,
            # facecolor="#2d3436",
            # edgecolor="#2d3436"
        )
        self.ax = self.figure.add_subplot(
            111,
            # facecolor="#36393f"
        )
        self.ax.set_title("Cell Contraction Analysis",
                          #   color="#ffffff",
                          fontsize=12,
                          fontweight='bold')
        self.ax.set_xlabel("Frame Index",
                           #    color="#ffffff"
                           )
        self.ax.set_ylabel("Cell Size (pixels)",
                           #    color="#ffffff"
                           )
        # self.ax.tick_params(colors="#b2bec3")
        self.ax.grid(True,
                     alpha=0.3,
                     #  color="#4a5568"
                     )
        # self.ax.spines['bottom'].set_color("#4a5568")
        # self.ax.spines['left'].set_color("#4a5568")
        # self.ax.spines['top'].set_color("#4a5568")
        # self.ax.spines['right'].set_color("#4a5568")

        # Embed the figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()

        # Add navigation toolbar with improved styling
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        # self.toolbar.config(bg="#2d3436")

        # Style the toolbar buttons
        for child in self.toolbar.winfo_children():
            if isinstance(child, tk.Button):
                child.config(
                    # bg="#36393f",
                    # fg="#ffffff",
                    # activebackground="#4a5568"
                )

        # Pack the toolbar first, then the canvas
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_plot(self, data: Optional[Union[np.ndarray, list]] = None) -> None:
        """Update the plot with new data.

        Args:
            data: Array or list of cell size measurements. If None, clears the plot.
        """
        self.ax.clear()
        self.ax.set_title(
            "Cell Contraction Analysis",
            # color="#ffffff",
            fontsize=12,
            fontweight='bold'
        )
        self.ax.set_xlabel(
            "Frame Index",
            # color="#ffffff"
        )
        self.ax.set_ylabel(
            "Cell Size (pixels)",
            # color="#ffffff"
        )
        # self.ax.tick_params(colors="#b2bec3")
        self.ax.grid(
            True,
            alpha=0.3,
            # color="#4a5568"
        )
        # self.ax.spines['bottom'].set_color("#4a5568")
        # self.ax.spines['left'].set_color("#4a5568")
        # self.ax.spines['top'].set_color("#4a5568")
        # self.ax.spines['right'].set_color("#4a5568")

        if data is not None and len(data) > 0:
            # Convert to numpy array for consistent handling
            data_array = np.array(data)

            # Plot each well's data
            if len(data_array.shape) == 2:
                # Multiple wells per frame
                colors = plt.cm.Set1(np.linspace(0, 1, data_array.shape[1]))
                for i in range(data_array.shape[1]):
                    self.ax.plot(
                        data_array[:, i], label=f"Well {i+1}", marker='o', markersize=4, color=colors[i])
                self.ax.legend(
                    bbox_to_anchor=(1.05, 1),
                    loc='upper left',
                    # facecolor="#2d3436",
                    # edgecolor="#4a5568",
                    # labelcolor="#ffffff"
                )
            elif len(data_array.shape) == 1:
                # Single series of data
                self.ax.plot(data_array, marker='o', markersize=4)

            self.ax.set_title(
                "Cell Contraction Analysis - Live Update",
                # color="#ffffff",
                fontsize=12,
                fontweight='bold'
            )
        else:
            self.ax.set_title(
                "Cell Contraction Analysis - No Data Available",
                # color="#ffffff",
                fontsize=12,
                fontweight='bold'
            )
            self.ax.text(
                0.5, 0.5,
                'No data to display',
                transform=self.ax.transAxes,
                ha='center',
                va='center',
                fontsize=12,
                #  color="#b2bec3"
            )

        self.canvas.draw()
