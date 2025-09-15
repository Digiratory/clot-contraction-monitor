# Contributing Guidelines

## Commit Conventions

Contributors MUST follow Conventional Commits 1.0.0 specification.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

Commits MUST be prefixed with a type, which consists of a noun, feat, fix, etc., followed by the OPTIONAL scope, OPTIONAL !, and REQUIRED terminal colon and space.
The type feat MUST be used when a commit adds a new feature to your application or library.
The type fix MUST be used when a commit represents a bug fix for your application.
A scope MAY be provided after a type. A scope MUST consist of a noun describing a section of the codebase surrounded by parenthesis, e.g., fix(parser):
A description MUST immediately follow the colon and space after the type/scope prefix. The description is a short summary of the code changes, e.g., fix: array parsing issue when multiple spaces were contained in string.
A longer commit body MAY be provided after the short description, providing additional contextual information about the code changes. The body MUST begin one blank line after the description.
A commit body is free-form and MAY consist of any number of newline separated paragraphs.

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
