"""Tests for cursor synchronization between FramePreview and PlotFrame."""

import tkinter as tk
import unittest
from unittest.mock import Mock, patch

import numpy as np

# Import the modules we want to test
from clot_contraction_monitor.app.frame_preview import FramePreview
from clot_contraction_monitor.app.plot_widget import PlotFrame


class TestCursorSynchronization(unittest.TestCase):
    """Test cases for cursor synchronization functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a root window for testing (needed for tkinter)
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window

        # Create the widgets
        self.frame_preview = FramePreview(self.root)
        self.plot_frame = PlotFrame(self.root)

        # Connect them for testing
        self.frame_preview.set_plot_frame(self.plot_frame)

    def tearDown(self):
        """Clean up after each test method."""
        self.root.destroy()

    def test_cursor_initialization(self):
        """Test that cursor is properly initialized."""
        # Check that PlotFrame has cursor-related attributes
        self.assertTrue(hasattr(self.plot_frame, "cursor_line"))
        self.assertTrue(hasattr(self.plot_frame, "current_frame_index"))
        self.assertTrue(hasattr(self.plot_frame, "update_cursor"))

    def test_update_cursor_method_exists(self):
        """Test that update_cursor method exists and is callable."""
        # Method should exist
        self.assertTrue(callable(getattr(self.plot_frame, "update_cursor", None)))

    def test_frame_preview_has_plot_frame_reference(self):
        """Test that FramePreview can reference PlotFrame."""
        # Should have the plot frame reference
        self.assertTrue(hasattr(self.frame_preview, "_plot_frame"))
        self.assertEqual(self.frame_preview._plot_frame, self.plot_frame)

    def test_cursor_update_with_data(self):
        """Test cursor update when plot has data."""
        # Create some test data
        test_data = np.random.rand(100, 5)  # 100 frames, 5 wells

        # Update plot with data
        self.plot_frame.update_plot(test_data)

        # Update cursor to frame 50
        self.plot_frame.update_cursor(50)

        # Check that current frame index was updated
        self.assertEqual(self.plot_frame.current_frame_index, 50)

    def test_cursor_persistence_after_plot_update(self):
        """Test that cursor persists after plot updates."""
        # Create some test data
        test_data = np.random.rand(100, 5)

        # Update plot and set cursor
        self.plot_frame.update_plot(test_data)
        self.plot_frame.update_cursor(25)

        # Update plot again (simulating grouping/smoothing change)
        self.plot_frame.update_plot(test_data)

        # Cursor should still be at the same position
        self.assertEqual(self.plot_frame.current_frame_index, 25)


if __name__ == "__main__":
    unittest.main()
