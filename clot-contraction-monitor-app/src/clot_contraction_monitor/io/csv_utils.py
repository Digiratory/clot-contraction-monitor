"""CSV export utilities for the cell contraction monitor application."""

import csv
import os
from typing import Dict, List, Optional

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


def export_analysis_results_to_csv(
    analysis_results: Optional[Dict[str, np.ndarray]],
    output_path: str,
    well_count: int = None,
) -> None:
    """Export analysis parameters to CSV format.

    Args:
        analysis_results: Dictionary containing parameter arrays or None
        output_path: Path to save the CSV file
        well_count: Number of wells (for fallback headers if results are None)
    """
    if analysis_results is None:
        # Create empty file structure with default headers
        headers = ["Parameter"]
        if well_count:
            headers.extend([f"Well_{i+1}" for i in range(well_count)])
        else:
            headers.extend([f"Well_{i+1}" for i in range(40)])  # Default

        with open(output_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
        return

    # Extract parameters
    parameters = list(analysis_results.keys())

    with open(output_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)

        # Write headers
        headers = ["Parameter"] + [
            f"Well_{i+1}" for i in range(len(analysis_results[parameters[0]]))
        ]
        writer.writerow(headers)

        # Write parameter data rows
        for param_name in parameters:
            param_data = analysis_results[param_name]

            # Convert NaN to empty strings for cleaner CSV output
            cleaned_data = ["" if np.isnan(val) else str(val) for val in param_data]

            row = [param_name] + cleaned_data
            writer.writerow(row)
