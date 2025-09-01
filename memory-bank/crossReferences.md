# Cross-References: Cells Contraction Monitor Memory Bank

## Overview
This document provides cross-references between memory bank files for efficient navigation and understanding of project relationships.

## File Index
### Core Files
- **projectbrief.md**: Project vision, objectives, success metrics
- **productContext.md**: Market analysis, user value, competitive landscape
- **systemPatterns.md**: Architecture, design patterns, component relationships
- **techContext.md**: Technology stack, development tools, performance
- **activeContext.md**: Current development status, technical decisions
- **progress.md**: Project progress, quality metrics, future planning

### Specialized Files
- **technicalStandards.md**: Coding standards, testing, documentation
- **performanceBenchmarks.md**: Performance metrics, benchmarking framework
- **userStories.md**: User scenarios, requirements (if exists)

## Key Relationships
- **Requirements**: userStories.md → technicalStandards.md → systemPatterns.md
- **Implementation**: techContext.md → systemPatterns.md → technicalStandards.md
- **Quality**: technicalStandards.md → performanceBenchmarks.md → progress.md
- **Risk**: riskAssessment.md → activeContext.md → progress.md

## Navigation Workflows
### New Contributors
1. projectbrief.md → productContext.md → systemPatterns.md → techContext.md
2. technicalStandards.md → activeContext.md → progress.md

### Developers
1. systemPatterns.md → techContext.md → technicalStandards.md
2. performanceBenchmarks.md → progress.md

### Project Managers
1. projectbrief.md → progress.md → activeContext.md
2. productContext.md → performanceBenchmarks.md
