"""
Video handling dialog and coordinator for the Clot Contraction Monitor.

This module provides functionality for processing video files into analysis-ready
image sequences with configurable sampling rates.
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

from ..io.video_utils import VideoUtils
from ..project_dialog import show_project_dialog
from ..project_settings import ProjectSettings
from .app import ClotContractionApp


class VideoDialog(tk.Toplevel):
    """Dialog for configuring video processing settings."""

    def __init__(
        self,
        parent: tk.Tk,
        video_path: str,
        callback: Callable[[str], None],
    ):
        """Initialize the video dialog.

        Args:
            parent: Parent Tkinter window
            video_path: Path to the video file
            callback: Function to call with the project folder path
        """
        super().__init__(parent)
        self.parent = parent
        self.video_path = video_path
        self.callback = callback
        self.project_folder: Optional[str] = None

        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()

        # Configure window
        self.title("Configure Video Processing")
        self.geometry("500x450")
        self.resizable(False, False)

        # Center the dialog
        self.center_window()

        # Get video information
        self.video_fps = VideoUtils.get_video_fps(video_path)
        self.video_frame_count = VideoUtils.get_video_frame_count(video_path)

        # Initialize variables
        self.extraction_option_var = tk.StringVar(value="all_frames")
        self.custom_fps_var = tk.StringVar()

        # Build UI
        self._create_widgets()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Wait for user input
        self.wait_window(self)

    def center_window(self) -> None:
        """Center the dialog on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create and layout the dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Title
        title_label = ttk.Label(
            main_frame, text="Video Processing Settings", font=("Arial", 12, "bold")
        )
        title_label.pack(pady=(0, 15))

        # Video info frame
        info_frame = ttk.LabelFrame(main_frame, text="Video Information", padding="10")
        info_frame.pack(fill="x", pady=(0, 15))

        video_name = os.path.basename(self.video_path)
        ttk.Label(info_frame, text=f"Video: {video_name}").pack(anchor="w")

        if self.video_fps:
            ttk.Label(info_frame, text=".2f").pack(anchor="w")
        else:
            ttk.Label(info_frame, text="FPS: Unable to detect").pack(anchor="w")

        if self.video_frame_count:
            ttk.Label(info_frame, text=f"Total frames: {self.video_frame_count}").pack(
                anchor="w"
            )
        else:
            ttk.Label(info_frame, text="Frame count: Unable to detect").pack(anchor="w")

        # Frame extraction settings frame
        extraction_frame = ttk.LabelFrame(
            main_frame, text="Frame Extraction Settings", padding="10"
        )
        extraction_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            extraction_frame,
            text="Choose how to extract frames from the video:",
            font=("Arial", 9, "italic"),
        ).pack(anchor="w", pady=(0, 10))

        # All frames option
        ttk.Radiobutton(
            extraction_frame,
            text="Extract all frames",
            variable=self.extraction_option_var,
            value="all_frames",
            command=self._on_extraction_option_changed,
        ).pack(anchor="w", pady=(0, 5))

        ttk.Label(
            extraction_frame,
            text="(Original timing preserved for highest quality)",
            font=("Arial", 8),
        ).pack(anchor="w", padx=(20, 0), pady=(0, 10))

        # Custom FPS option
        ttk.Radiobutton(
            extraction_frame,
            text="Extract at custom frame rate:",
            variable=self.extraction_option_var,
            value="custom_fps",
            command=self._on_extraction_option_changed,
        ).pack(anchor="w", pady=(5, 5))

        # Custom FPS input
        custom_frame = ttk.Frame(extraction_frame)
        custom_frame.pack(fill="x", padx=(20, 0), pady=(0, 5))

        self.custom_fps_entry = ttk.Entry(
            custom_frame, textvariable=self.custom_fps_var, state="disabled"
        )
        self.custom_fps_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Label(custom_frame, text=" FPS").pack(side="left")

        ttk.Label(
            extraction_frame,
            text="(Note: Can reduce frame rate for faster processing)",
            font=("Arial", 8),
        ).pack(anchor="w", padx=(20, 0))

        # Important note about project settings
        note_frame = ttk.LabelFrame(main_frame, text="Important Note", padding="10")
        note_frame.pack(fill="x", pady=(0, 15))

        note_text = (
            "Project sampling rate for time-axis scaling will be configured "
            "in the next dialog. This affects analysis scaling, not frame extraction."
        )
        ttk.Label(
            note_frame, text=note_text, font=("Arial", 9, "italic"), wraplength=400
        ).pack(anchor="w")

        # Error/Info message
        self.message_label = ttk.Label(main_frame, text="", foreground="blue")
        self.message_label.pack(pady=(0, 10))

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(buttons_frame, text="Cancel", command=self._on_cancel).pack(
            side="right", padx=(5, 0)
        )
        self.ok_button = ttk.Button(
            buttons_frame, text="Extract Frames", command=self._on_ok
        )
        self.ok_button.pack(side="right")

        # Processing progress (initially hidden)
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, variable=self.progress_var, maximum=100
        )
        self.progress_label = ttk.Label(self.progress_frame, text="Processing video...")

        # Set initial state
        self._on_extraction_option_changed()

    def _on_extraction_option_changed(self) -> None:
        """Handle extraction option change."""
        if self.extraction_option_var.get() == "all_frames":
            self.custom_fps_entry.config(state="disabled")
            if self.video_fps:
                self.message_label.config(
                    text=f"All {self.video_frame_count} frames will be extracted at native {self.video_fps:.1f} FPS",
                    foreground="green",
                )
            else:
                self.message_label.config(
                    text="All frames will be extracted at native rate",
                    foreground="green",
                )
        else:
            self.custom_fps_entry.config(state="normal")
            self.custom_fps_entry.focus()
            self.message_label.config(text="")

    def _on_ok(self) -> None:
        """Handle OK button click and start video processing."""
        try:
            # Determine extraction settings
            if self.extraction_option_var.get() == "all_frames":
                # Extract all frames - reuse video's FPS
                if not self.video_fps:
                    messagebox.showwarning(
                        "Warning",
                        "Unable to detect video FPS. Please specify a custom extraction rate.",
                        parent=self,
                    )
                    return
                extraction_fps = self.video_fps
            else:
                # Custom FPS extraction
                try:
                    extraction_fps = float(self.custom_fps_var.get().strip())
                    if extraction_fps <= 0:
                        raise ValueError("FPS must be positive")
                    if extraction_fps > self.video_fps:
                        messagebox.showwarning(
                            "Warning",
                            ".1f"
                            f"Extraction FPS ({extraction_fps:.1f}) is higher than video FPS ({self.video_fps:.1f}).\n"
                            f"This may not provide additional quality but will process frames multiple times.",
                            parent=self,
                        )
                except ValueError:
                    messagebox.showerror(
                        "Error",
                        "Please enter a valid extraction rate (positive number).",
                        parent=self,
                    )
                    return

            # Disable buttons and show progress
            self.ok_button.config(state="disabled")
            for child in self.winfo_children():
                if isinstance(child, ttk.Button):
                    child.config(state="disabled")

            # Show progress UI
            self.progress_frame.pack(fill="x", pady=(10, 0))
            self.progress_bar.pack(fill="x", pady=(5, 0))
            self.progress_label.pack(pady=(5, 0))

            # Start processing in thread
            processing_thread = threading.Thread(
                target=self._process_video, args=(extraction_fps,), daemon=True
            )
            processing_thread.start()

        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to start video processing: {e}", parent=self
            )
            self._on_cancel()

    def _process_video(self, extraction_fps: float) -> None:
        """Process the video in a separate thread."""
        try:
            # Update progress
            self._update_progress(10, "Creating project folder...")

            # Create project folder
            self.project_folder = VideoUtils.create_project_folder_for_video(
                self.video_path
            )

            # Update progress
            self._update_progress(30, "Extracting video frames...")

            # Extract frames based on settings
            if self.extraction_option_var.get() == "all_frames":
                # Extract all frames
                extracted_count, actual_fps = VideoUtils.extract_frames_from_video(
                    self.video_path, self.project_folder, frame_interval=1
                )
            else:
                # Extract at custom FPS
                extracted_count, actual_fps = VideoUtils.extract_frames_at_fps(
                    self.video_path, self.project_folder, extraction_fps
                )

            # Update progress
            if self.extraction_option_var.get() == "all_frames":
                self._update_progress(
                    100,
                    f"Extracted {extracted_count} frames at native {actual_fps:.1f} FPS",
                )
            else:
                self._update_progress(
                    100,
                    f"Extracted {extracted_count} frames at {extraction_fps:.1f} FPS",
                )

            # Success - close dialog and call callback
            self.after(500, lambda: self._finish_processing())

        except Exception as e:
            self.after(0, lambda: self._handle_error(f"Video processing failed: {e}"))

    def _update_progress(self, value: int, message: str) -> None:
        """Update progress bar and message safely from thread."""

        def update():
            self.progress_var.set(value)
            self.progress_label.config(text=message)

        self.after(0, update)

    def _finish_processing(self) -> None:
        """Finish processing and close dialog."""
        self.callback(self.project_folder)
        self.destroy()

    def _handle_error(self, error_msg: str) -> None:
        """Handle processing error."""
        messagebox.showerror("Error", error_msg, parent=self)
        self._on_cancel()

    def _on_cancel(self) -> None:
        """Handle dialog cancellation."""
        self.destroy()


def show_video_dialog(
    parent: tk.Tk, video_path: str, callback: Callable[[str], None]
) -> VideoDialog:
    """Convenience function to show the video processing dialog.

    Args:
        parent: Parent Tkinter window
        video_path: Path to the video file
        callback: Function to call with the project folder path

    Returns:
        The dialog instance
    """
    return VideoDialog(parent, video_path, callback)
