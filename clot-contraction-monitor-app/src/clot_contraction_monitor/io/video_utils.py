"""
Video processing utilities for the Clot Contraction Monitor.

This module provides functionality for extracting frames from video files
and creating project directories for video-based analysis.
"""

import logging
import os
from typing import Callable, Optional, Tuple

import cv2

# Configure logging
logger = logging.getLogger(__name__)


class VideoUtils:
    """Utility class for video processing operations in the Clot Contraction Monitor.

    Provides functionality for:
    - Video file validation and metadata extraction
    - Frame extraction at specified intervals or target FPS
    - Project directory creation for video analysis
    """

    # Supported video file extensions
    SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mov", ".wmv", ".mkv", ".flv", ".webm"}

    @staticmethod
    def is_video_file(file_path: str) -> bool:
        """Check if the given file path points to a supported video file.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file is a supported video format, False otherwise
        """
        if not os.path.isfile(file_path):
            return False

        _, ext = os.path.splitext(file_path.lower())
        return ext in VideoUtils.SUPPORTED_EXTENSIONS

    @staticmethod
    def get_video_fps(video_path: str) -> Optional[float]:
        """Get the frames per second (FPS) of a video file.

        Args:
            video_path: Path to the video file

        Returns:
            FPS value or None if video cannot be opened or has invalid FPS
        """
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.warning(f"Could not open video file: {video_path}")
                return None

            fps = cap.get(cv2.CAP_PROP_FPS)

            # Validate FPS value
            if fps <= 0:
                logger.warning(f"Invalid FPS detected for video {video_path}: {fps}")
                return None

            return fps

        except Exception as e:
            logger.error(f"Error getting FPS from video {video_path}: {e}")
            return None
        finally:
            if cap is not None:
                cap.release()

    @staticmethod
    def get_video_frame_count(video_path: str) -> Optional[int]:
        """Get the total frame count of a video file.

        Args:
            video_path: Path to the video file

        Returns:
            Total frame count or None if video cannot be opened
        """
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.warning(f"Could not open video file: {video_path}")
                return None

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Validate frame count
            if total_frames < 0:
                logger.warning(
                    f"Invalid frame count for video {video_path}: {total_frames}"
                )
                return None

            cap.release()
            return total_frames

        except Exception as e:
            logger.error(f"Error getting frame count from video {video_path}: {e}")
            return None
        finally:
            if cap is not None:
                cap.release()

    @staticmethod
    def create_project_folder_for_video(video_path: str) -> str:
        """Create a project folder for video processing.

        Creates a subfolder with the same name as the video file (without extension)
        in the same directory as the video file.

        Args:
            video_path: Path to the video file

        Returns:
            Path to the created project folder
        """
        try:
            # Get the directory and filename without extension
            video_dir = os.path.dirname(video_path)
            video_name = os.path.splitext(os.path.basename(video_path))[0]

            # Create project folder path
            project_folder = os.path.join(video_dir, video_name)

            # Create the directory if it doesn't exist
            if not os.path.exists(project_folder):
                os.makedirs(project_folder)
                logger.info(f"Created project folder: {project_folder}")

            return project_folder

        except Exception as e:
            logger.error(f"Error creating project folder for video {video_path}: {e}")
            raise RuntimeError(f"Failed to create project folder: {e}")

    @staticmethod
    def extract_frames_from_video(
        video_path: str,
        output_folder: str,
        frame_interval: int = 1,
        max_frames: Optional[int] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Tuple[int, float]:
        """Extract frames from a video file at specified intervals.

        Args:
            video_path: Path to the video file
            output_folder: Path to output folder for extracted frames
            frame_interval: Interval between extracted frames (1 = every frame,
                          2 = every 2nd frame, etc.)
            max_frames: Maximum number of frames to extract (None for all)
            progress_callback: Optional callback function to report progress (value, message)

        Returns:
            Tuple of (number of frames extracted, frames per second)

        Raises:
            ValueError: If video file cannot be opened or parameters are invalid
            RuntimeError: If frame extraction fails
        """
        # Validate inputs
        if frame_interval < 1:
            raise ValueError("Frame interval must be >= 1")

        if max_frames is not None and max_frames <= 0:
            raise ValueError("Max frames must be positive or None")

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                logger.warning(
                    f"Invalid FPS detected, using default 30.0 for video {video_path}"
                )
                fps = 30.0  # Default fallback

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                logger.warning(
                    f"Invalid frame count detected, assuming 1 frame for video {video_path}"
                )
                total_frames = 1  # Minimum

            # Calculate actual FPS based on frame interval
            actual_fps = fps / frame_interval if frame_interval > 1 else fps

            # Create output folder if it doesn't exist
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
                logger.info(f"Created output folder: {output_folder}")

            frame_count = 0
            extracted_count = 0

            # Estimate total frames to extract
            estimated_total_frames = (
                total_frames + frame_interval - 1
            ) // frame_interval
            if max_frames:
                estimated_total_frames = min(estimated_total_frames, max_frames)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Extract frame at specified intervals
                if frame_count % frame_interval == 0:
                    # Save frame as JPEG
                    frame_filename = os.path.join(
                        output_folder, f"frame_{extracted_count:06d}.jpg"
                    )
                    cv2.imwrite(frame_filename, frame)
                    extracted_count += 1

                    # Report progress for every extracted frame
                    if progress_callback:
                        # Calculate percentage (30% is the start of extraction phase)
                        progress_percent = 30 + int(
                            (extracted_count / max(1, estimated_total_frames)) * 65
                        )
                        # Ensure progress doesn't exceed 100%
                        progress_percent = min(progress_percent, 100)
                        progress_callback(
                            progress_percent, f"Extracted {extracted_count} frames..."
                        )

                    # Check if we've reached max_frames limit
                    if max_frames and extracted_count >= max_frames:
                        break

                frame_count += 1

            cap.release()
            logger.info(
                f"Successfully extracted {extracted_count} frames from {video_path}"
            )
            return extracted_count, actual_fps

        except Exception as e:
            logger.error(f"Error extracting frames from video {video_path}: {e}")
            raise RuntimeError(f"Error extracting frames from video: {e}")

    @staticmethod
    def extract_frames_at_fps(
        video_path: str,
        output_folder: str,
        target_fps: float,
        max_frames: Optional[int] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Tuple[int, float]:
        """Extract frames from video at a target frame rate.

        Args:
            video_path: Path to the video file
            output_folder: Path to output folder for extracted frames
            target_fps: Target frames per second for extraction
            max_frames: Maximum number of frames to extract
            progress_callback: Optional callback function to report progress (value, message)

        Returns:
            Tuple of (number of frames extracted, actual fps achieved)

        Raises:
            ValueError: If video file cannot be opened or parameters are invalid
            RuntimeError: If frame extraction fails
        """
        # Validate inputs
        if target_fps <= 0:
            raise ValueError("Target FPS must be positive")

        if max_frames is not None and max_frames <= 0:
            raise ValueError("Max frames must be positive or None")

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")

            video_fps = cap.get(cv2.CAP_PROP_FPS)
            if video_fps <= 0:
                logger.warning(
                    f"Invalid FPS detected, using default 30.0 for video {video_path}"
                )
                video_fps = 30.0  # Default fallback

            # Calculate frame interval based on target FPS
            frame_interval = int(round(video_fps / target_fps))
            if frame_interval < 1:
                frame_interval = 1

            # If target FPS is higher than video FPS, extract every frame
            if target_fps >= video_fps:
                frame_interval = 1
                actual_fps = video_fps
            else:
                actual_fps = video_fps / frame_interval

            cap.release()

            # Use the frame interval extraction method
            return VideoUtils.extract_frames_from_video(
                video_path, output_folder, frame_interval, max_frames, progress_callback
            )

        except Exception as e:
            logger.error(
                f"Error extracting frames at target FPS from video {video_path}: {e}"
            )
            raise RuntimeError(f"Error extracting frames at target FPS: {e}")
