"""CSV export utilities for the cell contraction monitor application."""

import csv
import os
from typing import List

import numpy as np


def export_to_csv(
    cell_sizes: np.ndarray, output_path: str, image_paths: List[str]
) -> None:
    """Export cell size data to CSV format.

    Args:
        cell_sizes: Array of cell sizes with shape (num_images, num_wells)
        output_path: Path to save the CSV file
        image_paths: List of image file paths for row labels
    """
    num_images, num_wells = cell_sizes.shape

    # Create column headers (Well_1, Well_2, ..., Well_N)
    headers = ["Sample"] + [f"Well_{i+1}" for i in range(num_wells)]

    with open(output_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)

        # Write headers
        writer.writerow(headers)

        # Write data rows
        for i in range(num_images):
            # Use image filename as sample identifier
            sample_name = os.path.splitext(os.path.basename(image_paths[i]))[0]
            row = [sample_name] + cell_sizes[i].tolist()
            writer.writerow(row)
