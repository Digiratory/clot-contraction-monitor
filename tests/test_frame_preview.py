"""Tests for the FramePreview class."""

import tkinter as tk
import unittest
from unittest.mock import Mock, patch

# Import the module we want to test
from cell_contraction_monitor.app.frame_preview import FramePreview


class TestFramePreview(unittest.TestCase):
    """Test cases for FramePreview class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a root window for testing (needed for tkinter)
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window

        # Create the frame preview widget
        self.frame_preview = FramePreview(self.root)

    def tearDown(self):
        """Clean up after each test method."""
        self.root.destroy()

    def test_init(self):
        """Test initialization of FramePreview."""
        # Should create an instance without errors
        self.assertIsInstance(self.frame_preview, FramePreview)

    def test_set_frame_count(self):
        """Test setting frame count."""
        # Test with a valid count
        self.frame_preview.set_frame_count(10)
        # The actual implementation would be tested with a real GUI

    def test_set_processing_session(self):
        """Test setting processing session."""
        # Create a mock session
        mock_session = Mock()
        self.frame_preview.set_processing_session(mock_session)

        # Should set the session
        self.assertEqual(self.frame_preview._processing_session, mock_session)


if __name__ == "__main__":
    unittest.main()
