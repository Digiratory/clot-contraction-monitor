# cell-contraction-monitor-app/src/cell_contraction_monitor/app/main.py
import argparse
import csv
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, ttk
from typing import Any, Callable, Optional

import numpy as np
from cell_contraction_monitor.app.frame_preview import FramePreview
from cell_contraction_monitor.app.plot_widget import PlotFrame
from cell_contraction_monitor.processing.processing_session import ProcessingSession


class CellContractionApp(tk.Tk):
    """Main application window for the Cell Contraction Monitor.

    This class provides the main GUI interface for analyzing cell contraction patterns
    in biological experiments. It orchestrates the processing pipeline and user
    interaction components.
    """

    APPLICATION_NAME = "Cell Contraction Monitor"

    def __init__(self) -> None:
        """Initialize the main application window."""
        super().__init__()
        self.title(CellContractionApp.APPLICATION_NAME)
        self.geometry("1000x700")
        self.minsize(800, 600)

        # Configure styles for a more modern look
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 9), padding=5)
        style.configure("TLabel", font=("Arial", 9))
        style.configure("TScale", gripcount=0)
        style.configure(
            "TFrame",
            # background="#2d3436"
        )

        # Configure window background
        # self.configure(bg="#2d3436")

        self.processing_session: ProcessingSession = ProcessingSession()
        self.processing_session.add_on_project_loaded_handler(
            self._on_prosessing_session_loaded
        )

        # Build the UI
        self._create_menu()
        self._create_widgets()
        self._processing_thread: Optional[threading.Thread] = None

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ---------- Menu ----------
    def _create_menu(self) -> None:
        """Create the application menu bar."""
        menubar = tk.Menu(
            self,
            # bg="#2d3436",
            # fg="#ffffff",
            # activebackground="#4a5568",
            # activeforeground="#ffffff"
        )
        file_menu = tk.Menu(
            menubar,
            tearoff=0,
            # bg="#2d3436",
            # fg="#ffffff",
            # activebackground="#4a5568"
        )
        file_menu.add_command(label="Select folder", command=self.select_folder)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

    def select_folder(self) -> None:
        """Open a folder selection dialog and start processing images."""
        folder = filedialog.askdirectory()
        if folder:
            print(f"Selected folder: {folder}")
            self.processing_session.select_folder(folder_path=folder)

            # Initialize progress tracking
            progress_var = tk.IntVar()
            progress_bar = ttk.Progressbar(
                self.status_frame,
                variable=progress_var,
                maximum=self.processing_session.frame_count(),
            )
            progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)

            def update_progress(
                new_progress: int, from_cache: bool, is_last: bool
            ) -> None:
                """Update progress bar and status text during processing."""
                nonlocal progress_var
                new_progress += 1
                progress_var.set(new_progress)

                if new_progress != self.processing_session.frame_count():
                    self.status_text.set(
                        f"File processing: {new_progress}/{self.processing_session.frame_count()}"
                    )
                else:
                    self.status_text.set(f"Ready")
                if not from_cache or is_last:
                    self.plot_frame.update_plot(
                        self.processing_session.get_cell_sizes()
                    )

            # Start processing in a separate thread to keep UI responsive
            self._processing_thread = threading.Thread(
                target=self.processing_session.load_project,
                args=(update_progress,),
                daemon=True,
            )
            self.title(
                f"{CellContractionApp.APPLICATION_NAME}: { os.path.split(folder)[1]}"
            )
            self._processing_thread.start()

    # ---------- Main Widgets ----------

    def _create_widgets(self) -> None:
        """Create and layout the main application widgets."""
        # Use a PanedWindow to split preview and plot areas
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        # Frame preview area
        self.preview_frame = FramePreview(paned, width=250)
        self.preview_frame.set_processing_session(self.processing_session)
        paned.add(self.preview_frame, weight=1)

        # Plot area
        self.plot_frame = PlotFrame(paned)
        paned.add(self.plot_frame, weight=3)

        # Status bar with improved styling
        self.status_frame = tk.Frame(
            self,
            bd=1,
            relief=tk.SUNKEN,
            # bg="#2d3436"
        )
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_text = tk.StringVar()
        self.status_text.set("Ready")
        self.status_label = tk.Label(
            self.status_frame,
            textvariable=self.status_text,
            anchor=tk.W,
            # bg="#2d3436",
            # fg="#ffffff"
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _on_prosessing_session_loaded(
        self, processing_session: ProcessingSession
    ) -> None:
        """Handle processing session loaded event.

        Args:
            processing_session: The loaded processing session
        """
        self.plot_frame.update_plot(self.processing_session.get_cell_sizes())

    def _on_closing(self):
        self.destroy()
        exit()


def run_headless(input_folder: str, output_csv: str) -> None:
    """Run the application in headless mode for batch processing.

    Args:
        input_folder: Path to the folder containing images to process
        output_csv: Path where to save the CSV results
    """
    print(f"Running in headless mode...")
    print(f"Input folder: {input_folder}")
    print(f"Output CSV: {output_csv}")

    # Initialize processing session
    processing_session = ProcessingSession()

    # Select and validate folder
    if not processing_session.select_folder(folder_path=input_folder):
        print("Error: Failed to select folder or no valid images found")
        sys.exit(1)

    # Progress callback for headless mode
    def progress_callback(frame_idx: int, from_cache: bool, is_last: bool) -> None:
        status = "cached" if from_cache else "processed"
        print(f"Frame {frame_idx + 1}/{processing_session.frame_count()}: {status}")
        if is_last:
            print("Processing complete!")

    # Process all images
    if not processing_session.load_project(progress_callback):
        print("Error: Failed to process images")
        sys.exit(1)

    # Get results
    cell_sizes = processing_session.get_cell_sizes()
    if cell_sizes is None:
        print("Error: No cell size data available")
        sys.exit(1)

    # Export to CSV
    export_to_csv(cell_sizes, output_csv, processing_session.images)
    print(f"Results exported to: {output_csv}")


def export_to_csv(cell_sizes: np.ndarray, output_path: str, image_paths: list) -> None:
    """Export cell size data to CSV format.

    Args:
        cell_sizes: Array of cell sizes with shape (num_images, num_wells)
        output_path: Path to save the CSV file
        image_paths: List of image file paths for row labels
    """
    num_images, num_wells = cell_sizes.shape

    # Create column headers (Well_1, Well_2, ..., Well_N)
    headers = ["Sample"] + [f"Well_{i+1}" for i in range(num_wells)]

    with open(output_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)

        # Write headers
        writer.writerow(headers)

        # Write data rows
        for i in range(num_images):
            # Use image filename as sample identifier
            sample_name = os.path.splitext(os.path.basename(image_paths[i]))[0]
            row = [sample_name] + cell_sizes[i].tolist()
            writer.writerow(row)


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Cell Contraction Monitor - Analyze cell contraction patterns"
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run in headless mode without GUI"
    )
    parser.add_argument(
        "--input-folder",
        type=str,
        help="Input folder containing images (required for headless mode)",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="results.csv",
        help="Output CSV file path (default: results.csv)",
    )

    args = parser.parse_args()

    if args.headless:
        if not args.input_folder:
            print("Error: --input-folder is required when using --headless mode")
            sys.exit(1)

        if not os.path.isdir(args.input_folder):
            print(f"Error: Input folder does not exist: {args.input_folder}")
            sys.exit(1)

        run_headless(args.input_folder, args.output_csv)
    else:
        # GUI mode
        app = CellContractionApp()
        app.mainloop()


if __name__ == "__main__":
    main()
