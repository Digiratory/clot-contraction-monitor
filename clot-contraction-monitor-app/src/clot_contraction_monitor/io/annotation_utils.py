"""
Utility functions for handling annotation I/O operations with version tracking.
"""

import base64
import gzip
import hashlib
import json
import os
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, List, Optional, Tuple

import numpy as np

# Current version of the processing session
CURRENT_VERSION = "1.0.0"


def decompress_bytes_to_string(inputBytes: bytes) -> str:
    """
    decompress the given byte array (which must be valid
    compressed gzip data) and return the decoded text (utf-8).
    """
    bio = BytesIO()
    stream = BytesIO(inputBytes)
    decompressor = gzip.GzipFile(fileobj=stream, mode="r")
    while True:  # until EOF
        chunk = decompressor.read(8192)
        if not chunk:
            decompressor.close()
            bio.seek(0)
            return bio.read().decode("utf-8")
        bio.write(chunk)
    return None


def compress_string_to_bytes(inputString: str) -> bytes:
    """
    read the given string, encode it in utf-8,
    compress the data and return it as a byte array.
    """
    bio = BytesIO()
    bio.write(inputString.encode("utf-8"))
    bio.seek(0)
    stream = BytesIO()
    compressor = gzip.GzipFile(fileobj=stream, mode="w")
    while True:  # until EOF
        chunk = bio.read(8192)
        if not chunk:  # EOF?
            compressor.close()
            return stream.getvalue()
        compressor.write(chunk)


def get_annotation_path(
    image_path: str, annotation_suffix: str = ".annotation.json.gz"
) -> str:
    """
    Generate the annotation file path for a given image path.

    Args:
        image_path: Path to the source image file
        annotation_suffix: Suffix for annotation files (default: ".annotation.json.gz")

    Returns:
        Path to the corresponding annotation file
    """
    image_path_obj = Path(image_path)
    return str(image_path_obj.parent / f"{image_path_obj.stem}{annotation_suffix}")


def save_annotation(
    image_path: str,
    centers: np.ndarray,
    well_radius: float,
    cell_masks: List[np.ndarray],
    version: str = CURRENT_VERSION,
) -> bool:
    """
    Save annotation data as JSON file near the source image with version info.

    Args:
        image_path: Path to the source image file
        centers: Array of well center coordinates (x, y)
        well_radius: Radius of wells
        cell_masks: List of cell mask arrays
        version: Version identifier for current ProcessingSession version

    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert numpy arrays to lists for JSON serialization
        centers_list = centers.tolist() if isinstance(centers, np.ndarray) else centers
        cell_masks_list = [
            base64.b64encode(mask).decode("utf-8") for mask in cell_masks
        ]

        # Create annotation data structure with frame index based on file order
        annotation_data = {
            "version": version,
            "image_path": image_path,
            "frame_index": get_frame_index_from_path(image_path),
            "centers": centers_list,
            "well_radius": float(well_radius),
            "cell_masks": cell_masks_list,
            "cell_masks_shape": cell_masks[0].shape,
            "cell_masks_dtype": str(cell_masks[0].dtype),
        }

        # Get annotation file path
        annotation_path = get_annotation_path(image_path)

        # Save to JSON file
        if annotation_path.endswith(".gz"):
            jsonstring = json.dumps(annotation_data, indent=None)
            with open(annotation_path, "wb") as f:
                f.write(compress_string_to_bytes(jsonstring))
        else:
            with open(annotation_path, "w") as f:
                json.dump(annotation_data, f, indent=None)

        return True

    except Exception as e:
        print(f"Error saving annotation for {image_path}: {e}")
        return False


def load_annotation(
    image_path: str,
) -> Tuple[
    Optional[np.ndarray], Optional[float], Optional[List[np.ndarray]], Optional[str]
]:
    """
    Load existing annotation from JSON file with version validation.

    Args:
        image_path: Path to the source image file

    Returns:
        Tuple of (centers, well_radius, cell_masks, version) or (None, None, None, None) if failed
    """
    try:
        annotation_path = get_annotation_path(image_path)

        # Check if annotation file exists
        if not os.path.exists(annotation_path):
            return None, None, None, None

        # Load annotation data

        if annotation_path.endswith(".gz"):
            with open(annotation_path, "rb") as f:
                jsonstr = decompress_bytes_to_string(f.read())
                annotation_data = json.loads(jsonstr)
        else:
            with open(annotation_path, "r") as f:
                annotation_data = json.load(f)

        # Validate version
        version = annotation_data.get("version", "unknown")
        if not check_annotation_version(version):
            print(
                f"Version mismatch for {image_path}: expected {CURRENT_VERSION}, got {version}"
            )
            return None, None, None, None

        # Extract data
        centers = np.array(annotation_data.get("centers", []))
        well_radius = annotation_data.get("well_radius")
        cell_masks_list = annotation_data.get("cell_masks", [])
        cell_masks_shape = annotation_data.get("cell_masks_shape")
        cell_masks_dtype = annotation_data.get("cell_masks_dtype")
        # Convert masks back to numpy arrays
        cell_masks = (
            [
                np.frombuffer(
                    np.array(base64.b64decode(mask)), dtype=cell_masks_dtype
                ).reshape(cell_masks_shape)
                for mask in cell_masks_list
            ]
            if cell_masks_list
            else []
        )

        return centers, float(well_radius), cell_masks, version

    except Exception as e:
        print(f"Error loading annotation for {image_path}: {e}")
        return None, None, None, None


def check_annotation_version(version: str) -> bool:
    """
    Validate if annotation matches current processing version.

    Args:
        version: Version string from annotation file

    Returns:
        True if version is compatible, False otherwise
    """
    # For now, we'll do a simple equality check
    # In a more complex system, you might implement semantic versioning checks
    return version == CURRENT_VERSION


def get_frame_index_from_path(image_path: str) -> int:
    """
    Extract frame index from image path.

    Args:
        image_path: Path to the image file

    Returns:
        Frame index number
    """
    try:
        basename = os.path.basename(image_path)
        name_without_ext = os.path.splitext(basename)[0]

        # Try to extract number from filename (last sequence of digits)
        import re

        match = re.search(r"(\d+)$", name_without_ext)
        if match:
            return int(match.group(1))
        else:
            # Fallback: use file modification time as a rough index
            return int(os.path.getmtime(image_path) % 1000000)

    except Exception:
        # If we can't determine frame index, return 0
        return 0


def get_find_all_frames(folder_path: str, ext: str = "JPG") -> List[str]:
    image_files = sorted(
        [f for f in os.listdir(folder_path) if f.lower().endswith(f".{ext.lower()}")]
    )
    return [os.path.join(folder_path, img_file) for img_file in image_files]


def get_last_processed_frame(folder_path: str, ext: str = "JPG") -> int:
    """
    Get the index of the last processed frame based on existing annotations.

    Args:
        folder_path: Path to the folder containing image files
        ext: File extension to filter (default: "JPG")

    Returns:
        Index of last processed frame, or 0 if no frames processed
    """
    try:
        image_files = get_find_all_frames(folder_path, ext)
        annotation_files = []

        # Check which images have annotations
        for img_path in image_files:
            annotation_path = get_annotation_path(img_path)
            if os.path.exists(annotation_path):
                annotation_files.append((img_path, annotation_path))
        if not annotation_files:
            return 0
        # Find the highest frame index among annotated files
        last_frame_index = len(annotation_files)

        return last_frame_index

    except Exception as e:
        print(f"Error getting last processed frame: {e}")
        return 0


def clear_annotations(folder_path: str, ext: str = "JPG") -> int:
    """
    Remove all annotation files for a given folder.

    Args:
        folder_path: Path to the folder containing image files
        ext: File extension to filter (default: "JPG")

    Returns:
        Number of files removed
    """
    try:
        image_files = get_find_all_frames(folder_path, ext)
        removed_count = 0

        for img_path in image_files:
            annotation_path = get_annotation_path(img_path)
            if os.path.exists(annotation_path):
                os.remove(annotation_path)
                removed_count += 1

        return removed_count

    except Exception as e:
        print(f"Error clearing annotations: {e}")
        return 0
