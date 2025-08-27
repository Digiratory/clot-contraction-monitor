# cell-contraction-monitor-app/src/cell_contraction_monitor/app/plot_widget.py
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PlotFrame(ttk.Frame):
    """A frame that embeds a Matplotlib plot."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Placeholder Plot")
        self.ax.set_xlabel("X-axis")
        self.ax.set_ylabel("Y-axis")

        # Embed the figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
    
    # Placeholder for updating the plot
    def update_plot(self, data):
        self.ax.clear()
        self.ax.plot(data)
        self.canvas.draw()