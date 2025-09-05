#!/usr/bin/env python3
"""
Example usage of the shared LitUNet class for model training and export.

This script demonstrates how to:
1. Import the LitUNet class from lit_unet.py
2. Use it for training (if you have data)
3. Export the trained model to ONNX format
"""

import numpy as np
import torch
from export_model import export_model_to_onnx
from lit_unet import LitUNet


def example_training():
    """Example of how to use LitUNet for training."""
    print("=== LitUNet Training Example ===")

    # Create model instance
    model = LitUNet(
        n_classes=2,  # Number of segmentation classes
        num_input_channel=1,  # Number of input channels (grayscale images)
        dropout=0.5,  # Dropout rate
        check_val=10,  # Validation check frequency
        max_epochs=50,  # Maximum training epochs
        optim_lr=0.001,  # Learning rate
    )

    print(f"Model created with {sum(p.numel() for p in model.parameters())} parameters")
    print(f"Input channels: {model.model.in_channels}")
    print(f"Output classes: {model.model.out_channels}")

    # Example: Load from checkpoint if available
    # checkpoint_path = "path/to/your/checkpoint.ckpt"
    # model = LitUNet.load_from_checkpoint(checkpoint_path)

    return model


def example_export():
    """Example of how to export a trained model to ONNX."""
    print("\n=== Model Export Example ===")

    # This would be your actual checkpoint path
    checkpoint_path = "path/to/your/trained/model.ckpt"

    try:
        export_model_to_onnx(
            checkpoint_path=checkpoint_path,
            output_path="models/exported_model.onnx",
            batch_size=4,  # Export with batch size 4
            input_channels=1,
            height=192,
            width=192,
            n_classes=2,
        )
    except FileNotFoundError:
        print(f"Checkpoint not found: {checkpoint_path}")
        print("Please update the checkpoint_path with your actual trained model path.")
    except Exception as e:
        print(f"Export failed: {e}")


def main():
    """Main function demonstrating LitUNet usage."""
    print("LitUNet Shared Module Usage Examples")
    print("=" * 40)

    # Example 1: Model creation
    model = example_training()

    # Example 2: Model export (requires actual checkpoint)
    example_export()

    print("\n=== Usage Summary ===")
    print("1. Import LitUNet: from lit_unet import LitUNet")
    print("2. Create model: model = LitUNet(n_classes=2, num_input_channel=1)")
    print(
        "3. Train or load: model = LitUNet.load_from_checkpoint('path/to/checkpoint.ckpt')"
    )
    print("4. Export: Use export_model.py script with --checkpoint_path argument")
    print("\nThis eliminates code duplication between notebooks and scripts!")


if __name__ == "__main__":
    main()
