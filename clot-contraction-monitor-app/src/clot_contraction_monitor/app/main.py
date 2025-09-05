# cell-contraction-monitor-app/src/clot_contraction_monitor/app/main.py
import argparse
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
from clot_contraction_monitor.app.app import ClotContractionApp
from clot_contraction_monitor.io import export_to_csv
from clot_contraction_monitor.processing.processing_session import ProcessingSession


def run_headless(input_folder: str, output_csv: str) -> None:
    """Run the application in headless mode for batch processing.

    Args:
        input_folder: Path to the folder containing images to process
        output_csv: Path where to save the CSV results
    """
    print(f"Running in headless mode...")
    print(f"Input folder: {input_folder}")
    print(f"Output CSV: {output_csv}")

    # Initialize processing session
    processing_session = ProcessingSession()

    # Select and validate folder
    if not processing_session.select_folder(folder_path=input_folder):
        print("Error: Failed to select folder or no valid images found")
        sys.exit(1)

    # Progress callback for headless mode
    def progress_callback(frame_idx: int, from_cache: bool, is_last: bool) -> None:
        status = "cached" if from_cache else "processed"
        print(f"Frame {frame_idx + 1}/{processing_session.frame_count()}: {status}")
        if is_last:
            print("Processing complete!")

    # Process all images
    if not processing_session.load_project(progress_callback):
        print("Error: Failed to process images")
        sys.exit(1)

    # Get results
    cell_sizes = processing_session.get_clot_sizes()
    if cell_sizes is None:
        print("Error: No cell size data available")
        sys.exit(1)

    # Export to CSV
    export_to_csv(cell_sizes, output_csv, processing_session.images)
    print(f"Results exported to: {output_csv}")

    # Save plot
    plot_path = os.path.splitext(output_csv)[0] + "_plot.png"
    plt.figure(figsize=(10, 6))
    num_wells = cell_sizes.shape[1]
    for i in range(num_wells):
        plt.plot(cell_sizes[:, i], label=f"Well {i+1}", marker="o", markersize=4)
    plt.xlabel("Frame Index")
    plt.ylabel("Cell Size (pixels)")
    plt.title("Cell Contraction Analysis")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(plot_path)
    plt.close()
    print(f"Plot saved to: {plot_path}")


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Cell Contraction Monitor - Analyze cell contraction patterns"
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run in headless mode without GUI"
    )
    parser.add_argument(
        "--input-folder",
        type=str,
        help="Input folder containing images (required for headless mode)",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="results.csv",
        help="Output CSV file path (default: results.csv)",
    )

    args = parser.parse_args()

    if args.headless:
        if not args.input_folder:
            print("Error: --input-folder is required when using --headless mode")
            sys.exit(1)

        if not os.path.isdir(args.input_folder):
            print(f"Error: Input folder does not exist: {args.input_folder}")
            sys.exit(1)

        run_headless(args.input_folder, args.output_csv)
    else:
        # GUI mode
        app = ClotContractionApp()
        app.mainloop()


if __name__ == "__main__":
    main()
