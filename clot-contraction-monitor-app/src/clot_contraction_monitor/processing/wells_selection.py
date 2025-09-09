import cv2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle


def moving_average(x, w):
    x_padded = np.pad(x, (w // 2, w - 1 - w // 2), mode="edge")
    return np.convolve(x_padded, np.ones(w), "valid") / w


def find_nearests(value, array, threshold):
    dists = np.linalg.norm(array - value, axis=1)
    return np.argwhere(dists < threshold)


def bubble_sort(arr, threshold):
    def compare(x, y):
        if np.abs(x[1] - y[1]) < threshold:
            return x[0] > y[0]
        else:
            return x[1] > y[1]

    n = len(arr)
    for i in range(n - 1):
        for j in range(0, n - i - 1):
            if compare(arr[j], arr[j + 1]):
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def merge_nearests(array, threshold):
    merged = []
    merged_array = []
    for i in range(array.shape[0]):
        if i in merged:
            continue
        nearests = find_nearests(array[i], array, threshold)
        merged.extend(nearests)
        merged_array.append(array[nearests].mean(axis=0)[0])

    merged_array = bubble_sort(merged_array, threshold)

    return np.squeeze(np.array(merged_array))


def find_wells(image_np: np.ndarray, n_wells_x=8, n_wells_y=5, threshold: int = 50):
    circles = cv2.HoughCircles(
        image_np,
        cv2.HOUGH_GRADIENT_ALT,
        dp=2,
        minDist=50,
        param1=100,
        param2=0.9,
        minRadius=int(image_np.shape[0] // (n_wells_x * 2)),
        maxRadius=int(image_np.shape[0] // (n_wells_x * 0.75)),
    )

    centers = merge_nearests(circles[0, :, 0:2], threshold=threshold)
    average_radius = circles[0, :, 2].mean()

    return centers, average_radius


def plot_wells(image_np, centers, average_radius):
    fig, ax = plt.subplots(1, 1, figsize=(9, 6))
    ax.imshow(image_np, cmap="gray")
    for i, (xx, yy) in enumerate(centers):
        circ = Circle((xx, yy), average_radius, fill=False, color="blue")
        ax.add_patch(circ)
        ax.text(xx, yy, i, ha="center", va="center", color="red")


def make_well_masks(image_shape, centers, average_radius) -> np.ndarray:
    """Create binary masks for each well based on detected centers and radius.

    This function generates a binary mask for each well in an image, where each
    well is represented as a circular region around its center. The masks are
    used to isolate individual wells for further analysis or processing.
    Args:
        image_shape (tuple): The shape of the input image as (height, width).
        centers (np.ndarray): Array of center coordinates for each well, where each
                              row represents (x, y) coordinates.
        average_radius (float): The average radius of the wells to be masked.
    Returns:
        np.ndarray: A list of binary masks, each corresponding to a well in the image.
              Each mask is a 2D numpy array of the same shape as the input image,
              with 1s inside the well region and 0s elsewhere.
    """
    mask = np.zeros((centers.shape[0],) + image_shape, dtype=np.uint8)
    for i, (xx, yy) in enumerate(centers):
        mask[i, :, :] = cv2.circle(
            np.zeros(image_shape), (int(xx), int(yy)), int(average_radius), 1, -1
        )
    return mask


def circle_mask(average_radius):
    size = int(average_radius) * 2 + 1
    well_mask = np.zeros((size, size))
    well_mask = cv2.circle(
        well_mask,
        (int(average_radius), int(average_radius)),
        int(average_radius),
        1,
        -1,
    )
    return well_mask


def get_well_images(image_np, centers, average_radius, well_mask=None):
    well_images = []
    if well_mask is None:
        well_mask = circle_mask(average_radius)

    radius = int(average_radius)
    size = 2 * radius + 1

    center: np.ndarray
    for center in centers:
        center = center.astype(int)

        # Calculate slice bounds considering image borders
        y_start = max(0, center[1] - radius)
        y_end = min(center[1] + radius + 1, image_np.shape[0])
        x_start = max(0, center[0] - radius)
        x_end = min(center[0] + radius + 1, image_np.shape[1])

        # Slice the image
        sliced_image = image_np[y_start:y_end, x_start:x_end]

        # Calculate offsets for placement in well_image
        y_offset = radius - (center[1] - y_start)
        x_offset = radius - (center[0] - x_start)

        # Create well_image of full size
        well_image = np.zeros((size, size), dtype=sliced_image.dtype)

        # Place the masked sliced image at the correct position
        well_image[
            y_offset : y_offset + sliced_image.shape[0],
            x_offset : x_offset + sliced_image.shape[1],
        ] = sliced_image
        well_image = well_image * well_mask
        well_images.append(well_image)
    return np.array(well_images)
