# Technology Context: Cells Contraction Monitor

## Core Technologies

### Primary Language
- **Python 3.x**: Main implementation language for all components

### Key Libraries and Frameworks
- **OpenCV**: Image processing and computer vision operations
- **NumPy**: Numerical computing and array operations
- **ONNX**: Neural network model loading and inference
- **ONNX Runtime**: Model inference for cell segmentation
- **tkinter**: GUI framework for desktop application
- **Matplotlib**: Data visualization and plotting
- **Pillow**: Image format support and basic image operations

### Development Tools
- **Poetry**: Dependency management and packaging
- **pytest**: Testing framework
- **Jupyter Notebooks**: Development and experimentation environment
- **Git**: Version control

## Project Structure
```
cell-contraction-monitor-app/
├── src/
│   └── cell_contraction_monitor/
│       ├── annotators/          # Pluggable annotation tools
│       ├── app/                 # Application interface
│       ├── io/                  # Input/output utilities
│       └── processing/          # Core analysis algorithms
├── tests/                       # Unit and integration tests
├── notebooks/                   # Development notebooks
└── models/                      # Neural network models
```

## Development Setup

### Prerequisites
- Python 3.8+
- Poetry for dependency management
- Git for version control

### Installation
```bash
cd cell-contraction-monitor-app
poetry install
```

### Development Workflow
1. **Component Development and Implementation**: Implement algorithms in src/ modules
2. **Testing**: Write unit tests for core functionality
3. **Integration**: Connect components in the application layer

## Key Dependencies
- `opencv-python`: Image processing
- `numpy`: Numerical operations
- `onnxruntime`: Neural network inference
- `tkinter`: GUI components
- `matplotlib`: Plotting and visualization
- `Pillow`: Image format support
- `scipy`: Scientific computing utilities

## Technical Constraints
- Cross-platform compatibility (Windows, macOS, Linux)
- Memory-efficient processing for large image datasets
- Real-time performance for interactive analysis
- Minimal external dependencies to ensure portability

## Development Patterns
- Type hints for all function signatures
- Comprehensive docstrings for public APIs
- Modular design with clear interfaces
- Test-driven development for core algorithms
