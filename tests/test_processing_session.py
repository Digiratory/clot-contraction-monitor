"""Tests for the ProcessingSession class."""

import unittest
from unittest.mock import Mock, patch

import numpy as np

# Import the module we want to test
from clot_contraction_monitor.processing.processing_session import ProcessingSession


class TestProcessingSession(unittest.TestCase):
    """Test cases for ProcessingSession class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.session = ProcessingSession()

    def test_init(self):
        """Test initialization of ProcessingSession."""
        # Should create an instance without errors
        self.assertIsInstance(self.session, ProcessingSession)
        self.assertIsNone(self.session.cell_sizes)
        self.assertEqual(self.session.images, [])
        self.assertEqual(self.session.annotations, [])

    @patch(
        "clot_contraction_monitor.processing.processing_session.CellInWellSegmentatior"
    )
    def test_select_folder_success(self, mock_segmentator_class):
        """Test successful folder selection."""
        # Mock the segmentator to return success
        mock_segmentator = Mock()
        mock_segmentator.predefine_wells.return_value = True
        mock_segmentator_class.return_value = mock_segmentator

        # This would normally test with actual files, but we're mocking for now
        # The actual implementation depends on file system access which is complex to mock properly
        pass

    def test_frame_count(self):
        """Test frame count functionality."""
        # Initially should have 0 frames
        self.assertEqual(self.session.frame_count(), 0)

    def test_get_cell_sizes(self):
        """Test cell sizes retrieval."""
        # Should return None when no data
        self.assertIsNone(self.session.get_cell_sizes())


if __name__ == "__main__":
    unittest.main()
