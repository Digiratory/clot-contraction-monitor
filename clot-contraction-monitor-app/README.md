# Clot Contraction Monitor

Clot Contraction Monitor is a tool for analyzing clot contraction patterns in biological experiments.

## Project Structure
```
clot-contraction-monitor-app/
├── pyproject.toml          # Project configuration and dependencies
├── src/                    # Source code
│   └── clot_contraction_monitor/
│       ├── __init__.py
│       ├── app/            # Application components
│       ├── annotators/     # clot annotation tools
│       ├── io/             # Input/output operations
│       └── processing/     # Image processing modules
└── tests/                  # Test files
```

## Development Environment Setup

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Installation Steps

1. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

2. **Activate the virtual environment:**
   - On Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```
   This installs the project in development mode along with all dependencies.

### Running Tests
```bash
python -m pytest tests/
```

### Development Commands
- Run tests: `python -m pytest tests/`
- Run specific test: `python -m pytest tests/test_frame_preview.py`
- Run all tests: `python tests/run_tests.py`

## Project Dependencies
The project requires the following key dependencies:
- numpy >= 1.21.0
- opencv-python >= 4.5.0
- matplotlib >= 3.5.0
- pillow >= 8.0.0
- scikit-image >= 0.18.0
- pandas >= 1.3.0
- onnxruntime >= 1.10.0
- openvino >= 2022.3.0
- typing_extensions >= 4.0.0

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests to ensure everything works
5. Submit a pull request

## Headless Mode Usage

The application supports headless mode for batch processing without the GUI interface. This is useful for automated workflows and server environments.

### Command Line Options

```bash
python -m clot_contraction_monitor.app.main --help
```

### Running in Headless Mode

```bash
python -m clot_contraction_monitor.app.main --input-folder /path/to/images --output-csv results.csv
```

### Arguments

- `--headless`: Enable headless mode (no GUI)
- `--input-folder`: Path to folder containing image files (required for headless mode)
- `--output-csv`: Output CSV file path (default: results.csv)

### CSV Output Format

The CSV file contains:
- **Rows**: Each row represents one image/sample
- **Columns**: First column is "Sample" (image filename), followed by Well_1, Well_2, ..., Well_40
- **Values**: Clot size measurements for each well in each image

Example CSV structure:
```
Sample,Well_1,Well_2,Well_3,...,Well_40
image001,123.45,234.56,345.67,...,456.78
image002,111.11,222.22,333.33,...,444.44
...
```

### Supported Image Formats

The application automatically detects and processes common image formats including:
- JPG/JPEG
- PNG
- TIFF
- BMP

## License
This project is licensed under the MIT License - see the LICENSE file for details.
