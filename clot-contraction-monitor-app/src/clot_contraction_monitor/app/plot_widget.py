# cell-contraction-monitor-app/src/clot_contraction_monitor/app/plot_widget.py
import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, Union

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from clot_contraction_monitor.app.radio_group_widget import RadioGroupWidget
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class PlotFrame(ttk.Frame):
    """A frame that embeds a Matplotlib plot for displaying clot contraction data.

    This widget provides real-time plotting capabilities for clot size measurements
    and other quantitative analysis results from the processing pipeline.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.figure = Figure(
            figsize=(6, 4),
            dpi=100,
        )
        self.ax = self.figure.add_subplot(
            111,
        )
        self.ax.set_title(
            self._get_plot_title(),
            fontsize=12,
            fontweight="bold",
        )
        self.ax.set_xlabel(
            "Frame Index",
        )
        self.ax.set_ylabel(
            "Relative size",
        )
        self.ax.set_ylim(0, 1)
        self.ax.grid(
            True,
            alpha=0.3,
        )

        # Embed the figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()

        # Initialize cursor line
        self.cursor_line = None
        self.current_frame_index = 0

        # Add navigation toolbar with improved styling
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()

        # Style the toolbar buttons
        for child in self.toolbar.winfo_children():
            if isinstance(child, tk.Button):
                child.config()

        # Create control frame for grouping options
        self.control_frame = ttk.Frame(self)
        self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Grouping radio buttons using RadioGroupWidget
        grouping_options = [
            ("All Wells", "all"),
            ("Group by Rows", "rows"),
            ("Group by Columns", "columns"),
        ]
        self.grouping_widget = RadioGroupWidget(
            self.control_frame,
            title="Data Grouping",
            options=grouping_options,
            default_value="all",
            callback=self._on_grouping_changed,
        )
        self.grouping_widget.pack(side=tk.LEFT, padx=5)

        # Smoothing radio buttons using RadioGroupWidget
        smoothing_options = [
            ("No filtering", "none"),
            ("3 samples", "3"),
            ("5 samples", "5"),
            ("7 samples", "7"),
        ]
        self.smoothing_widget = RadioGroupWidget(
            self.control_frame,
            title="Smoothing",
            options=smoothing_options,
            default_value="none",
            callback=self._on_smoothing_changed,
        )
        self.smoothing_widget.pack(side=tk.LEFT, padx=5)

        # Plot type radio buttons using RadioGroupWidget
        plot_options = [
            ("Raw data", "raw"),
            ("Fitted data", "fitted"),
        ]
        self.plot_options_widget = RadioGroupWidget(
            self.control_frame,
            title="Plotting",
            options=plot_options,
            default_value="none",
            callback=self._on_plot_type_changed,
        )
        self.plot_options_widget.pack(side=tk.LEFT, padx=5)

        # Pack the toolbar first, then the canvas
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def set_project_settings(self, project_settings) -> None:
        """Set the project settings to use for X-axis time scaling.

        Args:
            project_settings: The project settings containing sampling rate
        """
        self.project_settings = project_settings
        self.sampling_rate_seconds = (
            project_settings.sampling_rate_seconds if project_settings else 1.0
        )
        # Update plot if data is already available
        if hasattr(self, "_current_data") and self._current_data is not None:
            self.update_plot(self._current_data, self._current_data_fitted)
            # Ensure cursor is redrawn after replotting
            if self.current_frame_index >= 0:
                self.update_cursor(self.current_frame_index)

    def update_cursor(self, frame_index: int) -> None:
        """Update the vertical cursor line to the specified frame index.

        Args:
            frame_index: The frame index to position the cursor at
        """
        self.current_frame_index = frame_index

        # Remove existing cursor line if it exists
        if self.cursor_line is not None:
            try:
                self.cursor_line.remove()
            except:
                pass  # Line may have been removed during plot clear

        # Draw new cursor line if we have data
        if hasattr(self, "_current_data") and self._current_data is not None:
            # Use time position if we have sampling rate, otherwise use frame index
            cursor_position = frame_index
            if (
                hasattr(self, "sampling_rate_seconds")
                and self.sampling_rate_seconds != 1.0
            ):
                cursor_position = frame_index * self.sampling_rate_seconds
            # Use cyan color with dashed line style for visibility
            self.cursor_line = self.ax.axvline(
                x=cursor_position,
                color="cyan",
                linestyle="--",
                linewidth=2,
                alpha=0.8,
                label=f"Frame {frame_index}",
            )

            # Redraw the canvas to show the cursor
            self.canvas.draw()

    def _on_grouping_changed(self, value=None):
        """Handle grouping option changes."""
        # Replot with current data using new grouping
        if hasattr(self, "_current_data") and self._current_data is not None:
            self.update_plot(self._current_data, self._current_data_fitted)
            # Ensure cursor is redrawn after replotting
            if self.current_frame_index >= 0:
                self.update_cursor(self.current_frame_index)

    def _on_smoothing_changed(self, value=None):
        """Handle smoothing option changes."""
        # Replot with current data using new smoothing
        if hasattr(self, "_current_data") and self._current_data is not None:
            self.update_plot(self._current_data, self._current_data_fitted)
            # Ensure cursor is redrawn after replotting
            if self.current_frame_index >= 0:
                self.update_cursor(self.current_frame_index)

    def _on_plot_type_changed(self, value=None):
        if hasattr(self, "_current_data") and self._current_data is not None:
            self.update_plot(self._current_data, self._current_data_fitted)
            # Ensure cursor is redrawn after replotting
            if self.current_frame_index >= 0:
                self.update_cursor(self.current_frame_index)

    def _apply_smoothing(self, data_array):
        """Apply moving average smoothing to the data array.

        Args:
            data_array: Numpy array to smooth

        Returns:
            Smoothed numpy array
        """
        smoothing_option = self.smoothing_widget.get_value()
        if smoothing_option == "none":
            return data_array

        window_size = int(smoothing_option)
        if window_size < 2:
            return data_array

        # Apply moving average filter without zero-padding artifacts
        kernel = np.ones(window_size) / window_size
        if len(data_array.shape) == 1:
            # 1D array
            smoothed = np.convolve(data_array, kernel, mode="valid")
            # Pad the edges to maintain original length
            pad_left = (window_size - 1) // 2
            pad_right = window_size - 1 - pad_left

            # Use edge values for padding instead of zeros
            left_pad = np.full(pad_left, data_array[0])
            right_pad = np.full(pad_right, data_array[-1])

            return np.concatenate([left_pad, smoothed, right_pad])
        elif len(data_array.shape) == 2:
            # 2D array - apply smoothing to each column (time series for each well)
            smoothed = np.zeros_like(data_array)
            for i in range(data_array.shape[1]):
                column_data = data_array[:, i]
                smoothed_col = np.convolve(column_data, kernel, mode="valid")

                # Pad the edges to maintain original length
                pad_left = (window_size - 1) // 2
                pad_right = window_size - 1 - pad_left

                # Use edge values for padding instead of zeros
                left_pad = np.full(pad_left, column_data[0])
                right_pad = np.full(pad_right, column_data[-1])

                smoothed[:, i] = np.concatenate([left_pad, smoothed_col, right_pad])
            return smoothed
        else:
            return data_array

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

                # Use group name from project settings if available
                label = f"Row {row+1}"
                if (
                    hasattr(self, "project_settings")
                    and self.project_settings
                    and self.project_settings.group_names
                ):
                    if row < len(self.project_settings.group_names):
                        label = self.project_settings.group_names[row]

                grouped_data.append((row_mean, row_std, label))

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

                # Use group name from project settings if available
                label = f"Column {col+1}"
                if (
                    hasattr(self, "project_settings")
                    and self.project_settings
                    and self.project_settings.group_names
                ):
                    if col < len(self.project_settings.group_names):
                        label = self.project_settings.group_names[col]

                grouped_data.append((col_mean, col_std, label))

        return grouped_data

    def _get_plot_title(self, suffix: str = "") -> str:
        """Generate plot title with project name.

        Args:
            suffix: Additional text to append to the base title

        Returns:
            Formatted plot title
        """
        base_title = "Clot Contraction Analysis"
        if (
            hasattr(self, "project_settings")
            and self.project_settings
            and self.project_settings.experiment_name
        ):
            base_title = (
                f"Clot Contraction Analysis - {self.project_settings.experiment_name}"
            )

        if suffix:
            return f"{base_title} - {suffix}"
        return base_title

    def update_plot(
        self,
        data: Optional[Union[np.ndarray, list]] = None,
        fitted_data: Optional[Union[np.ndarray, list]] = None,
        params: Optional[Dict[str, np.ndarray]] = None,
    ) -> None:
        """Update the plot with new data.

        Args:
            data: Array or list of clot size measurements. If None, clears the plot.
        """
        self.ax.clear()
        self.ax.set_title(
            self._get_plot_title(),
            fontsize=12,
            fontweight="bold",
        )
        # Set X-axis label based on whether we have sampling rate
        if hasattr(self, "sampling_rate_seconds"):
            xlabel = "Time (seconds)"
        else:
            xlabel = "Frame Index"
        self.ax.set_xlabel(
            xlabel,
        )
        self.ax.set_ylabel(
            "Relative size",
        )
        self.ax.set_ylim(0, 1)
        self.ax.grid(
            True,
            alpha=0.3,
        )

        if data is not None and len(data) > 0:
            # Store current data for potential replotting
            self._current_data = data
            self._current_data_fitted = fitted_data

            plot_type_option = self.plot_options_widget.get_value()
            if plot_type_option == "raw" or fitted_data is None:
                data_array = data
            else:
                data_array = fitted_data

            # Convert to numpy array for consistent handling
            data_array = np.array(data_array)

            # Apply smoothing to the data
            data_array = self._apply_smoothing(data_array)

            # Create time array if sampling rate is available
            if (
                hasattr(self, "sampling_rate_seconds")
                and self.sampling_rate_seconds != 1.0
            ):
                time_array = np.arange(len(data_array)) * self.sampling_rate_seconds
            else:
                time_array = np.arange(len(data_array))

            # Get current grouping option
            grouping_option = self.grouping_widget.get_value()

            if len(data_array.shape) == 2:
                # Multiple wells per frame
                if grouping_option == "all":
                    # Plot all wells individually (original behavior)
                    colors = plt.cm.Set1(np.linspace(0, 1, data_array.shape[1]))
                    for i in range(data_array.shape[1]):
                        self.ax.plot(
                            time_array,
                            data_array[:, i],
                            label=f"Well {i+1}",
                            marker="o",
                            markersize=4,
                            color=colors[i],
                        )

                    self.ax.legend(loc="best")
                elif grouping_option == "rows":
                    # Group by rows and plot mean with std deviation
                    grouped_data = self._group_by_rows(data_array)
                    colors = plt.cm.Set1(np.linspace(0, 1, len(grouped_data)))
                    for i, (mean_vals, std_vals, label) in enumerate(grouped_data):
                        color = colors[i]
                        # Plot mean line
                        self.ax.plot(
                            time_array, mean_vals, label=label, color=color, linewidth=2
                        )
                        # Plot standard deviation as semi-transparent area
                        self.ax.fill_between(
                            time_array,
                            mean_vals - std_vals,
                            mean_vals + std_vals,
                            alpha=0.2,
                            color=color,
                        )
                    self.ax.legend(loc="best")
                elif grouping_option == "columns":
                    # Group by columns and plot mean with std deviation
                    grouped_data = self._group_by_columns(data_array)
                    colors = plt.cm.Set1(np.linspace(0, 1, len(grouped_data)))
                    for i, (mean_vals, std_vals, label) in enumerate(grouped_data):
                        color = colors[i]
                        # Plot mean line
                        self.ax.plot(
                            time_array, mean_vals, label=label, color=color, linewidth=2
                        )
                        # Plot standard deviation as semi-transparent area
                        self.ax.fill_between(
                            time_array,
                            mean_vals - std_vals,
                            mean_vals + std_vals,
                            alpha=0.2,
                            color=color,
                        )
                    self.ax.legend(loc="best")
            elif len(data_array.shape) == 1:
                # Single series of data
                self.ax.plot(time_array, data_array, marker="o", markersize=4)

            self.ax.set_title(
                self._get_plot_title(),
                fontsize=12,
                fontweight="bold",
            )
        else:
            self.ax.set_title(
                self._get_plot_title("No Data Available"),
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
            )

        # Redraw cursor if we have data and a current frame index
        if (
            hasattr(self, "_current_data")
            and self._current_data is not None
            and self.current_frame_index >= 0
        ):
            # Use time position if we have sampling rate, otherwise use frame index
            cursor_position = self.current_frame_index
            if (
                hasattr(self, "sampling_rate_seconds")
                and self.sampling_rate_seconds != 1.0
            ):
                cursor_position = self.current_frame_index * self.sampling_rate_seconds
            self.cursor_line = self.ax.axvline(
                x=cursor_position,
                color="cyan",
                linestyle="--",
                linewidth=2,
                alpha=0.8,
                label=f"Frame {self.current_frame_index}",
            )

        self.canvas.draw()
