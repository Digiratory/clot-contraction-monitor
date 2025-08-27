# cell-contraction-monitor-app/src/cell_contraction_monitor/app/main.py
import tkinter as tk
from tkinter import filedialog, ttk
import threading

from cell_contraction_monitor.app.frame_preview import FramePreview
from cell_contraction_monitor.app.plot_widget import PlotFrame

from cell_contraction_monitor.processing.processing_session import ProcessingSession


class CellContractionApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("Cell Contraction Monitor")
        self.geometry("900x600")

        self.processing_session = ProcessingSession()
        self.processing_session.add_on_project_loaded_handler(
            self._on_prosessing_session_loaded)

        # Build the UI
        self._create_menu()
        self._create_widgets()
        self._processing_thread = None

    # ---------- Menu ----------
    def _create_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Select folder",
                              command=self.select_folder)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

    def select_folder(self):
        """Open a folder selection dialog (placeholder)."""
        folder = filedialog.askdirectory()
        if folder:
            print(f"Selected folder: {folder}")
            self.processing_session.select_folder(folder_path=folder)
            # TODO: Load data from the selected folder
            # popup = tk.Toplevel()
            # tk.Label(popup, text="Images being processed").grid(
            #     row=0, column=0)
            progress_var = tk.IntVar()
            progress_bar = ttk.Progressbar(self.status_frame,
                                           variable=progress_var,
                                           maximum=self.processing_session.frame_count())            
            progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)


            def update_progress(new_progress: int):
                nonlocal progress_var
                progress_var.set(new_progress)
                self.status_text.set(
                    f"File processing: {new_progress}/{self.processing_session.frame_count()}")
                self.plot_frame.update_plot(self.processing_session.get_cell_sizes())
                
            self._processing_thread = threading.Thread(
                target=self.processing_session.load_project, args=(update_progress,)).start()
    # ---------- Main Widgets ----------

    def _create_widgets(self):
        # Use a PanedWindow to split preview and plot areas
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)

        # Frame preview area
        self.preview_frame = FramePreview(paned, width=250)
        self.preview_frame.set_processing_session(self.processing_session)
        paned.add(self.preview_frame, weight=1)

        # Plot area
        self.plot_frame = PlotFrame(paned)
        paned.add(self.plot_frame, weight=3)

        self.status_frame = tk.Frame(self, bd=1, relief=tk.SUNKEN)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_text = tk.StringVar()
        self.status_text.set("Ready")
        self.status_label = tk.Label(self.status_frame, textvariable=self.status_text, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _on_prosessing_session_loaded(self, processing_session: ProcessingSession):        
        self.plot_frame.update_plot(self.processing_session.get_cell_sizes())


if __name__ == "__main__":
    app = CellContractionApp()
    app.mainloop()
