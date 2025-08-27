# cell-contraction-monitor-app/src/cell_contraction_monitor/app/frame_preview.py
import tkinter as tk
from tkinter import ttk
from cell_contraction_monitor.processing.processing_session import ProcessingSession
from PIL import Image, ImageTk


class FramePreview(ttk.Frame):
    """Widget that shows a preview image with a zoom scale and an auto‑increment button."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # --- Canvas for the preview -------------------------------------------------
        self.canvas = tk.Canvas(self, background="black")
        self.canvas.pack(fill="both", expand=True)

        # (Placeholder: in a real app you would load and display an image here.)
        # self._draw_frame()

        # --- Scale widget for zoom ----------------------------------------------------
        self.scale_var = tk.IntVar(value=100)  # default 100 %
        self.scale = ttk.Scale(
            self,
            from_=0,
            to=200,
            orient="horizontal",
            variable=self.scale_var,
            command=self._on_scale_change,
        )
        self.scale.pack(fill="x", padx=5, pady=5)

        # --- Auto‑increment button ----------------------------------------------------
        self.play_btn = ttk.Button(
            self, text="Play", command=self._start_auto_increment)
        self.play_btn.pack(pady=5)

        self.stop_btn = ttk.Button(
            self, text="Stop", command=self.stop_auto_increment)
        self.stop_btn.pack(pady=5)

        # Internal state for the timer
        self._auto_job = None

        self._processing_session: ProcessingSession | None = None
        self._current_image = None

    def set_frame_count(self, count: int):

        self.scale.configure(to=count)
        self.scale_var.set(0)
    # --------------------------------------------------------------------

    def _draw_frame(self, frame_idx: int):
        """Draw a simple placeholder in the canvas."""
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        # self.canvas.create_rectangle(10, 10, w-10, h-10, outline="white")
        img = Image.fromarray(self._processing_session.get_image(frame_idx))
        img.thumbnail((w, h))
        self._current_image = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(w//2, h//2, image=self._current_image)
        self.canvas.create_text(
            5, 5, text=f"Frame {frame_idx}", fill="white", font=("Arial", 16), anchor="nw")

    # --------------------------------------------------------------------
    def _on_scale_change(self, *args):
        """Handle manual scale changes (zoom)."""
        frame_idx = self.scale_var.get()
        # In a real application you would use `scale_value` to adjust the image
        # size or the canvas transform.  For now we just redraw the placeholder.
        self._draw_frame(frame_idx)

    # --------------------------------------------------------------------
    def _start_auto_increment(self):
        """Begin auto‑incrementing the scale value."""
        if self._auto_job is not None:
            # Already running
            return

        def _step():
            current = self.scale_var.get()
            if current >= self.scale['to']:
                # Stop when the maximum is reached
                self._auto_job = None
                return
            self.scale_var.set(current + 1)  # increment by 5%
            self._on_scale_change()
            # Reschedule next step after 0.1 s
            self._auto_job = self.after(100, _step)

        _step()

    # --------------------------------------------------------------------
    def stop_auto_increment(self):
        """Stop any running auto‑increment timer."""
        if self._auto_job is not None:
            self.after_cancel(self._auto_job)
            self._auto_job = None

    def set_processing_session(self, processing_session: ProcessingSession):
        self._processing_session = processing_session
        self._processing_session.add_on_project_loaded_handler(
            self._on_prosessing_session_loaded)

    def _on_prosessing_session_loaded(self, processing_session: ProcessingSession):
        self.set_frame_count(processing_session.frame_count())
