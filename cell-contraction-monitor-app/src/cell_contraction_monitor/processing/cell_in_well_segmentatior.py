import os

import cell_contraction_monitor.processing.wells_selection as ccm_ws
import cv2
import numpy as np

if os.name == "nt":
    import onnxruntime.tools.add_openvino_win_libs as utils

    utils.add_openvino_libs_to_path()
import onnxruntime


def get_onnx_providers():
    available_providers = onnxruntime.get_available_providers()
    providers = []
    provider_options = []

    if "OpenVINOExecutionProvider" in available_providers:
        from openvino import Core

        ov_devs = Core().available_devices

        providers.append("OpenVINOExecutionProvider")
        provider_options.append({"device_type": "GPU" if "GPU" in ov_devs else "AUTO"})

    providers.append("CPUExecutionProvider")
    provider_options.append({})
    return providers, provider_options


class CellInWellSegmentatior:
    TARGET_SHAPE = 348

    def __init__(self, onnx_model_path: str):
        self._onnx_model_path = onnx_model_path

        self.sess_options = onnxruntime.SessionOptions()
        self.sess_options.graph_optimization_level = (
            onnxruntime.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
        )

        providers, provider_options = get_onnx_providers()
        self.ort_session = onnxruntime.InferenceSession(
            self._onnx_model_path,
            providers=providers,
            provider_options=provider_options,
            sess_options=self.sess_options,
        )
        self.centers = None
        self.well_radius = None
        self.well_mask = None

    def predefine_wells(self, image_np: np.ndarray, target_count) -> bool:
        if len(image_np.shape) == 3:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        centers, well_radius = ccm_ws.find_wells(image_np)
        if centers.shape[0] == target_count:
            self.centers = centers
            self.well_radius = well_radius
            self.well_mask = ccm_ws.circle_mask(well_radius)
            return True
        else:
            return False

    def process_image(self, image_np: np.ndarray):
        if len(image_np.shape) == 3:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)

        if self.centers is None:
            centers, well_radius = ccm_ws.find_wells(image_np)
            well_mask = ccm_ws.circle_mask(well_radius)
        else:
            centers, well_radius, well_mask = (
                self.centers,
                self.well_radius,
                self.well_mask,
            )

        well_images = ccm_ws.get_well_images(image_np, centers, well_radius, well_mask)

        cell_masks = []
        preprocessed_wells = []
        for i, well_image in enumerate(well_images):
            well_image = self._preprocess_well(well_image)
            preprocessed_wells.append(well_image)
        cell_masks = self._segment_cell_batched(
            np.array(preprocessed_wells, dtype=np.float32)
        )
        return centers.astype(int), well_radius, cell_masks

    def _preprocess_well(self, well_image: np.ndarray) -> np.ndarray:
        border_size = CellInWellSegmentatior.TARGET_SHAPE - well_image.shape[0]
        if border_size % 2 == 1:
            top = border_size // 2
            bottom = top + 1
        else:
            top = bottom = border_size // 2

        well_image = cv2.copyMakeBorder(
            well_image, top, bottom, top, bottom, cv2.BORDER_CONSTANT, None, 0
        )
        well_image = cv2.resize(
            well_image, (192, 192), dst=well_image, interpolation=cv2.INTER_CUBIC
        )
        well_image = well_image.astype(np.float32) / 255.0
        return well_image[np.newaxis, :]

    def _segment_cell(self, well_image: np.ndarray) -> np.ndarray:
        ort_inputs_1 = {
            self.ort_session.get_inputs()[0].name: well_image[np.newaxis, :]
        }

        mask = self.ort_session.run(None, ort_inputs_1)[0][0]
        mask = np.argmax(mask, axis=0).astype(np.uint8)
        mask = cv2.resize(
            mask,
            (CellInWellSegmentatior.TARGET_SHAPE, CellInWellSegmentatior.TARGET_SHAPE),
            dst=mask,
            interpolation=cv2.INTER_NEAREST,
        )
        return mask

    def _segment_cell_batched(self, well_images: np.ndarray) -> np.ndarray:
        ort_inputs_1 = {self.ort_session.get_inputs()[0].name: well_images}

        masks = self.ort_session.run(None, ort_inputs_1)[0]
        masks = np.argmax(masks, axis=1).astype(np.uint8)
        orig_size_masks = np.zeros(
            (
                masks.shape[0],
                CellInWellSegmentatior.TARGET_SHAPE,
                CellInWellSegmentatior.TARGET_SHAPE,
            ),
            dtype=np.uint8,
        )
        for i, mask in enumerate(masks):
            orig_size_masks[i] = cv2.resize(
                mask,
                (
                    CellInWellSegmentatior.TARGET_SHAPE,
                    CellInWellSegmentatior.TARGET_SHAPE,
                ),
                dst=mask,
                interpolation=cv2.INTER_NEAREST,
            )
        return orig_size_masks
