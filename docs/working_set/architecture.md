# System Architecture

## Overview

The Verifier System is designed as a modular, event-driven architecture that provides automated testing and documentation generation through Claude Code agents. The system follows a microservices-like pattern where each component has a specific responsibility and communicates through well-defined interfaces.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                           Overseer                              │
│                    (Main Orchestrator)                         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
┌─────────┐    ┌─────────────┐    ┌─────────────┐
│ Watcher │    │ Delta Gate  │    │ Agents      │
│         │    │             │    │             │
└─────────┘    └─────────────┘    └─────────────┘
    │                 │                 │
    │                 │                 │
    ▼                 ▼                 ▼
┌─────────┐    ┌─────────────┐    ┌─────────────┐
│ File    │    │ Batch       │    │ Claude Code │
│ Events  │    │ Processing  │    │ Interface   │
└─────────┘    └─────────────┘    └─────────────┘
                      │
                      ▼
               ┌─────────────┐
               │ Working Set │
               │ Manager     │
               └─────────────┘
```

## Component Architecture

### 1. Overseer (Main Orchestrator)

**Location**: `src/overseer.py:15`

The Overseer is the central coordinator that manages all other components and orchestrates the entire verification process.

**Responsibilities**:
- Initialize and coordinate all system components
- Handle signal processing for graceful shutdown
- Process file change batches from the Delta Gate
- Manage error reporting and display
- Coordinate parallel agent execution

**Key Features**:
- Dual-agent architecture (testing + documentation)
- Graceful shutdown handling
- Error reporting integration
- Parallel processing of file changes

### 2. File System Watcher

**Location**: `src/watcher.py:31`

Monitors filesystem changes using the watchdog library and filters changes based on configured file extensions.

**Responsibilities**:
- Monitor specified directories for file changes
- Filter changes based on file extensions
- Emit file change events to the Delta Gate
- Handle recursive directory monitoring

**Event Types**:
- `created`: New file created
- `modified`: Existing file modified
- `deleted`: File deleted

### 3. Delta Gate (Change Filter & Batcher)

**Location**: `src/delta_gate.py:29`

Intelligent filtering and batching system that determines which file changes warrant processing and groups related changes together.

**Responsibilities**:
- Filter out irrelevant file changes (temporary files, logs, etc.)
- Batch related changes together for efficient processing
- Implement rate limiting to prevent overwhelming the system
- Handle file size constraints

**Filtering Rules**:
- File extension filtering
- Ignore patterns (*.pyc, .git, __pycache__, etc.)
- File size constraints (min/max)
- Hidden file filtering

**Batching Strategy**:
- Minimum change interval (0.5s default)
- Batch timeout (2.0s default)
- Overwrite strategy for multiple changes to same file

### 4. Agent System

The system includes two types of agents that work in parallel:

#### VerifierAgent
**Location**: `src/agent.py:11`

Interfaces with Claude Code to generate and execute tests.

**Responsibilities**:
- Generate tests based on file changes
- Execute generated tests
- Report test results and failures
- Detect and report potential bugs

#### DocumentationAgent
**Location**: `src/doc_agent.py:11`

Interfaces with Claude Code to generate and update documentation.

**Responsibilities**:
- Generate API documentation
- Create usage examples
- Update existing documentation
- Generate architecture diagrams

### 5. Working Set Manager

**Location**: `src/working_set.py:7`

Manages the working set directory structure and generated artifacts.

**Responsibilities**:
- Create and organize test files
- Manage documentation artifacts
- Handle metadata and versioning
- Provide file cleanup utilities

**Directory Structure**:
```
working_set/
├── tests/           # Generated test files
├── artifacts/       # Build artifacts and reports
├── reports/         # Error reports and monitoring data
└── metadata.json    # Working set metadata
```

### 6. Error Reporting System

**Location**: `src/reporter.py:8`

Handles error detection, reporting, and monitoring.

**Components**:
- `ErrorReporter`: Writes errors to JSONL files
- `ReportMonitor`: Monitors for new error reports

**Error Report Format**:
```json
{
  "timestamp": "2025-07-05T08:20:00Z",
  "file": "src/example.py",
  "line": 42,
  "severity": "high|medium|low",
  "description": "Error description",
  "suggested_fix": "Suggested fix"
}
```

## Data Flow

### 1. File Change Detection

```
File System → Watcher → Delta Gate → Overseer
```

1. **File System**: User makes changes to monitored files
2. **Watcher**: Detects changes and emits events
3. **Delta Gate**: Filters and batches changes
4. **Overseer**: Receives batched changes for processing

### 2. Agent Processing

```
Overseer → [VerifierAgent, DocumentationAgent] → Claude Code → Working Set
```

1. **Overseer**: Dispatches file changes to both agents in parallel
2. **Agents**: Process changes and generate prompts for Claude Code
3. **Claude Code**: Generates tests/documentation based on prompts
4. **Working Set**: Stores generated artifacts

### 3. Error Flow

```
Agent → Error Reporter → Report Monitor → Overseer → User Display
```

1. **Agent**: Detects errors during processing
2. **Error Reporter**: Writes errors to JSONL file
3. **Report Monitor**: Detects new error reports
4. **Overseer**: Processes and displays errors to user

## Configuration Architecture

### Configuration Hierarchy

```
Default Config → File Config → CLI Arguments → Environment Variables
```

1. **Default Config**: Built-in defaults in `VerifierConfig`
2. **File Config**: User-defined JSON configuration file
3. **CLI Arguments**: Command-line overrides
4. **Environment Variables**: Runtime environment overrides

### Configuration Validation

The system validates configuration at startup:
- Check that watch directories exist
- Validate file extensions
- Ensure working set directory can be created
- Verify Claude Code is available

## Concurrency Model

### Async/Await Pattern

The system uses Python's asyncio for concurrent processing:

```python
# Parallel agent processing
await asyncio.gather(
    self.agent.process_file_changes(batch),
    self.doc_agent.process_file_changes(batch)
)
```

### Thread Safety

- File system operations are synchronized
- Agent sessions are isolated
- Error reporting uses file-based queuing

## Extensibility Points

### 1. Custom Agents

Create specialized agents by inheriting from base agent classes:

```python
class CustomAgent(VerifierAgent):
    def _get_mission_prompt(self) -> str:
        return "Custom mission prompt"
```

### 2. Custom Filters

Extend the Delta Gate with custom filtering logic:

```python
class CustomDeltaGate(DeltaGate):
    def _should_process_change(self, change: FileChange) -> bool:
        # Custom filtering logic
        return super()._should_process_change(change)
```

### 3. Custom Reporters

Implement custom error reporting formats:

```python
class CustomReporter(ErrorReporter):
    def report_error(self, ...):
        # Custom reporting logic
        pass
```

## Performance Considerations

### 1. File System Monitoring

- Uses efficient watchdog library
- Filters changes at the watcher level
- Recursive monitoring with pattern exclusion

### 2. Batch Processing

- Intelligent batching reduces Claude Code calls
- Configurable batch timeouts
- Rate limiting prevents overwhelming

### 3. Memory Management

- Conversation history management
- Working set cleanup utilities
- Log rotation for long-running processes

### 4. Error Handling

- Graceful degradation on agent failures
- Retry logic for transient errors
- Resource cleanup on shutdown

## Security Considerations

### 1. File System Access

- Configurable watch directories
- File extension filtering
- Size constraints prevent processing large files

### 2. External Process Execution

- Sandboxed Claude Code execution
- Timeout protection
- Error handling for process failures

### 3. Data Privacy

- Local file processing only
- No external data transmission
- Configurable log retention

## Monitoring and Observability

### 1. Logging

- Structured logging with JSON format
- Multiple log levels (DEBUG, INFO, ERROR)
- Separate logs for different components

### 2. Metrics

- File processing rates
- Agent success/failure rates
- Error report statistics

### 3. Health Checks

- Component status monitoring
- Resource utilization tracking
- Error rate monitoring

## Deployment Patterns

### 1. Development Mode

- Mock agents for testing
- Reduced timeouts
- Verbose logging

### 2. Production Mode

- Real Claude Code integration
- Optimized batch processing
- Error alerting

### 3. CI/CD Integration

- Automated test generation
- Documentation updates
- Quality gate enforcement