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
        # Create figure with custom subplot layout
        self.figure = plt.figure(figsize=(12, 8), dpi=100)

        # Main plot - spans full width across first row
        self.ax = self.figure.add_subplot(2, 1, 1)
        self.ax.set_title(
            self._get_plot_title(),
            fontsize=12,
            fontweight="bold",
        )
        self.ax.set_xlabel("Frame Index")
        self.ax.set_ylabel("Relative size")
        self.ax.set_ylim(0, 1)
        self.ax.grid(True, alpha=0.3)

        # Add horizontal boxplot subplots in second row with shared Y axis
        self.param_axes = {}
        self.param_configs = [
            ("crossover_position", "Crossover\nPosition"),
            ("last_index_95p", "95% Point\nFrame"),
            ("first_index_5p", "5% Point\nFrame"),
        ]

        # Create a GridSpec for more flexible subplot layout
        from matplotlib.gridspec import GridSpec

        gs = GridSpec(2, 3, figure=self.figure, height_ratios=[2, 1])

        # Main plot takes full width of first row
        self.ax = self.figure.add_subplot(gs[0, :])

        # Parameter subplots in second row - share Y axis
        first_ax = None
        for i, (param_key, title) in enumerate(self.param_configs):
            ax = self.figure.add_subplot(
                gs[1, i], sharey=first_ax if first_ax is not None else None
            )
            ax.set_title(title, fontsize=10, fontweight="bold")

            # Only the first subplot gets a ylabel
            if i == 0:
                ax.set_ylabel("Time (Seconds)", fontsize=9)
                first_ax = ax
            else:
                # Hide Y labels for shared axes to avoid clutter
                ax.tick_params(left=False)
                ax.set_ylabel("")  # Clear ylabel for middle subplots

            ax.grid(True, alpha=0.3, axis="y")
            self.param_axes[param_key] = ax

        # Adjust layout to minimize whitespace
        self.figure.subplots_adjust(hspace=0.3, wspace=0.1)

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
            default_value="raw",
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
            self.update_plot(
                self._current_data, self._current_data_fitted, self._current_params
            )
            # Ensure cursor is redrawn after replotting
            if self.current_frame_index >= 0:
                self.update_cursor(self.current_frame_index)

    def _on_smoothing_changed(self, value=None):
        """Handle smoothing option changes."""
        # Replot with current data using new smoothing
        if hasattr(self, "_current_data") and self._current_data is not None:
            self.update_plot(
                self._current_data, self._current_data_fitted, self._current_params
            )
            # Ensure cursor is redrawn after replotting
            if self.current_frame_index >= 0:
                self.update_cursor(self.current_frame_index)

    def _on_plot_type_changed(self, value=None):
        if hasattr(self, "_current_data") and self._current_data is not None:
            self.update_plot(
                self._current_data, self._current_data_fitted, self._current_params
            )
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

    def collect_group_stats(
        self, data_array: np.ndarray, params: Dict[str, np.ndarray]
    ):
        """Collect statistical parameters per group for boxplot visualization.

        Args:
            data_array: 2D array of curve data (frames, wells)
            params: Dictionary of parameter arrays from curve analysis

        Returns:
            List of dictionaries containing group statistics and labels
        """
        grouping_option = self.grouping_widget.get_value()
        if params is None:
            return []

        param_names = ["crossover_position", "last_index_95p", "first_index_5p"]
        group_stats = []

        # Get available parameter data length
        first_param = next(iter(params.values()), None)
        if first_param is None:
            return []

        num_wells = len(first_param)

        # Create actual groups based on grouping logic
        if grouping_option == "rows":
            # Group wells by rows (each row has 8 wells in a 5x8 grid)
            wells_per_row = 8
            num_rows = (
                num_wells + wells_per_row - 1
            ) // wells_per_row  # Ceiling division

            # Use project settings group names if available
            base_labels = [f"Row {i+1}" for i in range(num_rows)]
            if (
                hasattr(self, "project_settings")
                and self.project_settings
                and self.project_settings.group_names
            ):
                labels_to_use = self.project_settings.group_names[:num_rows]
                # Pad with default names if not enough custom names
                labels_to_use.extend(base_labels[len(labels_to_use) :])
            else:
                labels_to_use = base_labels

            # Create groups for each row
            for row_idx in range(num_rows):
                if row_idx >= len(labels_to_use):
                    break

                start_well = row_idx * wells_per_row
                end_well = min((row_idx + 1) * wells_per_row, num_wells)
                well_indices = list(range(start_well, end_well))

                if well_indices:  # Only create group if there are wells
                    group_data = {}
                    for param_name in param_names:
                        if param_name in params:
                            param_values = (
                                params[param_name][well_indices]
                                * self.sampling_rate_seconds
                            )
                            # Filter out NaN values and check if we have enough data
                            valid_values = param_values[~np.isnan(param_values)]
                            group_data[param_name] = (
                                valid_values.tolist() if len(valid_values) >= 1 else []
                            )

                    if any(
                        group_data[param_name] for param_name in param_names
                    ):  # Only if we have some valid data
                        group_data["label"] = labels_to_use[row_idx]
                        group_stats.append(group_data)

        elif grouping_option == "columns":
            # Group wells by columns (every 8th well)
            cols_per_group = 8
            num_cols = cols_per_group  # Use fixed 8 columns for consistency

            # Use project settings group names if available
            base_labels = [f"Col {i+1}" for i in range(num_cols)]
            if (
                hasattr(self, "project_settings")
                and self.project_settings
                and self.project_settings.group_names
            ):
                labels_to_use = self.project_settings.group_names[:num_cols]
                # Pad with default names if not enough custom names
                labels_to_use.extend(base_labels[len(labels_to_use) :])
            else:
                labels_to_use = base_labels

            # Create groups for each column
            for col_idx in range(num_cols):
                if col_idx >= len(labels_to_use):
                    break

                # Create column indices: every cols_per_group-th well starting from col_idx
                well_indices = [
                    col_idx + i * cols_per_group
                    for i in range(
                        (num_wells - col_idx + cols_per_group - 1) // cols_per_group
                    )
                ]
                well_indices = [idx for idx in well_indices if idx < num_wells]

                if well_indices:  # Only create group if there are wells
                    group_data = {}
                    for param_name in param_names:
                        if param_name in params:
                            param_values = (
                                params[param_name][well_indices]
                                * self.sampling_rate_seconds
                            )
                            # Filter out NaN values
                            valid_values = param_values[~np.isnan(param_values)]
                            group_data[param_name] = (
                                valid_values.tolist() if len(valid_values) >= 1 else []
                            )

                    if any(
                        group_data[param_name] for param_name in param_names
                    ):  # Only if we have some valid data
                        group_data["label"] = labels_to_use[col_idx]
                        group_stats.append(group_data)

        elif grouping_option == "all":
            # Single group with all wells
            group_data = {}
            well_indices = list(range(num_wells))

            for param_name in param_names:
                if param_name in params:
                    param_values = (
                        params[param_name][well_indices] * self.sampling_rate_seconds
                    )
                    # Filter out NaN values
                    valid_values = param_values[~np.isnan(param_values)]
                    group_data[param_name] = (
                        valid_values.tolist() if len(valid_values) >= 1 else []
                    )

            if any(
                group_data[param_name] for param_name in param_names
            ):  # Only if we have some valid data
                group_data["label"] = "All Wells"
                group_stats.append(group_data)

        return group_stats

    def update_boxplot(self, group_stats: list):
        """Update the horizontal boxplot subplots with statistical data per group.

        Args:
            group_stats: List of dictionaries containing group statistics
        """
        # Clear all parameter axes
        for ax in self.param_axes.values():
            ax.clear()

        if not group_stats or len(group_stats) == 0:
            # Show no data message on each parameter axis
            for ax in self.param_axes.values():
                ax.set_title("No Data", fontsize=10)
                ax.text(
                    0.5,
                    0.5,
                    "No parameter data available",
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    fontsize=9,
                )
            return

        colors = plt.cm.Set1(np.linspace(0, 1, len(group_stats)))

        # Create separate boxplots for each parameter
        for i, (param_name, title) in enumerate(self.param_configs):
            if param_name not in self.param_axes:
                continue

            ax = self.param_axes[param_name]
            ax.set_title(title, fontsize=10, fontweight="bold")
            ax.set_ylabel("Time (Seconds)", fontsize=9)
            ax.grid(True, alpha=0.3, axis="y")

            # Collect data for this parameter from all groups
            parameter_data = []
            group_labels = []

            for group_stat in group_stats:
                if param_name in group_stat and group_stat[param_name]:
                    parameter_data.append(group_stat[param_name])
                    group_labels.append(
                        group_stat.get("label", f"Group {len(group_labels) + 1}")
                    )

            if parameter_data:
                # Create boxplot for this parameter
                try:
                    result = ax.boxplot(
                        parameter_data,
                        patch_artist=True,
                        showfliers=True,
                        widths=0.7,
                        showmeans=True,
                        meanline=False,
                    )

                    # Style the boxes with different colors for each group
                    for i, patch in enumerate(result["boxes"]):
                        color = colors[i % len(colors)]
                        patch.set_facecolor(color)
                        patch.set_alpha(0.7)

                    # Style other elements
                    for mean in result["means"]:
                        mean.set_marker("o")
                        mean.set_markerfacecolor("red")
                        mean.set_markeredgecolor("black")
                        mean.set_markersize(4)

                    # Style outliers and whiskers
                    for flier in result["fliers"]:
                        flier.set_marker("o")
                        flier.set_markerfacecolor("black")
                        flier.set_markeredgecolor("none")
                        flier.set_markersize(3)

                    # Set tick labels if we have group information
                    if (
                        group_labels and len(group_labels) <= 10
                    ):  # Don't clutter with too many labels
                        ax.set_xticks(range(1, len(group_labels) + 1))
                        ax.set_xticklabels(
                            group_labels, rotation=45, ha="right", fontsize=8
                        )

                    # Branding for the axis
                    ax.grid(True, alpha=0.3, axis="y")

                except Exception as e:
                    # Handle boxplot creation errors gracefully
                    ax.text(
                        0.5,
                        0.5,
                        f"Failed to create\nboxplot: {str(e)[:50]}",
                        transform=ax.transAxes,
                        ha="center",
                        va="center",
                        fontsize=8,
                    )
            else:
                # No valid data for this parameter
                ax.set_title("No Valid Data", fontsize=10)
                ax.text(
                    0.5,
                    0.5,
                    "No data available",
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    fontsize=9,
                )

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
            self._current_params = params

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

        # Update boxplot with statistical data if parameters are available
        if data is not None and params is not None and len(data) > 0:
            # Convert to numpy array for grouping stats collection
            data_array = np.array(data)
            group_stats = self.collect_group_stats(data_array, params)
            self.update_boxplot(group_stats)

        self.canvas.draw()
