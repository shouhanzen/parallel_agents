# API Reference

## Core Classes

### VerifierConfig

Configuration management for the verifier system.

**Location**: `src/config.py:6`

```python
class VerifierConfig(BaseModel):
    """Configuration for the verifier system"""
```

#### Fields

- `watch_dirs: List[str]` - Directories to watch for changes (default: ['src'])
- `test_dir: str` - Directory to write tests (default: 'tests')
- `working_set_dir: str` - Working set directory for generated tests (default: 'tests/working_set')
- `watch_extensions: List[str]` - File extensions to watch (default: ['.py', '.js', '.ts', ...])
- `agent_mission: str` - Mission for the verifier agent (default: 'testing')
- `error_report_file: str` - File to write error reports (default: 'tests/working_set/error_report.jsonl')
- `claude_timeout: int` - Timeout for Claude Code operations in seconds (default: 300)
- `claude_log_file: str` - File to write Claude code interaction logs (default: 'tests/working_set/claude_logs.jsonl')

#### Methods

##### `from_file(config_path: str) -> VerifierConfig`

Load configuration from a JSON file.

```python
config = VerifierConfig.from_file('verifier.json')
```

##### `to_file(config_path: str)`

Save configuration to a JSON file.

```python
config.to_file('verifier.json')
```

---

### Overseer

Main orchestrator that coordinates all components.

**Location**: `src/overseer.py:15`

```python
class Overseer:
    """Main overseer process that coordinates all components"""
```

#### Constructor

```python
def __init__(self, config: VerifierConfig):
```

#### Methods

##### `async start()`

Start the overseer process with all components.

```python
overseer = Overseer(config)
await overseer.start()
```

##### `async stop()`

Stop the overseer process and cleanup resources.

```python
await overseer.stop()
```

##### `is_running() -> bool`

Check if the overseer is currently running.

```python
if overseer.is_running():
    print("Overseer is active")
```

---

### VerifierAgent

Agent that interfaces with Claude Code to generate and run tests.

**Location**: `src/agent.py:11`

```python
class VerifierAgent:
    """Agent that interfaces with Claude Code to generate and run tests"""
```

#### Constructor

```python
def __init__(self, config: VerifierConfig):
```

#### Methods

##### `async start_session()`

Start a new verifier session with Claude Code.

```python
agent = VerifierAgent(config)
await agent.start_session()
```

##### `async process_file_changes(file_changes: List[Dict[str, Any]])`

Process file changes and generate tests.

```python
changes = [
    {'file_path': 'src/example.py', 'action': 'created'},
    {'file_path': 'src/utils.py', 'action': 'modified'}
]
await agent.process_file_changes(changes)
```

##### `get_conversation_history() -> List[Dict[str, Any]]`

Get the conversation history with Claude Code.

```python
history = agent.get_conversation_history()
for entry in history:
    print(f"Type: {entry['type']}, Response: {entry['response']}")
```

##### `stop_session()`

Stop the verifier session.

```python
agent.stop_session()
```

---

### DocumentationAgent

Agent that generates and updates documentation for code changes.

**Location**: `src/doc_agent.py:11`

```python
class DocumentationAgent:
    """Agent that interfaces with Claude Code to generate and update documentation"""
```

#### Constructor

```python
def __init__(self, config: VerifierConfig):
```

#### Methods

##### `async start_session()`

Start a new documentation session.

```python
doc_agent = DocumentationAgent(config)
await doc_agent.start_session()
```

##### `async process_file_changes(file_changes: List[Dict[str, Any]])`

Process file changes and generate documentation.

```python
changes = [
    {'file_path': 'src/new_feature.py', 'action': 'created', 'content': '...'}
]
await doc_agent.process_file_changes(changes)
```

---

### WorkingSetManager

Manages the working set directory for generated tests and artifacts.

**Location**: `src/working_set.py:7`

```python
class WorkingSetManager:
    """Manages the working set directory for generated tests and artifacts"""
```

#### Constructor

```python
def __init__(self, working_set_dir: str):
```

#### Methods

##### `create_test_file(test_name: str, content: str) -> Path`

Create a test file in the working set.

```python
manager = WorkingSetManager('tests/working_set')
test_file = manager.create_test_file('test_example', test_content)
```

##### `list_test_files() -> List[Path]`

List all test files in the working set.

```python
test_files = manager.list_test_files()
for test_file in test_files:
    print(f"Test: {test_file.name}")
```

##### `remove_test_file(test_name: str) -> bool`

Remove a test file from the working set.

```python
success = manager.remove_test_file('test_example')
if success:
    print("Test file removed")
```

##### `clean_working_set()`

Clean the working set directory.

```python
manager.clean_working_set()
```

##### `get_working_set_size() -> int`

Get the number of files in the working set.

```python
size = manager.get_working_set_size()
print(f"Working set contains {size} files")
```

##### `ensure_directory_structure()`

Ensure the working set has proper directory structure.

```python
manager.ensure_directory_structure()
```

---

### FilesystemWatcher

Monitors filesystem changes using watchdog.

**Location**: `src/watcher.py:31`

```python
class FilesystemWatcher:
    """Watches filesystem changes in a directory"""
```

#### Constructor

```python
def __init__(self, watch_dir: str, callback: Callable[[str, str], None]):
```

#### Methods

##### `start()`

Start watching the directory.

```python
def on_change(file_path: str, action: str):
    print(f"File {action}: {file_path}")

watcher = FilesystemWatcher('src', on_change)
watcher.start()
```

##### `stop()`

Stop watching the directory.

```python
watcher.stop()
```

##### `is_alive() -> bool`

Check if the watcher is running.

```python
if watcher.is_alive():
    print("Watcher is active")
```

---

### DeltaGate

Filters and batches file changes intelligently.

**Location**: `src/delta_gate.py:29`

```python
class DeltaGate:
    """Filters and batches file changes to determine if they warrant processing"""
```

#### Constructor

```python
def __init__(self, config: DeltaGateConfig = None):
```

#### Methods

##### `add_change(file_path: str, action: str) -> bool`

Add a file change to the gate.

```python
gate = DeltaGate()
if gate.add_change('src/example.py', 'modified'):
    print("Change accepted")
```

##### `should_process_batch() -> bool`

Check if we should process the current batch of changes.

```python
if gate.should_process_batch():
    batch = gate.get_batch()
    # Process batch...
```

##### `get_batch() -> List[Dict[str, Any]]`

Get the current batch of changes and reset.

```python
batch = gate.get_batch()
for change in batch:
    print(f"Processing: {change['action']} {change['file_path']}")
```

##### `get_pending_count() -> int`

Get the number of pending changes.

```python
count = gate.get_pending_count()
print(f"Pending changes: {count}")
```

---

### ErrorReporter

Handles error reporting to JSONL files.

**Location**: `src/reporter.py:8`

```python
class ErrorReporter:
    """Handles error reporting to JSONL files"""
```

#### Constructor

```python
def __init__(self, report_file: str):
```

#### Methods

##### `report_error(file_path: str, line: Optional[int], severity: str, description: str, suggested_fix: Optional[str] = None)`

Report an error to the JSONL file.

```python
reporter = ErrorReporter('error_report.jsonl')
reporter.report_error(
    file_path='src/example.py',
    line=42,
    severity='high',
    description='Potential null pointer exception',
    suggested_fix='Add null check before accessing property'
)
```

##### `get_pending_reports() -> List[Dict[str, Any]]`

Get all pending error reports.

```python
reports = reporter.get_pending_reports()
for report in reports:
    print(f"Error in {report['file']}: {report['description']}")
```

---

## Usage Examples

### Basic Setup

```python
from src.config import VerifierConfig
from src.overseer import Overseer

# Create configuration
config = VerifierConfig(
    watch_dirs=['src', 'lib'],
    agent_mission='testing'
)

# Start overseer
overseer = Overseer(config)
await overseer.start()
```

### Custom Agent Configuration

```python
from src.agent import VerifierAgent
from src.config import VerifierConfig

# Configure for documentation generation
config = VerifierConfig(
    agent_mission='docs',
    working_set_dir='docs/generated'
)

# Create documentation agent
agent = VerifierAgent(config)
await agent.start_session()

# Process file changes
changes = [
    {
        'file_path': 'src/new_api.py',
        'action': 'created',
        'content': 'class NewAPI: ...'
    }
]
await agent.process_file_changes(changes)
```

### Working Set Management

```python
from src.working_set import WorkingSetManager

# Create manager
manager = WorkingSetManager('tests/working_set')

# Ensure directory structure
manager.ensure_directory_structure()

# Create test file
test_content = '''
import unittest

class TestExample(unittest.TestCase):
    def test_basic(self):
        self.assertTrue(True)
'''

test_file = manager.create_test_file('test_example', test_content)
print(f"Created test: {test_file}")

# List all tests
for test in manager.list_test_files():
    print(f"Test file: {test.name}")
```

### Error Monitoring

```python
from src.reporter import ErrorReporter, ReportMonitor

# Create reporter
reporter = ErrorReporter('error_report.jsonl')

# Report an error
reporter.report_error(
    file_path='src/buggy_code.py',
    line=25,
    severity='medium',
    description='Unused variable detected',
    suggested_fix='Remove unused variable or use it'
)

# Monitor for new reports
monitor = ReportMonitor('error_report.jsonl')
if monitor.has_new_reports():
    reports = monitor.get_new_reports()
    for report in reports:
        print(f"New error: {report['description']}")
```

## Configuration Examples

### Basic Configuration

```json
{
  "watch_dirs": ["src"],
  "test_dir": "tests",
  "working_set_dir": "tests/working_set",
  "agent_mission": "testing"
}
```

### Advanced Configuration

```json
{
  "watch_dirs": ["src", "lib", "api"],
  "test_dir": "tests",
  "working_set_dir": "tests/generated",
  "watch_extensions": [".py", ".js", ".ts", ".go"],
  "agent_mission": "testing",
  "error_report_file": "reports/errors.jsonl",
  "claude_timeout": 600,
  "claude_log_file": "logs/claude.jsonl"
}
```

### Documentation Configuration

```json
{
  "watch_dirs": ["src"],
  "test_dir": "tests",
  "working_set_dir": "docs/generated",
  "agent_mission": "docs",
  "claude_timeout": 300
}
```