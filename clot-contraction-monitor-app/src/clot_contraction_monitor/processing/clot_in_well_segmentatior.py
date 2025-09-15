import os

import clot_contraction_monitor.processing.wells_selection as ccm_ws
import cv2
import numpy as np

if os.name == "nt":
    try:
        import onnxruntime.tools.add_openvino_win_libs as utils

        utils.add_openvino_libs_to_path()
    except:
        pass
import onnxruntime


def get_onnx_providers():
    available_providers = onnxruntime.get_available_providers()
    providers = []
    provider_options = []

    if "DmlExecutionProvider" in available_providers:
        providers.append("DmlExecutionProvider")
        provider_options.append({})

    if "OpenVINOExecutionProvider" in available_providers:
        from openvino import Core

        ov_devs = Core().available_devices

        providers.append("OpenVINOExecutionProvider")
        provider_options.append({"device_type": "GPU" if "GPU" in ov_devs else "AUTO"})

    providers.append("CPUExecutionProvider")
    provider_options.append({})
    return providers, provider_options


class CellInWellSegmentatior:
    TARGET_SHAPE = 192

    def __init__(self):

        self.sess_options = onnxruntime.SessionOptions()
        self.sess_options.graph_optimization_level = (
            onnxruntime.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
        )

        self.providers, self.provider_options = get_onnx_providers()
        self._onnx_model_path = None
        self.ort_session = None

        self.centers = None
        self.well_radius = None
        self.well_mask = None

    def _load_model(self, batch_size: int):
        if batch_size == 40:
            self._onnx_model_path = os.path.join(
                os.path.dirname(__file__), "..", "assets", "optimized_model_40.onnx"
            )
        elif batch_size == 96:
            self._onnx_model_path = os.path.join(
                os.path.dirname(__file__), "..", "assets", "optimized_model_96.onnx"
            )
        else:
            raise ValueError(f"Unsupported batch size {batch_size}")
        self.ort_session = onnxruntime.InferenceSession(
            self._onnx_model_path,
            providers=self.providers,
            provider_options=self.provider_options,
            sess_options=self.sess_options,
        )

    def predefine_wells(
        self,
        image_np: np.ndarray,
        target_count: int,
        culture_plate_format: tuple[int, int],
    ) -> bool:
        """Predefines well locations and properties for subsequent cell segmentation processing.

        This method analyzes an input image to detect circular wells arranged in a grid layout.
        It uses automated well detection algorithms to identify the centers and radius of wells,
        then validates that the detected well count matches the expected target count. If successful,
        it stores the well parameters for use in subsequent processing steps.

        Args:
            image_np (np.ndarray): Input image containing the well plate. Can be grayscale or BGR color image.
                If color image, it will be automatically converted to grayscale for processing.
            target_count (int): Expected number of wells that should be detected in the image.
                The method will only succeed if exactly this number of wells are found.
            culture_plate_format (tuple[int, int]): Expected grid dimensions as (number_of_wells_x, number_of_wells_y).
                Used to guide the well detection algorithm with prior knowledge of the plate layout.

        Returns:
            bool: True if wells were successfully detected and match the target count,
                False if the detected well count doesn't match the target or detection failed.

        Note:
            Stores detected well centers, radius, circular mask and grid dimensions in instance variables
            (self.centers, self.well_radius, self.well_mask, self.culture_plate_format) for use by process_image method.
        """
        if len(image_np.shape) == 3:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        centers, well_radius = ccm_ws.find_wells(
            image_np,
            n_wells_x=culture_plate_format[0],
            n_wells_y=culture_plate_format[1],
        )
        if centers.shape[0] == target_count:
            self.centers = centers
            self.well_radius = well_radius
            self.well_mask = ccm_ws.circle_mask(well_radius)
            self.culture_plate_format = culture_plate_format
            self._load_model(target_count)
            return True
        else:
            return False

    def process_image(
        self, image_np: np.ndarray, culture_plate_format: tuple[int, int] = None
    ):
        if len(image_np.shape) == 3:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)

        if self.centers is None:
            centers, well_radius = ccm_ws.find_wells(
                image_np,
                n_wells_x=culture_plate_format[0],
                n_wells_y=culture_plate_format[1],
            )
            well_mask = ccm_ws.circle_mask(well_radius)
            culture_plate_format = culture_plate_format
        else:
            centers, well_radius, well_mask, culture_plate_format = (
                self.centers,
                self.well_radius,
                self.well_mask,
                self.culture_plate_format,
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
        cell_masks = self._postprocess_cell_batched(cell_masks, well_images.shape[1:])
        return centers.astype(int), well_radius, cell_masks

    def _preprocess_well(self, well_image: np.ndarray) -> np.ndarray:
        # border_size = CellInWellSegmentatior.TARGET_SHAPE - well_image.shape[0]
        # if border_size % 2 == 1:
        #     top = border_size // 2
        #     bottom = top + 1
        # else:
        #     top = bottom = border_size // 2

        # well_image = cv2.copyMakeBorder(
        #     well_image, top, bottom, top, bottom, cv2.BORDER_CONSTANT, None, 0
        # )
        well_image = cv2.resize(
            well_image,
            (CellInWellSegmentatior.TARGET_SHAPE, CellInWellSegmentatior.TARGET_SHAPE),
            dst=well_image,
            interpolation=cv2.INTER_CUBIC,
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
        return masks

    def _postprocess_cell_batched(
        self, masks_predicted: np.ndarray, source_shape: tuple[int, int]
    ):
        orig_size_masks = np.zeros(
            (
                masks_predicted.shape[0],
                source_shape[0],
                source_shape[1],
            ),
            dtype=np.uint8,
        )
        for i, mask in enumerate(masks_predicted):
            contour, hier = cv2.findContours(
                mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
            )
            for cnt in contour:
                cv2.drawContours(mask, [cnt], 0, 1, -1)

            orig_size_masks[i] = cv2.resize(
                mask,
                source_shape,
                dst=mask,
                interpolation=cv2.INTER_NEAREST,
            )
        return orig_size_masks
