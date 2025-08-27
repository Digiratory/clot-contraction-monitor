import onnxruntime
import numpy as np
import cv2
import cell_contraction_monitor.processing.wells_selection as ccm_ws

class CellInWellSegmentatior():
    TARGET_SHAPE = 384

    def __init__(self, onnx_model_path: str):
        self._onnx_model_path = onnx_model_path

        self.sess_options = onnxruntime.SessionOptions()
        self.sess_options.graph_optimization_level = (
            onnxruntime.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
        )
        self.ort_session = onnxruntime.InferenceSession(
            self._onnx_model_path,
            providers=["CPUExecutionProvider"],
            sess_options=self.sess_options,
        )

    def process_image(self, image_np: np.ndarray):
        if len(image_np.shape) == 3:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
            
        centers, well_radius = ccm_ws.find_wells(image_np)
        well_images, well_masks = ccm_ws.get_well_images(
            image_np, centers, well_radius)
        
        cell_masks = []
        for i, well_image in enumerate(well_images):
            well_image = self._preprocess_well(well_image)
            cell_mask = self._segment_cell(well_image)
            cell_masks.append(cell_mask)

        return centers.astype(int), well_radius, cell_masks

    def _preprocess_well(self, well_image: np.ndarray) -> np.ndarray:
        border_size = CellInWellSegmentatior.TARGET_SHAPE - well_image.shape[0]
        if border_size % 2 == 1:
            top = border_size // 2
            bottom = top + 1
        else:
            top = bottom = border_size // 2

        well_image = cv2.copyMakeBorder(
            well_image, top, bottom, top, bottom, cv2.BORDER_CONSTANT, None, 0)
        well_image = well_image.astype(np.float32) / 255.0
        return well_image

    def _segment_cell(self, well_image: np.ndarray) -> np.ndarray:
        ort_inputs_1 = {
            self.ort_session.get_inputs()[0].name: well_image[np.newaxis, np.newaxis, :]
        }

        mask = self.ort_session.run(None, ort_inputs_1)[0][0]
        return np.argmax(mask, axis=0)