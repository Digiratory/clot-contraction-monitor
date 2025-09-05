# Clot Contraction Monitor System

Clot Contraction Monitor is an open-source Python application that automates analysis of clot contraction patterns using computer vision and neural networks. Key features include neural network-based clot detection, interactive visualization with cursor synchronization, batch processing capabilities, and CSV export functionality.

## Pre-commit Hooks Setup

This project uses pre-commit hooks to enforce code quality and consistency standards. The following hooks are configured:

### Installed Hooks

1. **pre-commit-hooks**:
   - trailing-whitespace: Removes trailing whitespace
   - end-of-file-fixer: Ensures files end with a newline
   - check-yaml: Validates YAML files
   - check-added-large-files: Prevents large files from being added
   - check-case-conflict: Checks for case conflicts in filenames
   - check-json: Validates JSON files
   - detect-private-key: Detects private keys in files

2. **isort**:
   - Sorts Python imports in a consistent order
   - Uses black profile for import sorting
   - Runs on pre-commit, pre-merge-commit, pre-push, and manual stages

3. **black**:
   - Formats Python code consistently
   - Uses Python 3.10+ as language version

### Setup Instructions

1. Install pre-commit hooks:

   ```bash
   pre-commit install
   ```

2. Run all hooks on existing files:

   ```bash
   pre-commit run --all-files
   ```

3. The hooks will automatically run on every git commit, preventing code with formatting issues from being committed.

### Configuration

The configuration is defined in `.pre-commit-config.yaml` file which specifies:

- Repository URLs and versions for each hook group
- Specific hook IDs and their configurations
- Stages where hooks should run
- Language requirements for Python hooks

### Benefits

- Enforces consistent code style across the project
- Improves code quality automatically
- Prevents common formatting issues before commit
- Saves time during code reviews by standardizing formatting
