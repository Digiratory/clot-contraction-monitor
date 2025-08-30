# Cell Contraction Monitor

Cell Contraction Monitor is a tool for analyzing cell contraction patterns in biological experiments.

## Project Structure
```
cell-contraction-monitor-app/
├── pyproject.toml          # Project configuration and dependencies
├── src/                    # Source code
│   └── cell_contraction_monitor/
│       ├── __init__.py
│       ├── app/            # Application components
│       ├── annotators/     # Cell annotation tools
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

## License
This project is licensed under the MIT License - see the LICENSE file for details.
