import os
import cv2
import numpy as np
from glob import glob
from typing import Callable, List, Tuple, Optional, Any
import logging

import cell_contraction_monitor.io.utils as io_utils
from cell_contraction_monitor.processing.cell_in_well_segmentatior import CellInWellSegmentatior
from cell_contraction_monitor.annotators.cell_annotator import decorate_with_cells


class ProcessingSession:
    """Manages the processing pipeline for cell contraction analysis.

    This class orchestrates the loading, processing, and analysis of image data
    from biological experiments, including well detection, cell segmentation,
    and quantitative analysis.
    """

    WELLS_COUNT = 40
    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        """Initialize the processing session with default settings."""
        try:
            self.segmentator = CellInWellSegmentatior("./models/model.onnx")
            self.logger.info("Processing session initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize segmentator: {e}")
            raise

        self.on_project_loaded_handlers: List[Callable[[
            "ProcessingSession"], None]] = []
        self.images: List[str] = []
        # centers, well_radius, cell_masks
        self.annotations: List[Tuple[np.ndarray, float, List[np.ndarray]]] = []
        self.cell_sizes: Optional[np.ndarray] = None

    def add_on_project_loaded_handler(self, handler: Callable[["ProcessingSession"], None]) -> None:
        """Add a callback handler to be called when processing is complete.

        Args:
            handler: Function to call when project loading is complete
        """
        self.on_project_loaded_handlers.append(handler)

    def select_folder(self, folder_path: str, ext: str = "JPG") -> bool:
        """Select and load images from a folder for processing.

        Args:
            folder_path: Path to the folder containing image files
            ext: File extension to filter (default: "JPG")

        Returns:
            True if successful, False otherwise
        """
        try:
            self.images = sorted(glob(os.path.join(folder_path, f"*.{ext}")))
            self.annotations = []

            # Initialize annotations and cell sizes
            if len(self.images) > 0:
                # Try to find wells in the first image for reference
                first_image = io_utils.read_image(self.images[0])
                if first_image is not None:
                    if self.segmentator.predefine_wells(first_image, target_count=ProcessingSession.WELLS_COUNT):
                        self.logger.info(
                            f"Found wells in first image, processing {len(self.images)} images")
                    else:
                        self.logger.warning(
                            "Could not predefine wells in first image")
                else:
                    self.logger.error(
                        "Failed to read first image for well detection")
                    return False
            else:
                self.logger.warning("No images found in folder")
                return False

            # Initialize cell sizes array
            if len(self.images) > 0:
                self.cell_sizes = np.zeros(
                    (len(self.images), ProcessingSession.WELLS_COUNT), dtype=float)
            else:
                self.cell_sizes = None

            self._on_project_loaded()
            return True
        except Exception as e:
            self.logger.error(f"Error in select_folder: {e}")
            return False

    def load_project(self, callback: Callable[[int], None]) -> bool:
        """Load and process all images in the current session.

        Args:
            callback: Function to call with progress updates (frame index)

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.images:
                self.logger.warning("No images to process")
                return False

            for i, img_path in enumerate(self.images):
                try:
                    image_np = io_utils.read_image(img_path)
                    if image_np is None:
                        self.logger.warning(
                            f"Could not read image: {img_path}")
                        continue

                    centers, well_radius, cell_masks = self._process_image(
                        image_np)
                    self.annotations.append((centers, well_radius, cell_masks))
                    if self.cell_sizes is not None and i < len(self.cell_sizes):
                        # Sum over height and width
                        self.cell_sizes[i] = np.sum(cell_masks, axis=(1, 2))
                    callback(i)
                except Exception as e:
                    self.logger.error(
                        f"Error processing image {img_path}: {e}")
                    continue

            return True
        except Exception as e:
            self.logger.error(f"Error in load_project: {e}")
            return False

    def _on_project_loaded(self) -> None:
        """Handle the event when project loading is complete."""
        for handler in self.on_project_loaded_handlers:
            try:
                handler(self)
            except Exception as e:
                self.logger.error(f"Error in project loaded handler: {e}")

    def _process_image(self, image_np: np.ndarray) -> Tuple[np.ndarray, float, List[np.ndarray]]:
        """Process a single image through the segmentation pipeline.

        Args:
            image_np: Input image array

        Returns:
            Tuple of (centers, well_radius, cell_masks)
        """
        try:
            return self.segmentator.process_image(image_np)
        except Exception as e:
            self.logger.error(f"Error in _process_image: {e}")
            # Return default values on error
            return np.array([]), 0.0, []

    def get_image(self, img_idx: int, annotated: bool = False) -> Optional[np.ndarray]:
        """Get a processed image with optional annotations.

        Args:
            img_idx: Index of the image to retrieve
            annotated: Whether to include annotation overlays

        Returns:
            Image array or None if not available
        """
        try:
            if img_idx >= len(self.images):
                return None

            image_np = io_utils.read_image(self.images[img_idx])
            if image_np is None:
                return None

            # Convert grayscale to RGB if needed
            if len(image_np.shape) == 2:
                scene = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
            else:
                scene = image_np.copy()

            # Add annotations if requested and available
            if annotated and img_idx < len(self.annotations):
                centers, well_radius, cell_masks = self.annotations[img_idx]
                scene = decorate_with_cells(
                    scene, centers, well_radius, cell_masks)

            return scene
        except Exception as e:
            self.logger.error(f"Error in get_image: {e}")
            return None

    def frame_count(self) -> int:
        """Get the total number of frames in the session.

        Returns:
            Number of frames
        """
        return len(self.images)

    def get_cell_sizes(self) -> Optional[np.ndarray]:
        """Get the cell size measurements for all frames and wells.

        Returns:
            Array of cell sizes or None if not available
        """
        return self.cell_sizes

    def get_frame_data(self, frame_idx: int) -> Optional[np.ndarray]:
        """Get raw frame data without annotations (for preview purposes).

        Args:
            frame_idx: Index of the frame to retrieve

        Returns:
            Raw image data or None if not available
        """
        try:
            if frame_idx >= len(self.images):
                return None
            return io_utils.read_image(self.images[frame_idx])
        except Exception as e:
            self.logger.error(f"Error in get_frame_data: {e}")
            return None
