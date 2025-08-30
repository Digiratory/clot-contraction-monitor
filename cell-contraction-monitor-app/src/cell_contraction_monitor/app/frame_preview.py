# cell-contraction-monitor-app/src/cell_contraction_monitor/app/frame_preview.py
import tkinter as tk
from tkinter import ttk
from typing import Optional
from cell_contraction_monitor.processing.processing_session import ProcessingSession
from PIL import Image, ImageTk


class FramePreview(ttk.Frame):
    """Widget that shows a preview image with zoom control and auto-increment functionality.
    
    This widget provides an interactive preview of image frames from a processing session,
    allowing users to navigate through frames using a slider or automatic playback.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # --- Canvas for the preview -------------------------------------------------
        self.canvas = tk.Canvas(self, background="black")
        self.canvas.pack(fill="both", expand=True)

        # --- Scale widget for frame navigation --------------------------------------
        self.scale_var = tk.IntVar(value=0)  # default 0
        self.scale = ttk.Scale(
            self,
            from_=0,
            to=100,  # Will be updated with actual frame count
            orient="horizontal",
            variable=self.scale_var,
            command=self._on_scale_change,
        )
        self.scale.pack(fill="x", padx=5, pady=5)

        # --- Control buttons --------------------------------------------------------
        button_frame = tk.Frame(self)
        button_frame.pack(pady=5)

        self.play_btn = ttk.Button(
            button_frame, text="Play", command=self._start_auto_increment)
        self.play_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(
            button_frame, text="Stop", command=self.stop_auto_increment)
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        # Internal state for the timer
        self._auto_job: Optional[str] = None

        self._processing_session: ProcessingSession | None = None
        self._current_image = None

    def set_frame_count(self, count: int) -> None:
        """Set the total number of frames and initialize the scale.
        
        Args:
            count: Total number of frames in the processing session
        """
        self.scale.configure(to=count)
        self.scale_var.set(0)

    def _draw_frame(self, frame_idx: int) -> None:
        """Draw a specific frame image on the canvas.
        
        Args:
            frame_idx: Index of the frame to draw
        """
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        
        # Get image data from processing session
        if self._processing_session is not None:
            try:
                img_array = self._processing_session.get_image(frame_idx)
                if img_array is not None:
                    # Convert numpy array to PIL Image for display
                    img = Image.fromarray(img_array)
                    img.thumbnail((w, h), Image.Resampling.LANCZOS)
                    self._current_image = ImageTk.PhotoImage(image=img)
                    self.canvas.create_image(w//2, h//2, image=self._current_image)
                    self.canvas.create_text(
                        5, 5, text=f"Frame {frame_idx}", fill="white", font=("Arial", 16), anchor="nw")
            except Exception as e:
                print(f"Error drawing frame {frame_idx}: {e}")

    def _on_scale_change(self, *args) -> None:
        """Handle manual scale changes (frame navigation).
        
        Args:
            *args: Scale change arguments
        """
        frame_idx = self.scale_var.get()
        self._draw_frame(frame_idx)

    def _start_auto_increment(self) -> None:
        """Begin auto-incrementing the frame index."""
        if self._auto_job is not None:
            # Already running
            return

        def _step() -> None:
            current = self.scale_var.get()
            max_frames = int(self.scale['to'])
            
            if current >= max_frames - 1:  # Stop before reaching max to prevent overflow
                # Stop when the maximum is reached
                self._auto_job = None
                return
                
            self.scale_var.set(current + 1)  # increment by 1
            self._on_scale_change()
            # Reschedule next step after 100ms (10 FPS)
            self._auto_job = self.after(100, _step)

        _step()

    def stop_auto_increment(self) -> None:
        """Stop any running auto-increment timer."""
        if self._auto_job is not None:
            self.after_cancel(self._auto_job)
            self._auto_job = None

    def set_processing_session(self, processing_session: ProcessingSession) -> None:
        """Set the processing session to work with.
        
        Args:
            processing_session: The processing session containing image data
        """
        self._processing_session = processing_session
        if processing_session is not None:
            self._processing_session.add_on_project_loaded_handler(
                self._on_prosessing_session_loaded)

    def _on_prosessing_session_loaded(self, processing_session: ProcessingSession) -> None:
        """Handle processing session loaded event.
        
        Args:
            processing_session: The loaded processing session
        """
        self.set_frame_count(processing_session.frame_count())
