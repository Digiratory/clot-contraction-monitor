# Technology Context: Cells Contraction Monitor

## Core Technologies

### Primary Language
- **Python 3.10+**: Main implementation language for all components

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

### Commit Conventions
Contributors MUST follow Conventional Commits 1.0.0 specification.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

Commits MUST be prefixed with a type, which consists of a noun, feat, fix, etc., followed by the OPTIONAL scope, OPTIONAL !, and REQUIRED terminal colon and space.
The type feat MUST be used when a commit adds a new feature to your application or library.
The type fix MUST be used when a commit represents a bug fix for your application.
A scope MAY be provided after a type. A scope MUST consist of a noun describing a section of the codebase surrounded by parenthesis, e.g., fix(parser):
A description MUST immediately follow the colon and space after the type/scope prefix. The description is a short summary of the code changes, e.g., fix: array parsing issue when multiple spaces were contained in string.
A longer commit body MAY be provided after the short description, providing additional contextual information about the code changes. The body MUST begin one blank line after the description.
A commit body is free-form and MAY consist of any number of newline separated paragraphs.

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
- Python 3.10+
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
- `onnxruntime-openvino`: OpenVINO acceleration for ONNX models
- `openvino`: Hardware-accelerated neural network inference
- `tkinter`: GUI components
- `matplotlib`: Plotting and visualization
- `Pillow`: Image format support
- `scikit-image`: Advanced image processing
- `pandas`: Data manipulation and analysis
- `scipy`: Scientific computing utilities
- `typing_extensions`: Enhanced type hints for older Python versions

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
