# API Reference

This document provides detailed API documentation for all modules in the Parallel Agents Verifier System.

## Core Modules

### `verifier.config`

#### `VerifierConfig`
Configuration management for the verifier system.

**Fields:**
- `watch_dirs: List[str]` - Directories to monitor (default: ["src"])
- `test_dir: str` - Directory for tests (default: "test")
- `working_set_dir: str` - Working directory for generated tests (default: "tests/working_set")
- `watch_extensions: List[str]` - File extensions to monitor
- `agent_mission: str` - Mission for the agent (default: "testing")
- `error_report_file: str` - Error report file path
- `claude_timeout: int` - Claude Code timeout in seconds (default: 300)
- `claude_log_file: str` - File to write Claude code interaction logs (default: "tests/working_set/claude_logs.jsonl")

**Methods:**
```python
@classmethod
def from_file(cls, config_path: str) -> 'VerifierConfig'
```
Load configuration from JSON file.

```python
def to_file(self, config_path: str) -> None
```
Save configuration to JSON file.

```python
def get_default_config() -> VerifierConfig
```
Get default configuration instance.

---

### `verifier.overseer`

#### `Overseer`
Main coordinator process for the verifier system.

**Constructor:**
```python
def __init__(self, config: VerifierConfig)
```

**Methods:**
```python
async def start(self) -> None
```
Start the overseer process and begin monitoring.

```python
async def stop(self) -> None
```
Stop the overseer process gracefully.

```python
def is_running(self) -> bool
```
Check if the overseer is currently running.

**Private Methods:**
- `_on_file_change(self, file_path: str, action: str)` - Handle file system changes
- `_setup_watchers(self)` - Initialize filesystem watchers

- `async _process_pending_changes(self)` - Process batched file changes
- `_process_error_reports(self)` - Handle new error reports
- `_display_error_report(self, report: Dict[str, Any])` - Display formatted error reports

---

### `verifier.agent`

#### `VerifierAgent`
Agent that interfaces with Claude Code for test generation.

**Constructor:**
```python
def __init__(self, config: VerifierConfig)
```

**Methods:**
```python
async def start_session(self) -> None
```
Initialize a new verifier session with Claude Code.

```python
async def process_file_changes(self, file_changes: List[Dict[str, Any]]) -> None
```
Process a batch of file changes and generate tests.

```python
def get_conversation_history(self) -> List[Dict[str, Any]]
```
Get the conversation history with Claude Code.

```python
def stop_session(self) -> None
```
Stop the current verifier session.

**Private Methods:**
- `_get_mission_prompt(self) -> str` - Generate mission prompt for Claude Code
- `_get_file_deltas_prompt(self, file_changes: List[Dict[str, Any]]) -> str` - Generate change prompt
- `async _run_claude_code(self, prompt: str) -> str` - Execute Claude Code with prompt
- `_read_file_content(self, file_path: str) -> str` - Safely read file content

---

### `verifier.watcher`

#### `FilesystemWatcher`
Monitors filesystem changes in specified directories.

**Constructor:**
```python
def __init__(self, watch_dir: str, callback: Callable[[str, str], None])
```

**Methods:**
```python
def start(self) -> None
```
Start monitoring the directory.

```python
def stop(self) -> None
```
Stop monitoring and cleanup resources.

```python
def is_alive(self) -> bool
```
Check if the watcher is currently active.

#### `FileChangeHandler`
Internal event handler for filesystem events.

**Constructor:**
```python
def __init__(self, callback: Callable[[str, str], None], watch_extensions: Optional[Set[str]] = None)
```

**Methods:**
- `on_modified(self, event)` - Handle file modification events
- `on_created(self, event)` - Handle file creation events
- `on_deleted(self, event)` - Handle file deletion events
- `_should_process_file(self, file_path: str) -> bool` - Check if file should be processed

---

### `verifier.delta_gate`

#### `DeltaGate`
Filters and batches file changes for efficient processing.

**Constructor:**
```python
def __init__(self, config: DeltaGateConfig = None)
```

**Methods:**
```python
def add_change(self, file_path: str, action: str) -> bool
```
Add a file change to the gate. Returns True if change was accepted.

```python
def should_process_batch(self) -> bool
```
Check if the current batch should be processed.

```python
def get_batch(self) -> List[Dict[str, Any]]
```
Get the current batch of changes and reset the gate.

```python
def get_pending_count(self) -> int
```
Get the number of pending changes.

```python
def clear_pending(self) -> None
```
Clear all pending changes.

#### `DeltaGateConfig`
Configuration for the delta gate.

**Fields:**
- `min_change_interval: float` - Minimum seconds between processing (default: 0.5)
- `batch_timeout: float` - Maximum seconds to wait for batching (default: 2.0)
- `ignore_patterns: Set[str]` - File patterns to ignore
- `min_file_size: int` - Minimum file size to process (default: 1)
- `max_file_size: int` - Maximum file size to process (default: 1MB)

#### `FileChange`
Represents a single file change event.

**Fields:**
- `file_path: str` - Path to the changed file
- `action: str` - Type of change ('created', 'modified', 'deleted')
- `timestamp: float` - When the change occurred
- `size: Optional[int]` - File size (if applicable)

---

### `verifier.reporter`

#### `ErrorReporter`
Handles error reporting to JSONL files.

**Constructor:**
```python
def __init__(self, report_file: str)
```

**Methods:**
```python
def report_error(self, file_path: str, line: Optional[int], severity: str, 
                description: str, suggested_fix: Optional[str] = None) -> None
```
Report an error to the JSONL file.

```python
def get_pending_reports(self) -> List[Dict[str, Any]]
```
Get all pending error reports.

```python
def clear_reports(self) -> None
```
Clear all reports.

```python
def pop_report(self) -> Optional[Dict[str, Any]]
```
Remove and return the first report.

#### `ReportMonitor`
Monitors the error report file for changes.

**Constructor:**
```python
def __init__(self, report_file: str)
```

**Methods:**
```python
def has_new_reports(self) -> bool
```
Check if there are new reports since last check.

```python
def get_new_reports(self) -> List[Dict[str, Any]]
```
Get new reports and mark them as processed.

---

### `verifier.working_set`

#### `WorkingSetManager`
Manages the working set directory for generated tests and artifacts.

**Constructor:**
```python
def __init__(self, working_set_dir: str)
```

**Methods:**
```python
def create_test_file(self, test_name: str, content: str) -> Path
```
Create a test file in the working set.

```python
def list_test_files(self) -> List[Path]
```
List all test files in the working set.

```python
def remove_test_file(self, test_name: str) -> bool
```
Remove a test file from the working set.

```python
def clean_working_set(self) -> None
```
Clean the working set directory.

```python
def get_working_set_size(self) -> int
```
Get the number of files in the working set.

```python
def create_metadata_file(self, metadata: Dict[str, Any]) -> Path
```
Create a metadata file for the working set.

```python
def read_metadata(self) -> Optional[Dict[str, Any]]
```
Read metadata from the working set.

```python
def ensure_directory_structure(self) -> None
```
Ensure the working set has proper directory structure.

```python
def get_working_set_path(self) -> Path
```
Get the working set directory path.

---

### `verifier.cli`

#### CLI Commands

**`start`**
Start the verifier overseer process.

Options:
- `--config, -c`: Configuration file path (default: verifier.json)
- `--watch-dir, -w`: Directories to watch (multiple allowed)
- `--mission, -m`: Agent mission (testing, docs, tooling)

**`demo`**
Start the verifier with mock agent for testing.

Options: Same as `start`

**`init`**
Initialize a new verifier configuration.

Options:
- `--output, -o`: Output configuration file (default: verifier.json)

**`status`**
Show verifier status and configuration.

Options:
- `--config, -c`: Configuration file path (default: verifier.json)

**`validate`**
Validate the verifier configuration.

Options:
- `--config, -c`: Configuration file path (default: verifier.json)

## Error Report Format

Error reports are stored in JSONL format with the following structure:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "file": "src/calculator.py",
  "line": 42,
  "severity": "high|medium|low",
  "description": "Bug description",
  "suggested_fix": "Optional fix suggestion"
}
```

## Configuration Schema

```json
{
  "watch_dirs": ["src"],
  "test_dir": "test",
  "working_set_dir": "tests/working_set",
  "watch_extensions": [".py", ".js", ".ts"],
  "agent_mission": "testing",
  "error_report_file": "tests/working_set/error_report.jsonl",
  "claude_timeout": 300,
  "claude_log_file": "tests/working_set/claude_logs.jsonl"
}
```

## Exception Handling

All modules implement comprehensive exception handling:

- `RuntimeError`: For Claude Code execution failures
- `FileNotFoundError`: For missing files/directories
- `TimeoutError`: For operation timeouts
- `ValidationError`: For configuration validation failures
- `ValueError`: For invalid parameter values

## Logging

The system uses print statements for logging. For production use, consider implementing structured logging with the `logging` module.