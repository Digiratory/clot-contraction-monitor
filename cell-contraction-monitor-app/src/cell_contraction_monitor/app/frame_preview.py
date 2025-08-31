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
        self.canvas = tk.Canvas(
            self,
            # background="#2d3436",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # --- Frame counter display --------------------------------------------------
        self.frame_counter_frame = tk.Frame(
            self,
            # bg="#2d3436"
        )
        self.frame_counter_frame.pack(fill="x", padx=5, pady=(5, 0))

        self.frame_label = tk.Label(
            self.frame_counter_frame,
            text="Frame: 0/0",
            # bg="#2d3436",
            # fg="#ffffff",
            font=("Arial", 10, "bold")
        )
        self.frame_label.pack(side=tk.LEFT)

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
        button_frame = tk.Frame(
            self,
            # bg="#2d3436"
        )
        button_frame.pack(pady=5)

        # Navigation buttons with icons (using text for simplicity)
        self.prev_btn = ttk.Button(
            button_frame, text="◀", command=self._go_to_previous_frame, width=3)
        self.prev_btn.pack(side=tk.LEFT, padx=2)

        self.play_btn = ttk.Button(
            button_frame, text="▶", command=self._start_auto_increment, width=3)
        self.play_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(
            button_frame, text="■", command=self.stop_auto_increment, width=3)
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        self.next_btn = ttk.Button(
            button_frame, text="▶", command=self._go_to_next_frame, width=3)
        self.next_btn.pack(side=tk.LEFT, padx=2)

        # --- Zoom controls ----------------------------------------------------------
        zoom_frame = tk.Frame(
            self,
            #   bg="#2d3436"
        )
        zoom_frame.pack(fill="x", padx=5, pady=(0, 5))

        tk.Label(
            zoom_frame,
            text="Zoom:",
            #  bg="#2d3436",
            #  fg="#ffffff",
        ).pack(side=tk.LEFT)
        self.zoom_var = tk.DoubleVar(value=1.0)
        self.zoom_scale = ttk.Scale(
            zoom_frame,
            from_=0.5,
            to=3.0,
            orient="horizontal",
            variable=self.zoom_var,
            command=self._on_zoom_change,
            length=100
        )
        self.zoom_scale.pack(side=tk.LEFT, padx=5)
        self.zoom_label = tk.Label(
            zoom_frame, text="100%",
            # bg="#2d3436",
            # fg="#ffffff"
        )
        self.zoom_label.pack(side=tk.LEFT)

        # Internal state for the timer
        self._auto_job: Optional[str] = None
        self._playback_speed = 100  # milliseconds between frames
        self._is_playing = False

        self._processing_session: ProcessingSession | None = None
        self._current_image = None
        self._zoom_level = 1.0
        self._image_width = 0
        self._image_height = 0

    def set_frame_count(self, count: int) -> None:
        """Set the total number of frames and initialize the scale.

        Args:
            count: Total number of frames in the processing session
        """
        self.scale.configure(to=count)
        self.scale_var.set(0)
        self._update_frame_counter()

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
                # TODO: add control for flag `annotated` to show labeled or raw images
                img_array = self._processing_session.get_image(
                    frame_idx, annotated=True)
                if img_array is not None:
                    # Convert numpy array to PIL Image for display
                    img = Image.fromarray(img_array)
                    img.thumbnail((w, h), Image.Resampling.LANCZOS)

                    self._image_width, self._image_height = img.size

                    # Apply zoom
                    # zoomed_w = int(self._image_width * self._zoom_level)
                    # zoomed_h = int(self._image_height * self._zoom_level)
                    # img = img.resize((zoomed_w, zoomed_h),
                    #                  Image.Resampling.LANCZOS)

                    self._current_image = ImageTk.PhotoImage(image=img)
                    self.canvas.create_image(
                        w//2, h//2, image=self._current_image)
                    self._update_frame_counter()
            except Exception as e:
                print(f"Error drawing frame {frame_idx}: {e}")

    def _update_frame_counter(self) -> None:
        """Update the frame counter display."""
        max_frames = int(self.scale['to'])
        current_frame = self.scale_var.get()
        self.frame_label.config(text=f"Frame: {current_frame}/{max_frames}")

    def _on_scale_change(self, *args) -> None:
        """Handle manual scale changes (frame navigation).

        Args:
            *args: Scale change arguments
        """
        frame_idx = self.scale_var.get()
        self._draw_frame(frame_idx)

    def _go_to_previous_frame(self) -> None:
        """Navigate to the previous frame."""
        current = self.scale_var.get()
        if current > 0:
            self.scale_var.set(current - 1)
            self._on_scale_change()

    def _go_to_next_frame(self) -> None:
        """Navigate to the next frame."""
        current = self.scale_var.get()
        max_frames = int(self.scale['to'])
        if current < max_frames - 1:
            self.scale_var.set(current + 1)
            self._on_scale_change()

    def _on_zoom_change(self, *args) -> None:
        """Handle zoom level changes."""
        self._zoom_level = self.zoom_var.get()
        self.zoom_label.config(text=f"{int(self._zoom_level * 100)}%")
        # Redraw current frame with new zoom
        frame_idx = self.scale_var.get()
        self._draw_frame(frame_idx)

    def _start_auto_increment(self) -> None:
        """Begin auto-incrementing the frame index."""
        if self._auto_job is not None or self._is_playing:
            # Already running
            return

        self._is_playing = True
        self.play_btn.config(text="❚❚")  # Pause symbol

        def _step() -> None:
            current = self.scale_var.get()
            max_frames = int(self.scale['to'])

            if current >= max_frames - 1:  # Stop before reaching max to prevent overflow
                # Stop when the maximum is reached
                self._is_playing = False
                self.play_btn.config(text="▶")
                self._auto_job = None
                return

            self.scale_var.set(current + 1)  # increment by 1
            self._on_scale_change()
            # Reschedule next step after _playback_speed (10 FPS)
            self._auto_job = self.after(self._playback_speed, _step)

        _step()

    def stop_auto_increment(self) -> None:
        """Stop any running auto-increment timer."""
        if self._auto_job is not None:
            self.after_cancel(self._auto_job)
            self._auto_job = None
        self._is_playing = False
        self.play_btn.config(text="▶")
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
