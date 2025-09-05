import cv2
import numpy as np


def overlay_image_alpha(img, img_overlay, pos, alpha_mask):
    """Overlay `img_overlay` onto `img` at (x, y) and blend using `alpha_mask`.

    `alpha_mask` must have same HxW as `img_overlay` and values in range [0, 1].
    """
    x, y = pos
    # Image ranges
    if img is None or img_overlay is None:
        print("WTF")
    y1, y2 = max(0, y), min(img.shape[0], y + img_overlay.shape[0])
    x1, x2 = max(0, x), min(img.shape[1], x + img_overlay.shape[1])

    # Overlay ranges
    y1o, y2o = max(0, -y), min(img_overlay.shape[0], img.shape[0] - y)
    x1o, x2o = max(0, -x), min(img_overlay.shape[1], img.shape[1] - x)

    # Exit if nothing to do
    if y1 >= y2 or x1 >= x2 or y1o >= y2o or x1o >= x2o:
        return

    # Blend overlay within the determined ranges
    img_crop = img[y1:y2, x1:x2]
    img_overlay_crop = img_overlay[y1o:y2o, x1o:x2o]
    alpha = alpha_mask[y1o:y2o, x1o:x2o, np.newaxis] * 0.25
    alpha_inv = 1.0 - alpha

    img[y1:y2, x1:x2] = alpha * img_overlay_crop + alpha_inv * img_crop
    return img


def decorate_with_mask(
    full_img: np.ndarray,
    centers: list,
    well_radius: float,
    masks: np.ndarray,
    font_scale: float = 3,
    thickness: int = 2,
    circle_thickness: int = 3,
) -> np.ndarray:
    scene = np.array(full_img, copy=True, dtype=np.uint8)

    fontFace = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = font_scale
    color = (255, 0, 255)  # Green color (BGR)
    lineType = cv2.LINE_AA

    for i, clot_mask in enumerate(masks):
        clot_overlay = np.zeros(clot_mask.shape + (3,), dtype=np.uint8)
        clot_overlay[:, :, 1] = 255
        scene = overlay_image_alpha(
            scene,
            clot_overlay,
            centers[i] - np.array(clot_mask.shape[0]) // 2,
            clot_mask,
        )

    for i, well_center in enumerate(centers):
        scene = cv2.circle(
            scene, well_center, int(well_radius), (0, 0, 255), circle_thickness
        )
        scene = cv2.putText(
            scene,
            f"{i+1}",
            well_center,
            fontFace,
            fontScale,
            color,
            thickness,
            lineType,
        )

    return scene
