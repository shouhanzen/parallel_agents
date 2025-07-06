# Interactive CLI Documentation

## Overview

The Parallel Agents Interactive CLI provides a command-line interface for managing and monitoring the verifier agent system. This CLI includes real-time log streaming, configuration management, and agent lifecycle control.

## Recent Changes

### Configuration Validation
- Added configuration validation before starting agents
- Added safety checks to prevent operations with invalid configurations
- Enhanced error handling for missing configurations

### New Features
- **LogStreamer Class**: Real-time log streaming with formatted output
- **Interactive Commands**: Complete CLI interface with status monitoring
- **Configuration Management**: Load, validate, and switch configurations
- **Agent Control**: Start/stop agents with demo mode support

## Architecture

### LogStreamer Class
```python
class LogStreamer:
    """Handles real-time log streaming from log files"""
```

**Purpose**: Provides real-time monitoring of agent activities through log file streaming.

**Key Features**:
- Threaded log streaming to avoid blocking CLI
- JSON log parsing with formatted output
- Automatic file monitoring and error recovery
- Graceful shutdown handling

### InteractiveVerifierCLI Class
```python
class InteractiveVerifierCLI(cmd.Cmd):
    """Interactive CLI for the Verifier system"""
```

**Purpose**: Main CLI interface for managing the parallel agents system.

**Key Features**:
- Configuration management and validation
- Agent lifecycle control (start/stop)
- Real-time log streaming
- Status monitoring and reporting

## Command Reference

### Configuration Commands

#### `config [file]`
Show current configuration or load a new configuration file.

**Usage**:
```bash
(parallel-agents) config                    # Show current config
(parallel-agents) config my-config.json     # Load specific config
```

#### `init [filename]`
Initialize a new configuration file with default values.

**Usage**:
```bash
(parallel-agents) init                      # Create verifier.json
(parallel-agents) init custom.json         # Create custom.json
```

#### `validate`
Validate the current configuration for errors and missing dependencies.

**Usage**:
```bash
(parallel-agents) validate
```

**Validation Checks**:
- Watch directory existence
- Working set directory creation
- Configuration file integrity

### Agent Control Commands

#### `start [options]`
Start the verifier agent with optional parameters.

**Usage**:
```bash
(parallel-agents) start                              # Start normal agent
(parallel-agents) start --demo                      # Start demo agent
(parallel-agents) start --mission "Custom mission"  # Start with custom mission
(parallel-agents) start --demo --mission testing    # Demo with custom mission
```

**Options**:
- `--demo`: Use MockOverseer for testing without actual Claude API calls
- `--mission <text>`: Override the default mission from configuration

#### `stop`
Stop the currently running verifier agent.

**Usage**:
```bash
(parallel-agents) stop
```

### Monitoring Commands

#### `status`
Show detailed agent status and recent activity.

**Usage**:
```bash
(parallel-agents) status
```

**Information Displayed**:
- Agent running state
- Current mission
- Watch directories
- Working set directory
- Log file location
- Recent log entries (last 3)

#### `logs [start|stop]`
Control real-time log streaming.

**Usage**:
```bash
(parallel-agents) logs          # Start streaming
(parallel-agents) logs start    # Start streaming
(parallel-agents) logs stop     # Stop streaming
```

**Log Format**:
- 🚀 Session start events
- ✅/❌ Claude API interactions with success/failure indicators
- 📋 General log entries
- Timestamps and truncated content for readability

### Utility Commands

#### `help [command]`
Show available commands or detailed help for a specific command.

**Usage**:
```bash
(parallel-agents) help          # Show all commands
(parallel-agents) help start    # Show help for start command
```

#### `exit` / `quit`
Exit the interactive CLI, stopping all running services.

**Usage**:
```bash
(parallel-agents) exit
(parallel-agents) quit
```

## Configuration Integration

The CLI automatically loads configuration from `verifier.json` by default. Key configuration elements used:

- `agent_mission`: Default mission for agents
- `watch_dirs`: Directories to monitor for changes
- `working_set_dir`: Directory for agent output
- `claude_log_file`: Location of interaction logs

## Error Handling

### Configuration Errors
- Missing configuration files trigger default config creation
- Invalid configurations show descriptive error messages
- Configuration validation prevents startup with invalid settings

### Agent Management Errors
- Prevents starting multiple agents simultaneously
- Handles agent startup/shutdown failures gracefully
- Provides clear error messages for troubleshooting

### Log Streaming Errors
- Handles missing log files gracefully
- Recovers from temporary file access issues
- Provides error feedback without crashing

## Threading Model

The CLI uses threading to prevent blocking operations:

1. **Main Thread**: Handles CLI interactions and command processing
2. **Agent Thread**: Runs the overseer agent with its own event loop
3. **Log Thread**: Streams log files in real-time (daemon thread)

This design ensures responsive CLI interactions while maintaining agent operations.

## Security Considerations

- Configuration files are validated before use
- Agent operations are sandboxed to configured directories
- Log streaming uses read-only file access
- Graceful shutdown prevents resource leaks

## Examples

### Basic Workflow
```bash
# Initialize new configuration
(parallel-agents) init

# Validate configuration
(parallel-agents) validate

# Start agent
(parallel-agents) start --mission "Monitor and document code changes"

# Monitor logs
(parallel-agents) logs start

# Check status
(parallel-agents) status

# Stop agent
(parallel-agents) stop
```

### Demo Mode Testing
```bash
# Start demo agent for testing
(parallel-agents) start --demo --mission testing

# Stream logs to see mock interactions
(parallel-agents) logs start

# Stop when done
(parallel-agents) stop
```

## Integration Points

The CLI integrates with:
- **VerifierConfig**: Configuration management
- **Overseer**: Production agent management
- **MockOverseer**: Testing and demonstration
- **Log Files**: Real-time monitoring and analysis

## Future Enhancements

Potential improvements:
- Command history and autocompletion
- Configuration editing within CLI
- Agent performance metrics
- Multi-agent support
- Remote agent management