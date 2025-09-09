# System Patterns: Clots Contraction Monitor

## Architecture Overview
Modular design with separation of concerns, prioritizing scientific accuracy and extensibility.

## Core Principles
- Scientific accuracy first
- Modular extensibility via plugins
- Performance optimization for large datasets
- User-centric design
- Cross-platform compatibility

## Layered Architecture
- **Core Engine**: Neural networks, image processing, math libraries, curve fitting algorithms
- **Data Access**: File I/O, annotation persistence, caching, headless processing interface
- **Processing**: Preprocessing, segmentation, tracking, feature extraction, curve metrics analysis
- **Analysis**: Statistical analysis, pattern recognition, quality metrics, second-order response modeling
- **Visualization**: Interactive plots, previews, progress monitoring, statistical parameter visualization, GridSpec layouts
- **Application**: Workflow orchestration, UI, session management, batch processing capabilities

## Key Design Patterns
1. **Pipeline Processing**: Modular stages with validation and error handling
2. **Strategy Pattern**: Interchangeable analysis algorithms
3. **Session State**: Persistent processing state with resume capability
4. **Observer Pattern**: Real-time updates and event handling
5. **Repository Pattern**: Data persistence abstraction
6. **Factory Pattern**: Dynamic component creation
7. **Curve Fitting Pattern**: Second-order aperiodic transfer function modeling for biological curves
8. **Statistical Visualization Pattern**: Boxplot-based parameter comparison across experimental groups
9. **GridSpec Layout Pattern**: Flexible subplot arrangement for complex multi-parameter views

## Component Relationships
Core modules: app/, processing/, io/, utils/ with clear dependencies and data flow from input to visualization.

## Technical Decisions
- **ONNX Runtime**: Cross-platform neural network inference
- **Streaming Processing**: Memory-efficient handling of large datasets
- **Comprehensive Error Handling**: Graceful degradation and recovery
- **Platform Optimizations**: Native performance and UI per platform

## Performance Optimization
- Vectorization and SIMD instructions
- Multi-threading and async I/O
- Hardware acceleration (GPU, SIMD)

## Quality Assurance
- Unit and integration testing
- Performance benchmarking
- Scientific validation against ground truth
