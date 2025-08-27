import os
import cv2
import numpy as np
from glob import glob
from typing import Callable

import cell_contraction_monitor.io.utils as io_utils
from cell_contraction_monitor.processing.cell_in_well_segmentatior import CellInWellSegmentatior
from cell_contraction_monitor.annotators.cell_annotator import decorate_with_cells


class ProcessingSession:
    WELLS_COUNT = 40
    def __init__(self):
        self.segmentator = CellInWellSegmentatior("./models/model.onnx")

        self.on_project_loaded_handlers: list[Callable[[
            ProcessingSession], None]] = []
        self.images: list[str] = []
        self.annotations: list = []  # centers, well_radius, cell_masks
        self.cell_sizes: np.ndarray | None = None

    def add_on_project_loaded_handler(self, handler: Callable[[int], None]):
        self.on_project_loaded_handlers.append(handler)

    def select_folder(self, folder_path, ext="JPG"):
        self.images = sorted(glob(os.path.join(folder_path, f"*.{ext}")))
        self.annotations = []
        for i, img in enumerate(self.images):
            image_np = io_utils.read_image(img)
            if self.segmentator.predefine_wells(image_np, target_count=ProcessingSession.WELLS_COUNT):
                break
        self.cell_sizes = np.zeros((len(self.images), ProcessingSession.WELLS_COUNT), dtype=float)
        self._on_project_loaded()

    def load_project(self, callback: Callable):
        for i, img in enumerate(self.images):
            image_np = io_utils.read_image(img)
            centers, well_radius, cell_masks = self._process_image(image_np)
            self.annotations.append((centers, well_radius, cell_masks))
            self.cell_sizes[i] = np.sum(cell_masks, axis=(1,2))
            callback(i)

    def _on_project_loaded(self):
        for on_project_loaded_handler in self.on_project_loaded_handlers:
            on_project_loaded_handler(self)

    def _process_image(self, image_np):
        return self.segmentator.process_image(image_np)

    def get_image(self, img_idx: int, annotated: bool = False):
        image_np = io_utils.read_image(self.images[img_idx])

        if len(image_np.shape) == 2:
            scene = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)

        if img_idx < len(self.annotations):
            centers, well_radius, cell_masks = self.annotations[img_idx]
            scene = decorate_with_cells(
                scene, centers, well_radius, cell_masks)
        return scene

    def frame_count(self):
        return len(self.images)

    def get_cell_sizes(self):
        return self.cell_sizes
