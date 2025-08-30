# cell-contraction-monitor-app/src/cell_contraction_monitor/app/plot_widget.py
import tkinter as tk
from tkinter import ttk
from typing import Optional, Union
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PlotFrame(ttk.Frame):
    """A frame that embeds a Matplotlib plot for displaying cell contraction data.
    
    This widget provides real-time plotting capabilities for cell size measurements
    and other quantitative analysis results from the processing pipeline.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Cell Contraction Analysis")
        self.ax.set_xlabel("Frame Index")
        self.ax.set_ylabel("Cell Size (pixels)")
        self.ax.grid(True, alpha=0.3)

        # Embed the figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def update_plot(self, data: Optional[Union[np.ndarray, list]] = None) -> None:
        """Update the plot with new data.
        
        Args:
            data: Array or list of cell size measurements. If None, clears the plot.
        """
        self.ax.clear()
        self.ax.set_title("Cell Contraction Analysis")
        self.ax.set_xlabel("Frame Index")
        self.ax.set_ylabel("Cell Size (pixels)")
        self.ax.grid(True, alpha=0.3)
        
        if data is not None and len(data) > 0:
            # Convert to numpy array for consistent handling
            data_array = np.array(data)
            
            # Plot each well's data
            if len(data_array.shape) == 2:
                # Multiple wells per frame
                for i in range(data_array.shape[1]):
                    self.ax.plot(data_array[:, i], label=f"Well {i+1}", marker='o', markersize=3)
                self.ax.legend()
            elif len(data_array.shape) == 1:
                # Single series of data
                self.ax.plot(data_array, marker='o', markersize=3)
            
            self.ax.set_title("Cell Contraction Analysis - Live Update")
        else:
            self.ax.set_title("Cell Contraction Analysis - No Data Available")
            self.ax.text(0.5, 0.5, 'No data to display', transform=self.ax.transAxes, 
                        ha='center', va='center', fontsize=12)
        
        self.canvas.draw()
