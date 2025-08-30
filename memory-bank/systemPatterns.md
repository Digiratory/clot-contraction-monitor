# System Patterns: Cells Contraction Monitor

## Architecture Overview
The system follows a modular architecture with clear separation of concerns:
- **Data Processing Layer**: Handles input data loading and preprocessing
- **Analysis Layer**: Contains core algorithms for cell segmentation and contraction analysis
- **Visualization Layer**: Provides interactive tools for data exploration and result visualization
- **Application Layer**: Manages user interface and workflow orchestration

## Key Design Patterns

### 1. Pipeline Processing Pattern
Data flows through a well-defined pipeline:
```
Input Data → Preprocessing → Well Detection → Cell Segmentation → Contraction Analysis → Results
```
Each stage is modular and can be independently tested and optimized.

### 2. Plugin/Strategy Pattern for Annotators
Different annotation approaches are implemented as pluggable components, allowing for:
- Multiple cell segmentation algorithms
- Different well detection methods
- Extensible analysis techniques

### 3. Session-Based Processing
Processing sessions encapsulate the entire analysis workflow, maintaining state and enabling:
- Resume capability
- Batch processing
- Consistent parameter management

### 4. Observer Pattern for UI Updates
Real-time updates to visualizations and progress indicators use observer patterns to maintain loose coupling between processing and UI components.

## Component Relationships

### Core Modules
- `processing/`: Contains main analysis algorithms
- `annotators/`: Pluggable annotation and segmentation tools
- `io/`: Data input/output utilities
- `app/`: Application interface and visualization components

### Data Flow
1. **Input Stage**: Raw image data is loaded and preprocessed
2. **Segmentation Stage**: Wells and cells are identified using neural network models
3. **Analysis Stage**: Contraction patterns are measured and quantified
4. **Output Stage**: Results are visualized and exported

## Critical Implementation Paths

### Neural Network Integration
- ONNX model integration for cell segmentation
- Preprocessing pipelines optimized for model input requirements
- Post-processing for converting model outputs to usable data structures

### Performance Optimization
- Batch processing for large datasets
- Memory-efficient image handling
- Parallel processing where applicable

### User Experience
- Interactive frame preview for parameter tuning
- Real-time plotting of contraction data
- Intuitive workflow management
