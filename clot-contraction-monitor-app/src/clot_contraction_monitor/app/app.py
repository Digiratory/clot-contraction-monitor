import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional

import numpy as np
from clot_contraction_monitor.app.frame_preview import FramePreview
from clot_contraction_monitor.app.plot_widget import PlotFrame
from clot_contraction_monitor.io import export_to_csv
from clot_contraction_monitor.processing.processing_session import ProcessingSession
from clot_contraction_monitor.project_dialog import show_project_dialog
from clot_contraction_monitor.project_settings import ProjectSettings
from clot_contraction_monitor.settings_persistence import SettingsPersistence


class ClotContractionApp(tk.Tk):
    """Main application window for the Clot Contraction Monitor.

    This class provides the main GUI interface for analyzing clot contraction patterns
    in biological experiments. It orchestrates the processing pipeline and user
    interaction components.
    """

    APPLICATION_NAME = "Clot Contraction Monitor"

    def __init__(self) -> None:
        """Initialize the main application window."""
        super().__init__()
        self.title(ClotContractionApp.APPLICATION_NAME)
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

        # Track processing status
        self.processing_finished = False
        self.file_menu = None
        self.save_csv_menu_index = None

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
        self.file_menu = tk.Menu(
            menubar,
            tearoff=0,
            # bg="#2d3436",
            # fg="#ffffff",
            # activebackground="#4a5568"
        )
        self.file_menu.add_command(label="Select folder", command=self.select_folder)
        self.file_menu.add_command(
            label="Save CSV", command=self.save_csv, state=tk.DISABLED
        )
        menubar.add_cascade(label="File", menu=self.file_menu)
        self.config(menu=menubar)

    def _set_save_csv_enabled(self, enabled: bool) -> None:
        """Enable or disable the Save CSV menu item."""
        if self.file_menu:
            state = tk.NORMAL if enabled else tk.DISABLED
            try:
                # Find the Save CSV menu item index
                for i in range(self.file_menu.index("end") + 1):
                    if self.file_menu.entrycget(i, "label") == "Save CSV":
                        self.file_menu.entryconfig(i, state=state)
                        break
            except:
                pass  # Menu might not be fully initialized

    def select_folder(self) -> None:
        """Open a folder selection dialog and configure project settings if needed."""
        folder = filedialog.askdirectory()
        if folder:
            print(f"Selected folder: {folder}")

            # Check if settings file exists
            if SettingsPersistence.settings_file_exists(folder):
                # Load existing settings and start processing directly
                try:
                    settings = SettingsPersistence.load_settings_from_json(folder)
                    if settings:
                        print(
                            f"Loaded existing settings for experiment: {settings.experiment_name}"
                        )
                        self._start_processing(folder, settings)
                        return
                except Exception as e:
                    messagebox.showwarning(
                        "Settings Error",
                        f"Could not load existing settings: {e}\nPlease reconfigure the project.",
                    )

            # No valid settings file exists, show configuration dialog
            def on_settings_configured(settings: ProjectSettings) -> None:
                """Callback when project settings are configured."""
                self._start_processing(folder, settings)

            show_project_dialog(self, folder, on_settings_configured)

    def _start_processing(self, folder: str, settings: ProjectSettings) -> None:
        """Start processing with configured project settings.

        Args:
            folder: Path to the selected folder
            settings: Configured project settings
        """
        print(f"Starting processing for {settings.experiment_name}")
        self.processing_finished = False
        self._set_save_csv_enabled(False)

        # Initialize processing session with project settings
        self.processing_session.select_folder(folder_path=folder, settings=settings)

        # Set project settings in plot frame for proper X-axis scaling
        self.plot_frame.set_project_settings(settings)

        # Initialize progress tracking
        progress_var = tk.IntVar()
        progress_bar = ttk.Progressbar(
            self.status_frame,
            variable=progress_var,
            maximum=self.processing_session.frame_count(),
        )
        progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)

        def update_progress(new_progress: int, from_cache: bool, is_last: bool) -> None:
            """Update progress bar and status text during processing."""
            nonlocal progress_var
            new_progress += 1
            progress_var.set(new_progress)

            if new_progress < self.processing_session.frame_count():
                self.status_text.set(
                    f"File processing: {new_progress}/{self.processing_session.frame_count()}"
                )
            else:
                self.status_text.set(f"Ready")
                self.processing_finished = True
                self._set_save_csv_enabled(True)

            # Update plot on every frame completion, regardless of cache status
            if not from_cache or is_last:
                self.plot_frame.update_plot(
                    self.processing_session.get_clot_sizes(),
                    self.processing_session.get_fitted_curves(),
                    self.processing_session.get_analysis_results(),
                )

        # Start processing in a separate thread to keep UI responsive
        self._processing_thread = threading.Thread(
            target=self.processing_session.load_project,
            args=(update_progress,),
            daemon=True,
        )
        self.title(f"{ClotContractionApp.APPLICATION_NAME}: {settings.experiment_name}")
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

        # Connect preview frame to plot frame for cursor synchronization
        self.preview_frame.set_plot_frame(self.plot_frame)

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
        self.plot_frame.update_plot(self.processing_session.get_clot_sizes())

    def save_csv(self) -> None:
        """Save processed cell size data to a CSV file."""
        if not self.processing_finished:
            messagebox.showwarning("Warning", "Processing is not finished yet.")
            return

        cell_sizes = self.processing_session.get_clot_sizes()
        if cell_sizes is None:
            messagebox.showerror("Error", "No data available to save.")
            return

        # Open save file dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Cell Size Data",
        )

        if not file_path:
            return

        try:
            export_to_csv(cell_sizes, file_path, self.processing_session.images)
            messagebox.showinfo("Success", f"Data saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def _on_closing(self):
        self.destroy()
        exit()
