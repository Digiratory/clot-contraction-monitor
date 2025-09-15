"""Tests for the video_utils module."""

import os
import tempfile
import unittest
from unittest.mock import Mock, mock_open, patch

import cv2
import numpy as np
from clot_contraction_monitor.io.video_utils import VideoUtils


class TestVideoUtils(unittest.TestCase):
    """Test cases for VideoUtils class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        # Clean up temp directory after tests
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_is_video_file(self):
        """Test video file detection."""
        # Create test files for supported extensions
        test_video_dir = os.path.join(self.temp_dir, "test_files")
        os.makedirs(test_video_dir)

        # Supported extensions
        supported_files = []
        for ext in VideoUtils.SUPPORTED_EXTENSIONS:
            filename = f"test_video{ext}"
            filepath = os.path.join(test_video_dir, filename)
            with open(filepath, "w") as f:
                f.write("dummy")
            supported_files.append(filepath)

        for file_path in supported_files:
            with self.subTest(file_path=file_path):
                self.assertTrue(VideoUtils.is_video_file(file_path))

        # Non-video files
        non_video_files = []
        for ext in [".jpg", ".pdf", ".txt", ".csv"]:
            filename = f"test_file{ext}"
            filepath = os.path.join(test_video_dir, filename)
            with open(filepath, "w") as f:
                f.write("dummy")
            non_video_files.append(filepath)

        for file_path in non_video_files:
            with self.subTest(file_path=file_path):
                self.assertFalse(VideoUtils.is_video_file(file_path))

        # Non-existent file
        self.assertFalse(VideoUtils.is_video_file("/nonexistent/file.mp4"))

    @patch("cv2.VideoCapture")
    def test_get_video_fps_success(self, mock_video_capture):
        """Test successful FPS detection."""
        # Mock a working video capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 30.0  # 30 FPS
        mock_cap.release.return_value = None
        mock_video_capture.return_value = mock_cap

        fps = VideoUtils.get_video_fps("test_video.mp4")
        self.assertEqual(fps, 30.0)

        # Verify the mock was called correctly
        mock_cap.get.assert_called_once_with(cv2.CAP_PROP_FPS)
        mock_cap.release.assert_called_once()

    @patch("cv2.VideoCapture")
    def test_get_video_fps_none_on_error(self, mock_video_capture):
        """Test FPS detection returns None on error."""
        # Mock a failing video capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_cap.release.return_value = None
        mock_video_capture.return_value = mock_cap

        fps = VideoUtils.get_video_fps("corrupt_video.mp4")
        self.assertIsNone(fps)

        mock_cap.get.assert_not_called()  # Should not attempt to get FPS
        mock_cap.release.assert_called_once()

    @patch("cv2.VideoCapture")
    def test_get_video_fps_zero_fps(self, mock_video_capture):
        """Test FPS detection when video has zero FPS."""
        # Mock video with invalid FPS
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 0
        mock_cap.release.return_value = None
        mock_video_capture.return_value = mock_cap

        fps = VideoUtils.get_video_fps("zero_fps_video.mp4")
        self.assertIsNone(fps)

    @patch("cv2.VideoCapture")
    def test_get_video_frame_count_success(self, mock_video_capture):
        """Test successful frame count detection."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 1500  # 1500 frames
        mock_cap.release.return_value = None
        mock_video_capture.return_value = mock_cap

        count = VideoUtils.get_video_frame_count("test_video.mp4")
        self.assertEqual(count, 1500)

        mock_cap.get.assert_called_once_with(cv2.CAP_PROP_FRAME_COUNT)
        mock_cap.release.assert_called_once()

    @patch("cv2.VideoCapture")
    def test_get_video_frame_count_none_on_error(self, mock_video_capture):
        """Test frame count detection returns None on error."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap

        count = VideoUtils.get_video_frame_count("invalid_video.mp4")
        self.assertIsNone(count)

        mock_cap.get.assert_not_called()

    def test_create_project_folder_for_video(self):
        """Test project folder creation."""
        # Create a test directory structure
        test_video_dir = os.path.join(self.temp_dir, "videos")
        os.makedirs(test_video_dir)
        video_path = os.path.join(test_video_dir, "experiment_001.mp4")

        # Ensure video file exists (create empty file)
        with open(video_path, "w") as f:
            f.write("")

        # Create project folder
        project_folder = VideoUtils.create_project_folder_for_video(video_path)

        # Verify folder was created
        self.assertTrue(os.path.exists(project_folder))
        self.assertTrue(os.path.isdir(project_folder))

        # Verify folder name (should be video name without extension)
        expected_name = "experiment_001"
        self.assertEqual(os.path.basename(project_folder), expected_name)

        # Verify location (should be in same directory as video)
        self.assertEqual(os.path.dirname(project_folder), test_video_dir)

    def test_create_project_folder_creates_directory(self):
        """Test that project folder creation creates the directory if it doesn't exist."""
        test_video_dir = os.path.join(self.temp_dir, "videos")
        os.makedirs(test_video_dir)
        video_path = os.path.join(test_video_dir, "test.mp4")

        # Don't create the project folder yet
        project_folder = VideoUtils.create_project_folder_for_video(video_path)

        # Should still create it
        self.assertTrue(os.path.exists(project_folder))
        self.assertTrue(os.path.isdir(project_folder))

    @patch("cv2.VideoCapture")
    @patch("cv2.imwrite")
    def test_extract_frames_from_video_success(self, mock_imwrite, mock_video_capture):
        """Test successful frame extraction at interval."""
        # Mock video capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 150,  # 5 seconds at 30 FPS
        }.get(prop, 0)
        # Mock read to return 150 frames, then end of video (to prevent StopIteration)
        mock_cap.read.side_effect = [
            (True, np.zeros((480, 640, 3), dtype=np.uint8))
        ] * 150 + [(False, None)]
        mock_cap.release.return_value = None
        mock_video_capture.return_value = mock_cap

        # Mock imwrite to simulate successful saves
        mock_imwrite.return_value = True

        # Test extraction
        extracted_count, actual_fps = VideoUtils.extract_frames_from_video(
            "test_video.mp4",
            self.temp_dir,
            frame_interval=10,  # Every 10th frame = 15 frames
        )

        self.assertEqual(extracted_count, 15)  # 150/10 = 15
        self.assertAlmostEqual(actual_fps, 30.0 / 10, places=1)  # Expected FPS

        # Verify imwrite was called 15 times
        self.assertEqual(mock_imwrite.call_count, 15)

    @patch("cv2.VideoCapture")
    def test_extract_frames_from_video_invalid_format(self, mock_video_capture):
        """Test frame extraction with invalid video format."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap

        with self.assertRaises(RuntimeError):
            VideoUtils.extract_frames_from_video("invalid_video.mp4", self.temp_dir)

    @patch("cv2.VideoCapture")
    @patch("cv2.imwrite")
    def test_extract_frames_at_fps_success(self, mock_imwrite, mock_video_capture):
        """Test successful frame extraction at target FPS."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 60.0,  # 60 FPS video
            cv2.CAP_PROP_FRAME_COUNT: 300,
        }.get(prop, 0)
        # Mock the read method to return tuples (successful read, frame)
        mock_cap.read.side_effect = [
            (True, np.zeros((480, 640, 3), dtype=np.uint8))
        ] * 150 + [(False, None)]
        mock_cap.release.return_value = None
        mock_video_capture.return_value = mock_cap

        mock_imwrite.return_value = True

        # Extract at 30 FPS from 60 FPS video
        extracted_count, actual_fps = VideoUtils.extract_frames_at_fps(
            "high_fps_video.mp4", self.temp_dir, target_fps=30.0
        )

        self.assertGreater(extracted_count, 0)
        self.assertEqual(actual_fps, 30.0)

        # Verify second call to extract_frames_from_video (this should be interval extraction)
        self.assertTrue(mock_imwrite.call_count > 0)

    @patch("cv2.VideoCapture")
    @patch("cv2.imwrite")
    def test_extract_frames_at_fps_higher_than_video(
        self, mock_imwrite, mock_video_capture
    ):
        """Test extraction when target FPS > video FPS."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 100,
        }.get(prop, 0)
        # Mock read to return frames and then end of video
        mock_cap.read.side_effect = [
            (True, np.zeros((480, 640, 3), dtype=np.uint8))
        ] * 100 + [(False, None)]
        mock_cap.release.return_value = None
        mock_video_capture.return_value = mock_cap

        mock_imwrite.return_value = True

        # Target FPS higher than source FPS should extract all frames
        extracted_count, actual_fps = VideoUtils.extract_frames_at_fps(
            "video.mp4", self.temp_dir, target_fps=60.0  # Higher than source 30 fps
        )

        # Should extract all frames since target FPS > source FPS
        self.assertEqual(extracted_count, 100)  # All 100 frames extracted
        self.assertEqual(actual_fps, 30.0)  # Source FPS
        self.assertEqual(mock_imwrite.call_count, 100)

    @patch("cv2.VideoCapture")
    def test_extract_frames_generic_error(self, mock_video_capture):
        """Test frame extraction with generic error."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = Exception("OpenCV error")
        mock_video_capture.return_value = mock_cap

        with self.assertRaises(RuntimeError):
            VideoUtils.extract_frames_from_video("error_video.mp4", self.temp_dir)

    def test_supported_extensions_constant(self):
        """Test supported extensions set."""
        expected_extensions = {".mp4", ".avi", ".mov", ".wmv", ".mkv", ".flv", ".webm"}
        self.assertEqual(VideoUtils.SUPPORTED_EXTENSIONS, expected_extensions)


if __name__ == "__main__":
    unittest.main()
