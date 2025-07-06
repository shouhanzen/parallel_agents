# Architecture Overview

The Parallel Agents Verifier System is a sophisticated automated testing framework that uses Claude Code agents to monitor source code changes and generate tests in real-time.

## System Components

### 1. Overseer (`overseer.py`)
The central coordinator that manages all system components:
- **Purpose**: Orchestrates the entire system lifecycle
- **Key Responsibilities**:
  - Initializes and coordinates all components
  - Manages the main event loop
  - Handles graceful shutdown
  - Processes file changes and error reports
  - Displays colored error reports to users

### 2. Filesystem Watcher (`watcher.py`)
Real-time file system monitoring:
- **Purpose**: Detects file changes in watched directories
- **Key Features**:
  - Recursive directory monitoring
  - Configurable file extension filtering
  - Event-driven architecture using watchdog library
  - Supports create, modify, and delete events

### 3. Delta Gate (`delta_gate.py`)
Intelligent change filtering and batching:
- **Purpose**: Reduces noise and batches changes efficiently
- **Key Features**:
  - Filters out irrelevant files (*.pyc, logs, etc.)
  - Batches changes to avoid processing every minor change
  - Configurable timing and size constraints
  - File size validation

### 4. Verifier Agent (`agent.py`)
Claude Code integration for automated testing:
- **Purpose**: Interfaces with Claude Code to generate and run tests
- **Key Features**:
  - Maintains conversation history
  - Configurable mission prompts
  - Asynchronous Claude Code execution
  - Timeout handling
  - Error reporting integration

### 5. Error Reporter (`reporter.py`)
Bug tracking and reporting system:
- **Purpose**: Handles error reporting in JSONL format
- **Key Features**:
  - Structured error reports with severity levels
  - JSONL format for machine readability
  - Report monitoring and processing
  - Timestamped error entries

### 6. Working Set Manager (`working_set.py`)
Test artifact management:
- **Purpose**: Manages generated tests and artifacts
- **Key Features**:
  - Organized directory structure
  - Test file creation and management
  - Metadata tracking
  - Cleanup utilities

### 7. Configuration System (`config.py`)
Centralized configuration management:
- **Purpose**: Manages all system settings
- **Key Features**:
  - Pydantic-based validation
  - JSON configuration files
  - Default value handling
  - Environment-specific settings

### 8. CLI Interface (`cli.py`)
Command-line interface for system operations:
- **Purpose**: Provides user-friendly command-line access
- **Key Features**:
  - Multiple operation modes (start, demo, init, status, validate)
  - Configuration override capabilities
  - Interactive feedback
  - Mock mode for testing

## Data Flow

```
File Change → Filesystem Watcher → Delta Gate → Verifier Agent → Claude Code
                                                      ↓
Working Set Manager ← Error Reporter ← Test Generation & Execution
```

## Key Design Patterns

### 1. Event-Driven Architecture
- File changes trigger events through the system
- Asynchronous processing for responsiveness
- Decoupled components communicate through events

### 2. Pipeline Pattern
- Changes flow through a processing pipeline
- Each stage adds value and filtering
- Clear separation of concerns

### 3. Configuration-Driven Design
- Behavior controlled through configuration
- Environment-specific customization
- Runtime parameter adjustment

### 4. Graceful Degradation
- System continues operation despite component failures
- Comprehensive error handling
- Resource cleanup on shutdown

## Threading and Concurrency

The system uses:
- **AsyncIO**: For non-blocking operations
- **Watchdog Observers**: For file system monitoring
- **Process Execution**: For Claude Code integration
- **Thread-Safe Operations**: For cross-component communication

## Scalability Considerations

### Performance Optimizations
- Change batching to reduce processing overhead
- File filtering to avoid unnecessary work
- Configurable timeouts for resource management
- Efficient file I/O operations

### Resource Management
- Temporary file cleanup
- Memory-efficient file processing
- Configurable working set management
- Process timeout handling

## Security Considerations

### Input Validation
- File path validation
- Configuration parameter validation
- File extension filtering
- Size constraints

### Process Isolation
- Subprocess execution for Claude Code
- Timeout protection against hanging processes
- Resource cleanup on failure

## Extension Points

The architecture supports extension through:
- **Custom Missions**: Different agent behaviors
- **File Type Support**: Additional language support
- **Reporter Backends**: Different output formats
- **Watcher Enhancements**: Advanced filtering rules