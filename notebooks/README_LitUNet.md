# LitUNet Shared Module

This project now uses a shared `LitUNet` class to eliminate code duplication between notebooks and scripts.

## File Structure

```
notebooks/
├── lit_unet.py              # Shared LitUNet class
├── export_model.py          # ONNX export script (uses lit_unet.py)
├── example_usage.py         # Usage examples
├── README_LitUNet.md        # This documentation
├── 3-Segmentation-NN.ipynb  # Training notebook (can import from lit_unet.py)
├── 4-export-model.ipynb     # Export notebook (can import from lit_unet.py)
└── [other notebooks...]
models/                      # Output directory for exported models
```

## Benefits

- **No Code Duplication**: Single source of truth for the LitUNet class
- **Easier Maintenance**: Changes only need to be made in one place
- **Consistency**: All notebooks and scripts use the same implementation
- **Modularity**: Clean separation of concerns

## Usage

### In Python Scripts

```python
from lit_unet import LitUNet

# Create model
model = LitUNet(n_classes=2, num_input_channel=1)

# Load from checkpoint
model = LitUNet.load_from_checkpoint("path/to/checkpoint.ckpt")
```

### In Jupyter Notebooks

```python
from lit_unet import LitUNet

# Now you can use LitUNet without defining it in the notebook
model = LitUNet(n_classes=2, num_input_channel=1)
```

### Export to ONNX

```bash
python export_model.py --checkpoint_path path/to/model.ckpt --batch_size 4
```

## Migration Guide

### For notebooks/3-Segmentation-NN.ipynb

1. Add import at the top:
   ```python
   from lit_unet import LitUNet
   ```

2. Remove the inline `LitUNet` class definition

3. Use the imported class as before

### For notebooks/4-export-model.ipynb

1. Add import at the top:
   ```python
   from lit_unet import LitUNet
   ```

2. Remove the inline `LitUNet` class definition

3. Use the imported class as before

## LitUNet Class Features

- **PyTorch Lightning Integration**: Full LightningModule implementation
- **MONAI UNet Backend**: Uses MONAI's UNet architecture
- **Training & Validation**: Complete training loop with metrics
- **Loss Functions**: TverskyLoss for segmentation
- **Metrics**: Dice coefficient tracking
- **Visualization**: Built-in plotting capabilities
- **Checkpointing**: Automatic saving/loading of model state

## Parameters

- `n_classes`: Number of segmentation classes
- `num_input_channel`: Number of input channels (1 for grayscale, 3 for RGB)
- `dropout`: Dropout rate (default: 0.5)
- `check_val`: Validation check frequency (default: 10)
- `max_epochs`: Maximum training epochs (default: 50)
- `optim_lr`: Learning rate (default: 0.001)

## Export Features

The `export_model.py` script provides:

- **Batch Support**: Export models with configurable batch sizes
- **Optimization**: ONNX optimization enabled by default
- **Verification**: Automatic verification of exported models
- **ONNX Runtime Testing**: Validates exported models work correctly
- **Command Line Interface**: Easy-to-use CLI with sensible defaults

## Example Workflow

1. **Train Model** (using notebook or script with shared LitUNet)
2. **Save Checkpoint** (automatic with PyTorch Lightning)
3. **Export to ONNX**:
   ```bash
   python export_model.py --checkpoint_path checkpoints/model.ckpt --batch_size 8
   ```
4. **Use Exported Model** in production with ONNX Runtime

This refactoring improves code organization and maintainability while preserving all existing functionality.
