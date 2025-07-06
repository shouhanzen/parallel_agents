# User Guide

This guide will help you get started with the Parallel Agents Verifier System and make the most of its features.

## Getting Started

### Prerequisites

Before using the verifier system, ensure you have:
- Python 3.12 or higher
- `uv` package manager
- `claude` CLI tool installed and configured
- Access to Claude Code API

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd parallel_agents
   ```

2. **Install dependencies:**
   ```bash
   uv pip install -e .
   ```

3. **Verify installation:**
   ```bash
   uv run verifier --help
   ```

### Initial Setup

1. **Initialize configuration:**
   ```bash
   uv run verifier init
   ```
   This creates a `verifier.json` file with default settings.

2. **Customize configuration:**
   Edit `verifier.json` to match your project structure:
   ```json
   {
     "watch_dirs": ["src", "lib"],
     "test_dir": "tests",
     "working_set_dir": "tests/generated",
     "agent_mission": "testing",
     "claude_timeout": 300
   }
   ```

3. **Validate configuration:**
   ```bash
   uv run verifier validate
   ```

## Basic Usage

### Starting the Verifier

To start monitoring your codebase:

```bash
uv run verifier start
```

The verifier will:
- Begin monitoring configured directories
- Start a Claude Code agent session
- Process file changes as they occur
- Generate tests automatically
- Report any bugs found

### Demo Mode

For testing without actually calling Claude Code:

```bash
uv run verifier demo
```

This uses a mock agent that simulates the behavior without making API calls.

### Checking Status

To see current configuration and status:

```bash
uv run verifier status
```

## Configuration Guide

### Core Settings

#### `watch_dirs`
List of directories to monitor for changes.
```json
"watch_dirs": ["src", "app", "lib"]
```

#### `test_dir`
Directory where tests are stored.
```json
"test_dir": "test"
```

#### `working_set_dir`
Directory for generated tests and artifacts.
```json
  "working_set_dir": "tests/working_set"
```

#### `watch_extensions`
File extensions to monitor.
```json
"watch_extensions": [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs"]
```

#### `agent_mission`
Mission for the Claude Code agent:
- `"testing"` - Generate and run tests
- `"docs"` - Generate documentation
- `"tooling"` - Create development tools

```json
"agent_mission": "testing"
```

#### `error_report_file`
Path to the error report file (JSONL format).
```json
  "error_report_file": "tests/working_set/error_report.jsonl"
```

#### `claude_timeout`
Timeout for Claude Code operations in seconds.
```json
"claude_timeout": 300
```

### Advanced Configuration

#### Filtering Behavior

The system automatically filters out:
- Compiled files (*.pyc, *.pyo, *.pyd)
- Version control files (.git, .gitignore)
- Log files (*.log)
- Temporary files (*.tmp, *.swp)
- System files (.DS_Store)
- Dependencies (node_modules, __pycache__)

#### Batching Behavior

Changes are batched to avoid processing every minor change:
- **Minimum interval**: 0.5 seconds between processing
- **Batch timeout**: 2.0 seconds maximum wait time
- **File size limits**: 1 byte minimum, 1MB maximum

## Working with the System

### Understanding the Workflow

1. **File Change Detection**: The system monitors your source files
2. **Change Filtering**: Irrelevant changes are filtered out
3. **Change Batching**: Multiple changes are grouped together
4. **Test Generation**: Claude Code analyzes changes and generates tests
5. **Test Execution**: Generated tests are run automatically
6. **Error Reporting**: Any bugs found are reported

### Monitoring Output

The verifier provides real-time feedback:

```
Starting Verifier Overseer...
Watching directory: src
Overseer started. Monitoring for changes...
File change detected: modified src/calculator.py
Processed batch of 1 changes

🚨 ERROR REPORT (HIGH)
File: src/calculator.py
Line: 15
Description: Division by zero not handled
Suggested Fix: Add zero check before division
Timestamp: 2024-01-15T10:30:00Z
```

### Error Reports

Error reports are stored in JSONL format and displayed with color coding:
- **Red**: High severity errors
- **Yellow**: Medium severity errors
- **Blue**: Low severity errors

### Working Set Management

The working set directory contains:
- `tests/` - Generated test files
- `artifacts/` - Additional generated files
- `reports/` - Error reports and metadata

## Command Line Options

### Global Options

All commands support:
- `--config, -c`: Specify configuration file path
- `--help`: Show command help

### Start Command

```bash
uv run verifier start [OPTIONS]
```

Options:
- `--watch-dir, -w`: Override watch directories (multiple allowed)
- `--mission, -m`: Override agent mission

Examples:
```bash
# Start with custom watch directories
uv run verifier start -w src -w lib

# Start with documentation mission
uv run verifier start -m docs

# Start with custom config file
uv run verifier start -c my-config.json
```

### Demo Command

```bash
uv run verifier demo [OPTIONS]
```

Same options as `start` command, but uses mock agent.

### Init Command

```bash
uv run verifier init [OPTIONS]
```

Options:
- `--output, -o`: Output configuration file path

### Status Command

```bash
uv run verifier status [OPTIONS]
```

Shows current configuration and validates directories.

### Validate Command

```bash
uv run verifier validate [OPTIONS]
```

Validates configuration and checks directory permissions.

## Best Practices

### Project Structure

Organize your project for optimal results:

```
my-project/
├── src/                    # Source code (watched)
│   ├── main.py
│   └── utils.py
├── test/                   # Regular tests
│   └── test_manual.py
├── tests/working_set/       # Generated tests
│   ├── tests/
│   ├── artifacts/
│   └── reports/
├── verifier.json          # Configuration
└── README.md
```

### Configuration Tips

1. **Watch Specific Directories**: Only watch directories with source code
2. **Exclude Build Directories**: Don't watch build, dist, or output directories
3. **Set Reasonable Timeouts**: Balance responsiveness with API costs
4. **Use Descriptive Missions**: Clear missions help Claude Code understand goals

### Workflow Integration

#### With Git

Add to `.gitignore`:
```
tests/working_set/
*.jsonl
```

#### With CI/CD

Consider running the verifier in CI:
```yaml
# .github/workflows/verifier.yml
name: Verifier
on: [push, pull_request]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: uv run verifier validate
```

#### With Development

Run the verifier in a separate terminal while developing:
```bash
# Terminal 1: Development
vim src/main.py

# Terminal 2: Verifier
uv run verifier start
```

## Troubleshooting

### Common Issues

#### "Configuration file not found"
- Run `uv run verifier init` to create default configuration
- Check the configuration file path

#### "Claude Code failed"
- Ensure `claude` CLI is installed and configured
- Check API credentials and permissions
- Verify network connectivity

#### "Watch directory does not exist"
- Verify directory paths in configuration
- Use absolute paths if needed
- Check directory permissions

#### "No changes detected"
- Verify file extensions are in `watch_extensions`
- Check if files are being filtered by ignore patterns
- Ensure directories are being watched

### Performance Issues

#### High CPU Usage
- Reduce the number of watched directories
- Add more ignore patterns
- Increase `min_change_interval`

#### Slow Response
- Reduce `claude_timeout`
- Increase `batch_timeout` to process more changes together
- Use demo mode for testing

### Debug Mode

Enable verbose output by modifying the source code to add logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Advanced Usage

### Custom Missions

Create custom missions by modifying the agent mission:

```json
{
  "agent_mission": "Generate comprehensive integration tests for API endpoints"
}
```

### Multiple Configurations

Use different configurations for different projects:

```bash
# Web project
uv run verifier start -c web-config.json

# API project
uv run verifier start -c api-config.json
```

### Integration with IDEs

Many IDEs can be configured to run the verifier automatically:

#### VS Code
Add to `.vscode/tasks.json`:
```json
{
  "label": "Start Verifier",
  "type": "shell",
  "command": "uv run verifier start",
  "group": "build",
  "presentation": {
    "echo": true,
    "reveal": "always",
    "focus": false,
    "panel": "dedicated"
  }
}
```

### Extending the System

The system is designed to be extensible. Consider:
- Adding new file watchers
- Implementing custom report formats
- Creating specialized agents for different tasks
- Adding integration with testing frameworks

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the configuration
3. Test with demo mode
4. Check error reports for details
5. Validate your setup with `uv run verifier validate`