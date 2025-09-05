import cv2
import numpy as np


def read_image(im_path: str) -> np.ndarray:
    """
    Read an image from the specified file path using OpenCV.

    This function loads an image from a given file path and returns it as a NumPy array.
    The image is loaded in BGR color format by default, which is the standard format used by OpenCV.

    Example:
    >>> img = read_image('path/to/image.jpg')
    >>> print(img.shape)
    (480, 640, 3)

    Note:
    If the image file path is invalid or the file format is not supported, the function will
    return None.

    Args:
        im_path (str): The file path to the image that needs to be read. This should be a valid
                       path to an image file (e.g., .jpg, .png, .bmp).

    Returns:
        np.ndarray: The image as a NumPy array with shape (height, width, channels) if the image
                    is color, or (height, width) if it's grayscale. Returns None if the image
                    cannot be loaded.
    """
    return cv2.imdecode(np.fromfile(im_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)


def write_image(im_path: str, image_np: np.ndarray):
    """
    Write an image to the specified file path using OpenCV.

    This function saves a NumPy array representing an image to a file at the given path.
    The image format is determined by the file extension in the path. The function handles
    both color and grayscale images correctly, preserving the original data type and dimensions.

    Example:
    >>> img = read_image('path/to/image.jpg')
    >>> write_image('output/path/new_image.png', img)

    Args:
        im_path (str): The file path where the image will be saved. The file extension
                       determines the format of the saved image (e.g., .jpg, .png, .bmp).
        image_np (np.ndarray): The image to be saved as a NumPy array. It should have
                               shape (height, width, channels) for color images or
                               (height, width) for grayscale images.
    """
    cv2.imencode(".jpg", image_np)[1].tofile(im_path)
