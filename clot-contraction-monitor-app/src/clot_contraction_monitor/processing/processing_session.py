import logging
import os
from glob import glob
from typing import Any, Callable, Dict, List, Optional, Tuple

import clot_contraction_monitor.io.utils as io_utils
import cv2
import numpy as np
from clot_contraction_monitor.annotators.cell_annotator import decorate_with_mask
from clot_contraction_monitor.io.annotation_utils import (
    check_annotation_version,
    get_find_all_frames,
    get_last_processed_frame,
    load_annotation,
    save_annotation,
)
from clot_contraction_monitor.processing.clot_in_well_segmentatior import (
    CellInWellSegmentatior,
)
from clot_contraction_monitor.project_settings import ProjectSettings


class ProcessingSession:
    """Manages the processing pipeline for cell contraction analysis.

    This class orchestrates the loading, processing, and analysis of image data
    from biological experiments, including well detection, cell segmentation,
    and quantitative analysis.
    """

    WELLS_COUNT = 40
    TARGET_WIDTH = 960
    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        """Initialize the processing session with default settings."""
        # TODO: implement logic to save processing results into persistance storage.
        try:
            self.segmentator = CellInWellSegmentatior(
                os.path.join(
                    os.path.dirname(__file__), "..", "assets", "optimized_model.onnx"
                )
            )
            self.logger.info("Processing session initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize segmentator: {e}")
            raise

        self.on_project_loaded_handlers: List[Callable[["ProcessingSession"], None]] = (
            []
        )
        self.images: List[str] = []
        # centers, well_radius, cell_masks
        self.annotations: List[Tuple[np.ndarray, float, List[np.ndarray]]] = []
        self.cell_sizes: Optional[np.ndarray] = None
        self.image_cache: Dict[Tuple[int, bool], np.ndarray] = {}

    def add_on_project_loaded_handler(
        self, handler: Callable[["ProcessingSession"], None]
    ) -> None:
        """Add a callback handler to be called when processing is complete.

        Args:
            handler: Function to call when project loading is complete
        """
        self.on_project_loaded_handlers.append(handler)

    def select_folder(
        self,
        folder_path: str,
        ext: str = "JPG",
        settings: Optional[ProjectSettings] = None,
    ) -> bool:
        """Select and load images from a folder for processing.

        Args:
            folder_path: Path to the folder containing image files
            ext: File extension to filter (default: "JPG")
            settings: Project settings to use for processing

        Returns:
            True if successful, False otherwise
        """
        try:
            self.images = get_find_all_frames(folder_path, ext)
            self.annotations = []
            self.image_cache = {}

            # Use wells count from settings or default
            wells_count = (
                settings.wells_count if settings else ProcessingSession.WELLS_COUNT
            )

            # Initialize annotations and cell sizes
            wells_founded = False
            for i, img in enumerate(self.images):
                # Try to find wells in the first image for reference
                image_np = io_utils.read_image(img)
                if image_np is not None:
                    wells_founded = self.segmentator.predefine_wells(
                        image_np, target_count=wells_count
                    )
                    if wells_founded:
                        self.logger.info(
                            f"Found all wells in {i} image, processing {len(self.images)} images"
                        )
                        break
                else:
                    self.logger.error("Failed to read {i} image for well detection")
                    return False
            if not wells_founded:
                self.logger.warning("Could not predefine wells in images")
                return False

            # Initialize cell sizes array with configured wells count
            if len(self.images) > 0:
                self.cell_sizes = np.zeros((len(self.images), wells_count), dtype=float)
            else:
                self.cell_sizes = None

            # Store project settings for later use
            self.project_settings = settings

            self._on_project_loaded()
            return True
        except Exception as e:
            self.logger.error(f"Error in select_folder: {e}")
            return False

    def load_project(self, callback: Callable[[int, bool, bool], None]) -> bool:
        """Load and process images in the current session.

        This method may loads annotations from existing JSON files and populates
        the session with previously processed data, allowing for resuming
        interrupted processing sessions.

        Args:
            callback: Function to call with progress updates (frame index, is frame from cache, is last frame)

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.images:
                self.logger.warning("No images to process")
                return False

            # Check for existing annotations and resume from last processed frame
            last_processed = get_last_processed_frame(
                self.images[0] if self.images else "", "JPG"
            )
            self.logger.info(f"Resuming from frame {last_processed}")

            for i, img_path in enumerate(self.images):
                from_cache = False
                try:
                    # Check if we have existing annotation for this frame
                    centers, well_radius, cell_masks, version = load_annotation(
                        img_path
                    )

                    # If we have valid existing annotation and it's the correct version, use it
                    if (
                        centers is not None
                        and well_radius is not None
                        and cell_masks is not None
                        and check_annotation_version(version)
                    ):
                        self.logger.info(f"Using existing annotation for frame {i}")
                        self.annotations.append((centers, well_radius, cell_masks))
                        from_cache = True
                    else:
                        # Process image normally and save annotation
                        self.logger.info(f"Processing new frame {i}")
                        image_np = io_utils.read_image(img_path)
                        if image_np is None:
                            self.logger.warning(f"Could not read image: {img_path}")
                            continue
                        centers, well_radius, cell_masks = self._process_image(image_np)
                        self.annotations.append((centers, well_radius, cell_masks))

                        # Clear cache for this frame
                        keys_to_delete = [
                            key for key in self.image_cache if key[0] == i
                        ]
                        for key in keys_to_delete:
                            del self.image_cache[key]

                        # Save the annotation for persistence
                        if not save_annotation(
                            img_path, centers, well_radius, cell_masks
                        ):
                            self.logger.warning(
                                f"Failed to save annotation for frame {i}"
                            )

                    if self.cell_sizes is not None and i < len(self.cell_sizes):
                        # Sum over height and width
                        self.cell_sizes[i] = np.sum(cell_masks, axis=(1, 2))

                    callback(i, from_cache, i == len(self.images) - 1)
                except Exception as e:
                    self.logger.error(f"Error processing image {img_path}: {e}")
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

    def _process_image(
        self, image_np: np.ndarray
    ) -> Tuple[np.ndarray, float, List[np.ndarray]]:
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

            cache_key = (img_idx, annotated)
            if cache_key in self.image_cache:
                return self.image_cache[cache_key]

            image_np = io_utils.read_image(self.images[img_idx])
            if image_np is None:
                return None

            # Convert grayscale to RGB if needed
            if len(image_np.shape) == 2:
                scene = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
            else:
                scene = image_np.copy()

            # Resize to reduced size
            scale = min(1.0, ProcessingSession.TARGET_WIDTH / scene.shape[1])
            scene = cv2.resize(scene, (0, 0), fx=scale, fy=scale)

            # Add annotations if requested and available
            if annotated and img_idx < len(self.annotations):
                centers, well_radius, cell_masks = self.annotations[img_idx]
                # Scale annotations
                centers = (centers * scale).astype(int)
                well_radius = int(well_radius * scale)
                cell_masks = [
                    cv2.resize(
                        mask,
                        (0, 0),
                        fx=scale,
                        fy=scale,
                        interpolation=cv2.INTER_NEAREST,
                    )
                    for mask in cell_masks
                ]
                # Scale decoration parameters
                font_scale = 3 * scale
                thickness = max(1, int(2 * scale))
                circle_thickness = max(1, int(3 * scale))
                scene = decorate_with_mask(
                    scene,
                    centers,
                    well_radius,
                    cell_masks,
                    font_scale,
                    thickness,
                    circle_thickness,
                )

            self.image_cache[cache_key] = scene
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

    def get_clot_sizes(self) -> Optional[np.ndarray]:
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
