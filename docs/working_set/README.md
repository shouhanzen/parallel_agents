# Verifier System Documentation

## Overview

The Verifier System is an automated testing and documentation framework that monitors filesystem changes and uses Claude Code agents to generate tests and documentation in real-time. The system consists of multiple components working together to provide continuous verification of code changes.

## Key Features

- **Real-time File Monitoring**: Watches specified directories for file changes
- **Automated Test Generation**: Uses Claude Code agents to generate tests for code changes
- **Automated Documentation**: Generates comprehensive documentation for new code
- **Intelligent Batching**: Groups related changes together for efficient processing
- **Error Reporting**: Detects and reports potential bugs and issues
- **Working Set Management**: Organizes generated tests and artifacts in a structured directory

## System Architecture

The verifier system consists of several key components:

1. **Overseer**: Main orchestrator that coordinates all components
2. **Agents**: Interface with Claude Code to generate tests and documentation
3. **File Watcher**: Monitors filesystem changes using watchdog
4. **Delta Gate**: Filters and batches file changes intelligently
5. **Working Set Manager**: Manages generated tests and artifacts
6. **Reporter**: Handles error reporting and monitoring

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize configuration
python -m src.cli init

# Start the verifier
python -m src.cli start
```

### Basic Usage

```bash
# Start with default configuration
python -m src.cli start

# Start with specific watch directories
python -m src.cli start --watch-dir src --watch-dir lib

# Start with custom mission
python -m src.cli start --mission docs

# Run in demo mode (with mock agents)
python -m src.cli demo
```

## Configuration

The system is configured through a JSON configuration file (`verifier.json`):

```json
{
  "watch_dirs": ["src"],
  "test_dir": "tests",
  "working_set_dir": "tests/working_set",
  "watch_extensions": [".py", ".js", ".ts"],
  "agent_mission": "testing",
  "error_report_file": "tests/working_set/error_report.jsonl",
  "claude_timeout": 300,
  "claude_log_file": "tests/working_set/claude_logs.jsonl"
}
```

## Generated Files

The system generates several types of files:

### Test Files
- Located in `tests/working_set/tests/`
- Automatically generated based on code changes
- Include unit tests, integration tests, and validation tests

### Documentation
- Located in `docs/working_set/`
- API documentation, usage examples, and architecture diagrams
- Automatically updated when code changes

### Reports
- Error reports in JSONL format
- Interaction logs with Claude Code
- Monitoring and status reports

## CLI Commands

### `start`
Start the verifier overseer process with real Claude Code agents.

```bash
python -m src.cli start [OPTIONS]
```

Options:
- `--config, -c`: Configuration file path (default: verifier.json)
- `--watch-dir, -w`: Directories to watch (can be specified multiple times)
- `--mission, -m`: Agent mission (testing, docs, tooling)

### `demo`
Start the verifier with mock agents for testing and demonstration.

```bash
python -m src.cli demo [OPTIONS]
```

### `init`
Initialize a new verifier configuration file.

```bash
python -m src.cli init [OPTIONS]
```

Options:
- `--output, -o`: Output configuration file (default: verifier.json)

### `status`
Show verifier status and current configuration.

```bash
python -m src.cli status [OPTIONS]
```

### `validate`
Validate the verifier configuration and check prerequisites.

```bash
python -m src.cli validate [OPTIONS]
```

## Agent Missions

The system supports different agent missions:

### Testing Mission
- Generates unit tests for new functions and classes
- Creates integration tests for complex components
- Validates code changes with comprehensive test suites

### Documentation Mission
- Creates API documentation for new code
- Generates usage examples and tutorials
- Updates existing documentation when code changes

### Tooling Mission
- Generates utility scripts and tools
- Creates automation scripts for common tasks
- Builds development helpers and debugging tools

## Error Handling

The system includes comprehensive error handling:

- **File System Errors**: Graceful handling of permission issues and missing files
- **Agent Timeouts**: Configurable timeouts for Claude Code interactions
- **Batch Processing**: Intelligent retry logic for failed operations
- **Error Reports**: Detailed error reporting with suggested fixes

## Best Practices

1. **Configuration**: Start with default settings and customize as needed
2. **Watch Directories**: Be selective about which directories to monitor
3. **File Extensions**: Configure appropriate file extensions for your project
4. **Mission Selection**: Choose the right mission for your use case
5. **Working Set**: Regularly review and clean up generated files

## Troubleshooting

### Common Issues

1. **Claude Code Not Found**: Ensure Claude Code is installed and in PATH
2. **Permission Errors**: Check file permissions in watch directories
3. **High CPU Usage**: Reduce batch frequency or add ignore patterns
4. **Failed Tests**: Review generated tests and customize as needed

### Debug Mode

Enable debug logging by setting environment variables:

```bash
export VERIFIER_DEBUG=1
export VERIFIER_LOG_LEVEL=DEBUG
```

## Contributing

The verifier system is designed to be extensible. Key extension points:

- **Custom Agents**: Create specialized agents for specific tasks
- **File Filters**: Add custom file filtering logic
- **Report Formats**: Implement custom report formats
- **Integration**: Add integrations with other tools and services

## API Reference

See `api-reference.md` for detailed API documentation.

## Examples

See `examples/` directory for usage examples and sample configurations.