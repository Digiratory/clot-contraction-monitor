# cell-contraction-monitor-app/src/cell_contraction_monitor/app/plot_widget.py
import tkinter as tk
from tkinter import ttk
from typing import Optional, Union

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


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
        self.ax.set_title(
            "Cell Contraction Analysis",
            #   color="#ffffff",
            fontsize=12,
            fontweight="bold",
        )
        self.ax.set_xlabel(
            "Frame Index",
            #    color="#ffffff"
        )
        self.ax.set_ylabel(
            "Cell Size (pixels)",
            #    color="#ffffff"
        )
        # self.ax.tick_params(colors="#b2bec3")
        self.ax.grid(
            True,
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

        # Create control frame for grouping options
        self.control_frame = ttk.Frame(self)
        self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Grouping radio buttons
        self.grouping_var = tk.StringVar(value="all")
        grouping_frame = ttk.LabelFrame(
            self.control_frame, text="Data Grouping", padding=5
        )
        grouping_frame.pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            grouping_frame,
            text="All Wells",
            variable=self.grouping_var,
            value="all",
            command=self._on_grouping_changed,
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            grouping_frame,
            text="Group by Rows",
            variable=self.grouping_var,
            value="rows",
            command=self._on_grouping_changed,
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            grouping_frame,
            text="Group by Columns",
            variable=self.grouping_var,
            value="columns",
            command=self._on_grouping_changed,
        ).pack(anchor=tk.W)

        # Pack the toolbar first, then the canvas
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _on_grouping_changed(self):
        """Handle grouping option changes."""
        # Replot with current data using new grouping
        if hasattr(self, "_current_data") and self._current_data is not None:
            self.update_plot(self._current_data)

    def _group_by_rows(self, data_array):
        """Group wells by rows (5 rows of 8 wells each)."""
        # Wells arranged in 5x8 grid: 0-39
        # Row 0: wells 0-7, Row 1: wells 8-15, etc.
        rows = 5
        cols = 8
        grouped_data = []

        for row in range(rows):
            row_wells = data_array[:, row * cols : (row + 1) * cols]
            if row_wells.size > 0:
                # Calculate mean and std for each frame in this row
                row_mean = np.mean(row_wells, axis=1)
                row_std = np.std(row_wells, axis=1)
                grouped_data.append((row_mean, row_std, f"Row {row+1}"))

        return grouped_data

    def _group_by_columns(self, data_array):
        """Group wells by columns (8 columns of 5 wells each)."""
        # Wells arranged in 5x8 grid: 0-39
        # Column 0: wells 0,8,16,24,32, Column 1: wells 1,9,17,25,33, etc.
        rows = 5
        cols = 8
        grouped_data = []

        for col in range(cols):
            col_wells = data_array[
                :, col::cols
            ]  # Extract every 8th element starting from col
            if col_wells.size > 0:
                # Calculate mean and std for each frame in this column
                col_mean = np.mean(col_wells, axis=1)
                col_std = np.std(col_wells, axis=1)
                grouped_data.append((col_mean, col_std, f"Column {col+1}"))

        return grouped_data

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
            fontweight="bold",
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
            # Store current data for potential replotting
            self._current_data = data

            # Convert to numpy array for consistent handling
            data_array = np.array(data)

            # Get current grouping option
            grouping_option = self.grouping_var.get()

            if len(data_array.shape) == 2:
                # Multiple wells per frame
                if grouping_option == "all":
                    # Plot all wells individually (original behavior)
                    colors = plt.cm.Set1(np.linspace(0, 1, data_array.shape[1]))
                    for i in range(data_array.shape[1]):
                        self.ax.plot(
                            data_array[:, i],
                            label=f"Well {i+1}",
                            marker="o",
                            markersize=4,
                            color=colors[i],
                        )
                    self.ax.legend(
                        bbox_to_anchor=(1.05, 1),
                        loc="upper left",
                        # facecolor="#2d3436",
                        # edgecolor="#4a5568",
                        # labelcolor="#ffffff"
                    )
                elif grouping_option == "rows":
                    # Group by rows and plot mean with std deviation
                    grouped_data = self._group_by_rows(data_array)
                    colors = plt.cm.Set1(np.linspace(0, 1, len(grouped_data)))
                    for i, (mean_vals, std_vals, label) in enumerate(grouped_data):
                        color = colors[i]
                        # Plot mean line
                        self.ax.plot(mean_vals, label=label, color=color, linewidth=2)
                        # Plot standard deviation as semi-transparent area
                        self.ax.fill_between(
                            range(len(mean_vals)),
                            mean_vals - std_vals,
                            mean_vals + std_vals,
                            alpha=0.2,
                            color=color,
                        )
                    self.ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
                elif grouping_option == "columns":
                    # Group by columns and plot mean with std deviation
                    grouped_data = self._group_by_columns(data_array)
                    colors = plt.cm.Set1(np.linspace(0, 1, len(grouped_data)))
                    for i, (mean_vals, std_vals, label) in enumerate(grouped_data):
                        color = colors[i]
                        # Plot mean line
                        self.ax.plot(mean_vals, label=label, color=color, linewidth=2)
                        # Plot standard deviation as semi-transparent area
                        self.ax.fill_between(
                            range(len(mean_vals)),
                            mean_vals - std_vals,
                            mean_vals + std_vals,
                            alpha=0.2,
                            color=color,
                        )
                    self.ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
            elif len(data_array.shape) == 1:
                # Single series of data
                self.ax.plot(data_array, marker="o", markersize=4)

            self.ax.set_title(
                "Cell Contraction Analysis - Live Update",
                # color="#ffffff",
                fontsize=12,
                fontweight="bold",
            )
        else:
            self.ax.set_title(
                "Cell Contraction Analysis - No Data Available",
                # color="#ffffff",
                fontsize=12,
                fontweight="bold",
            )
            self.ax.text(
                0.5,
                0.5,
                "No data to display",
                transform=self.ax.transAxes,
                ha="center",
                va="center",
                fontsize=12,
                #  color="#b2bec3"
            )

        self.canvas.draw()
