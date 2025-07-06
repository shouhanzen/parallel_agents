# Verifier - Automated Testing with Claude Code Agents

An automated testing system that monitors source code changes and uses Claude Code agents to generate and run tests in the background.

## Features

- **Filesystem Watching**: Monitors source directories for file changes
- **Smart Change Detection**: Filters and batches changes using a delta gate
- **Claude Code Integration**: Uses Claude Code agents to generate tests automatically
- **Error Reporting**: Reports bugs and issues in JSONL format
- **Working Set Management**: Organizes generated tests and artifacts
- **CLI Interface**: Easy-to-use command-line interface

## Architecture

The system consists of several key components:

1. **Filesystem Watcher**: Monitors source directories for changes
2. **Delta Gate**: Filters and batches file changes to avoid noise
3. **Verifier Agent**: Interfaces with Claude Code to generate tests
4. **Error Reporter**: Handles bug reports in JSONL format
5. **Working Set Manager**: Manages test files and artifacts
6. **Overseer Process**: Coordinates all components

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd verifier

# Install with uv
uv pip install -e .
```

## Usage

### Initialize Configuration

```bash
uv run verifier init
```

This creates a `verifier.json` configuration file.

### Start the Verifier

```bash
uv run verifier start
```

The verifier will start monitoring your source code and generate tests automatically.

### Configuration Options

- `watch_dirs`: Directories to monitor (default: ["src"])
- `test_dir`: Directory for tests (default: "test")
- `working_set_dir`: Working directory for generated tests (default: "tests/working_set")
- `watch_extensions`: File extensions to monitor
- `agent_mission`: Mission for the agent ("testing", "docs", "tooling")
- `error_report_file`: File for error reports (JSONL format)
- `claude_timeout`: Timeout for Claude Code operations

### CLI Commands

- `verifier init`: Initialize configuration
- `verifier start`: Start the verifier overseer
- `verifier validate`: Validate configuration
- `verifier status`: Show current status

## How It Works

1. **File Monitoring**: The system watches configured directories for changes
2. **Change Filtering**: The delta gate filters out irrelevant changes (e.g., .pyc files, logs)
3. **Batch Processing**: Changes are batched to avoid processing every tiny change
4. **Test Generation**: Claude Code agents analyze changes and generate appropriate tests
5. **Error Detection**: If bugs are found, they're reported to the error report file
6. **Continuous Operation**: The system runs continuously, processing new changes as they occur

## Error Reporting

When bugs are detected, they're reported in JSONL format:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "file": "src/calculator.py",
  "line": 42,
  "severity": "high",
  "description": "Division by zero not handled",
  "suggested_fix": "Add zero check before division"
}
```

## Development

This project uses:
- Python 3.12+
- uv for package management
- Watchdog for filesystem monitoring
- Pydantic for configuration
- Click for CLI interface

## Testing the System

The system can be tested on itself! Just run:

```bash
uv run verifier start
```

Then make changes to files in the `src/` directory and watch the system generate tests automatically.