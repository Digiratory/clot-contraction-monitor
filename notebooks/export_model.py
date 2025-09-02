#!/usr/bin/env python3
"""
Script to export trained UNet model to optimized ONNX format with batching support.

This script loads a trained PyTorch Lightning model, unwraps the UNet component,
and exports it to ONNX format with optimizations enabled.

Usage:
    python export_model.py --checkpoint_path path/to/checkpoint.ckpt --output_path models/model.onnx --batch_size 4

Arguments:
    --checkpoint_path: Path to PyTorch Lightning checkpoint file
    --output_path: Output ONNX file path (default: models/optimized_model.onnx)
    --batch_size: Batch size for the model input (default: 4)
    --input_channels: Number of input channels (default: 1)
    --height: Input height (default: 192)
    --width: Input width (default: 192)
    --n_classes: Number of output classes (default: 2)
    --opset_version: ONNX opset version (default: 22)
"""

import argparse
import os

import monai.networks.utils as m_nn_utils
import numpy as np
import onnx
import onnxruntime
import torch
from lit_unet import LitUNet
from onnxconverter_common import float16
from onnxruntime.quantization import QuantType, quant_pre_process, quantize_dynamic


def export_model_to_onnx(
    checkpoint_path: str,
    output_path: str = "model.onnx",
    batch_size: int = 1,
    input_channels: int = 1,
    height: int = 192,
    width: int = 192,
    n_classes: int = 2,
    opset_version: int = 22,
    optimize: bool = True,
    quantize: bool = True,
):
    """
    Export trained model to ONNX format.

    Args:
        checkpoint_path: Path to PyTorch Lightning checkpoint
        output_path: Output ONNX file path
        batch_size: Batch size for the model input
        input_channels: Number of input channels
        height: Input height
        width: Input width
        n_classes: Number of output classes
        opset_version: ONNX opset version
        optimize: Whether to optimize the ONNX model
    """

    print(f"Loading model from checkpoint: {checkpoint_path}")

    # Load the trained model
    best_model = LitUNet.load_from_checkpoint(
        checkpoint_path, n_classes=n_classes, num_input_channel=input_channels
    )
    unwrapped_best_model = best_model.model

    print("Model loaded successfully")

    # Set model to evaluation mode
    with torch.no_grad():
        with m_nn_utils.eval_mode(unwrapped_best_model):
            unwrapped_best_model.eval()
            unwrapped_best_model.cpu()

            print("Model set to evaluation mode on CPU")

            # Create dummy input with specified batch size
            dummy_input = torch.randn(
                (batch_size, input_channels, height, width),
                requires_grad=False,
                device="cpu",
            )

            print(f"Created dummy input with shape: {dummy_input.shape}")

            # Forward pass with original model
            torch_out = unwrapped_best_model(dummy_input)
            print(f"Original model output shape: {torch_out.shape}")

            # Export to TorchScript using torch.export
            print("Exporting to TorchScript...")
            ts_model = torch.export.export(
                unwrapped_best_model, args=(dummy_input,), strict=True
            )

            # Verify TorchScript model
            ts_out = ts_model.module()(dummy_input)
            np.testing.assert_allclose(
                torch_out.detach().cpu().numpy(),
                ts_out.detach().cpu().numpy(),
                rtol=0.01,
                atol=0.001,
            )
            print("TorchScript model verified successfully")

            # Export to ONNX
            print(f"Exporting to ONNX: {output_path}")
            onnx_program = torch.onnx.export(
                ts_model,
                (dummy_input,),
                output_path,
                opset_version=opset_version,
                input_names=["input"],
                output_names=["output"],
                optimize=optimize,
                external_data=False,
                dynamo=True,
            )

            print("ONNX export completed")

            # Load and verify ONNX model
            print("Loading and verifying ONNX model...")
            onnx_model = onnx.load(output_path)
            onnx.checker.check_model(onnx_model)
            print("ONNX model verified successfully")

            model_fp16 = float16.convert_float_to_float16(onnx_model)
            onnx.save(model_fp16, output_path.replace(".onnx", "_fp16.onnx"))

            # Test with ONNX Runtime
            print("Testing with ONNX Runtime...")
            ort_session = onnxruntime.InferenceSession(output_path)

            ort_inputs = {
                ort_session.get_inputs()[0].name: dummy_input.detach().cpu().numpy()
            }
            ort_outs = ort_session.run(None, ort_inputs)

            # Verify outputs match
            np.testing.assert_allclose(
                torch_out.detach().cpu().numpy(), ort_outs[0], rtol=0.001, atol=0.001
            )

            # Test with ONNX Runtime
            print("Testing with ONNX Runtime fp16...")
            ort_session = onnxruntime.InferenceSession(
                output_path.replace(".onnx", "_fp16.onnx")
            )

            ort_inputs = {
                ort_session.get_inputs()[0]
                .name: dummy_input.detach()
                .cpu()
                .numpy()
                .astype(np.float16)
            }
            ort_outs = ort_session.run(None, ort_inputs)

            # Verify outputs match
            np.testing.assert_allclose(
                torch_out.detach().cpu().numpy(), ort_outs[0], rtol=0.001, atol=0.001
            )

            if quantize:
                model_fp32 = output_path
                model_infer = output_path.replace(".onnx", "-infer.onnx")
                quant_pre_process(model_fp32, model_infer)
                model_quant = output_path.replace(".onnx", ".quant.onnx")
                quantized_model = quantize_dynamic(
                    model_infer,
                    model_quant,
                    weight_type=QuantType.QUInt8,
                    # nodes_to_exclude=["node_conv2d_quant"],
                )

                # Test Quant with ONNX Runtime
                print("Testing Quant model with ONNX Runtime...")
                ort_session = onnxruntime.InferenceSession(model_quant)

                ort_inputs = {
                    ort_session.get_inputs()[0].name: dummy_input.detach().cpu().numpy()
                }
                ort_outs = ort_session.run(None, ort_inputs)

                # Verify outputs match
                np.testing.assert_allclose(
                    torch_out.detach().cpu().numpy(),
                    ort_outs[0],
                    rtol=0.001,
                    atol=0.001,
                )

            print("ONNX Runtime verification successful")

            print(f"Model exported successfully to: {output_path}")
            print(f"Input shape: {dummy_input.shape}")
            print(f"Output shape: {torch_out.shape}")
            print(f"ONNX opset version: {opset_version}")
            print(f"Optimization enabled: {optimize}")
            print(f"Quantization enabled: {quantize}")


def main():
    """Main function to run the export process."""

    parser = argparse.ArgumentParser(
        description="Export PyTorch Lightning UNet model to ONNX format"
    )
    parser.add_argument(
        "--checkpoint_path",
        type=str,
        required=True,
        help="Path to PyTorch Lightning checkpoint file",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="models/optimized_model.onnx",
        help="Output ONNX file path",
    )
    parser.add_argument(
        "--batch_size", type=int, default=4, help="Batch size for the model input"
    )
    parser.add_argument(
        "--input_channels", type=int, default=1, help="Number of input channels"
    )
    parser.add_argument("--height", type=int, default=192, help="Input height")
    parser.add_argument("--width", type=int, default=192, help="Input width")
    parser.add_argument(
        "--n_classes", type=int, default=2, help="Number of output classes"
    )
    parser.add_argument(
        "--opset_version", type=int, default=22, help="ONNX opset version"
    )

    args = parser.parse_args()

    # Check if checkpoint exists
    if not os.path.exists(args.checkpoint_path):
        print(f"Error: Checkpoint file not found: {args.checkpoint_path}")
        print("Please provide a valid path to the checkpoint file.")
        return

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Export the model
    try:
        export_model_to_onnx(
            checkpoint_path=args.checkpoint_path,
            output_path=args.output_path,
            batch_size=args.batch_size,
            input_channels=args.input_channels,
            height=args.height,
            width=args.width,
            n_classes=args.n_classes,
            opset_version=args.opset_version,
        )
        print("\nExport completed successfully!")
    except Exception as e:
        print(f"Error during export: {str(e)}")
        raise


if __name__ == "__main__":
    main()
