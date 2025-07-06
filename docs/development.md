# Development Guide

This guide covers development practices, testing, and contribution guidelines for the Parallel Agents Verifier System.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- `uv` package manager
- `claude` CLI tool (for integration testing)
- Git for version control

### Environment Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd parallel_agents
   ```

2. **Create development environment:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install in development mode:**
   ```bash
   uv pip install -e .
   ```

4. **Install development dependencies:**
   ```bash
   uv pip install pytest pytest-asyncio pytest-cov black flake8 mypy
   ```

### Project Structure

```
parallel_agents/
├── src/                    # Example source code
│   ├── __init__.py
│   └── calculator.py
├── verifier/              # Main package
│   ├── __init__.py
│   ├── agent.py          # Claude Code integration
│   ├── cli.py            # Command line interface
│   ├── config.py         # Configuration management
│   ├── delta_gate.py     # Change filtering
│   ├── overseer.py       # Main coordinator
│   ├── reporter.py       # Error reporting
│   ├── watcher.py        # File system monitoring
│   └── working_set.py    # Test artifact management
├── tests/                 # Unit tests
│   ├── test_config.py
│   └── test_delta_gate.py
├── test/                  # Integration tests
│   └── working_set/       # Generated artifacts
├── docs/                  # Documentation
├── main.py               # Entry point
├── test_basic.py         # Basic system tests
├── verifier.json         # Configuration
├── pyproject.toml        # Package configuration
└── README.md
```

## Code Style and Standards

### Python Style Guide

This project follows PEP 8 with the following conventions:

- **Line Length**: 88 characters (Black default)
- **String Quotes**: Double quotes for strings, single quotes for short literals
- **Imports**: Use absolute imports, group by standard library, third-party, local
- **Type Hints**: Use type hints for all public functions and methods
- **Docstrings**: Use Google-style docstrings for all public APIs

### Code Formatting

Use `black` for automatic code formatting:

```bash
black verifier/ tests/
```

### Linting

Use `flake8` for linting:

```bash
flake8 verifier/ tests/
```

### Type Checking

Use `mypy` for static type checking:

```bash
mypy verifier/
```

### Pre-commit Hooks

Consider setting up pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
```

## Testing

### Test Structure

The project uses multiple testing approaches:

1. **Unit Tests** (`tests/`): Test individual components in isolation
2. **Integration Tests** (`test_basic.py`): Test component interactions
3. **End-to-End Tests**: Test the complete system workflow

### Running Tests

#### Basic Tests
```bash
python test_basic.py
```

#### Unit Tests
```bash
pytest tests/
```

#### With Coverage
```bash
pytest --cov=verifier --cov-report=html tests/
```

### Test Categories

#### Unit Tests

Test individual components:

```python
# tests/test_config.py
import pytest
from src.config import VerifierConfig

def test_default_config():
    config = VerifierConfig()
    assert config.watch_dirs == ["src"]
    assert config.agent_mission == "testing"

def test_config_validation():
    config = VerifierConfig(watch_dirs=[])
    assert len(config.watch_dirs) == 0
```

#### Integration Tests

Test component interactions:

```python
# test_basic.py
def test_filesystem_watcher():
    changes = []
    
    def on_change(file_path, action):
        changes.append((file_path, action))
    
    with tempfile.TemporaryDirectory() as temp_dir:
        watcher = FilesystemWatcher(temp_dir, on_change)
        watcher.start()
        
        # Create test file
        test_file = Path(temp_dir) / "test.py"
        test_file.write_text("print('hello')")
        
        time.sleep(0.5)
        watcher.stop()
        
        assert len(changes) > 0
```

#### Mock Testing

Use mocks for external dependencies:

```python
from unittest.mock import patch, MagicMock
import pytest

@patch('verifier.agent.subprocess')
async def test_claude_code_execution(mock_subprocess):
    # Mock subprocess execution
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = (b"Success", b"")
    mock_subprocess.create_subprocess_exec.return_value = mock_process
    
    agent = VerifierAgent(VerifierConfig())
    result = await agent._run_claude_code("test prompt")
    
    assert result == "Success"
```

### Test Data

Create test fixtures for consistent testing:

```python
@pytest.fixture
def temp_config():
    with tempfile.TemporaryDirectory() as temp_dir:
        config = VerifierConfig(working_set_dir=temp_dir)
        yield config

@pytest.fixture
def sample_changes():
    return [
        {"file_path": "src/test.py", "action": "created", "timestamp": time.time()},
        {"file_path": "src/test.py", "action": "modified", "timestamp": time.time()},
    ]
```

## Development Workflow

### Feature Development

1. **Create Feature Branch:**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Implement Feature:**
   - Write tests first (TDD approach)
   - Implement the feature
   - Update documentation

3. **Test Thoroughly:**
   ```bash
   python test_basic.py
   pytest tests/
   black verifier/
   flake8 verifier/
   mypy verifier/
   ```

4. **Commit and Push:**
   ```bash
   git add .
   git commit -m "Add new feature: description"
   git push origin feature/new-feature
   ```

### Bug Fixes

1. **Create Bug Fix Branch:**
   ```bash
   git checkout -b bugfix/issue-description
   ```

2. **Write Failing Test:**
   ```python
   def test_bug_reproduction():
       # Test that reproduces the bug
       pass
   ```

3. **Fix the Bug:**
   - Implement the fix
   - Ensure test passes
   - Verify no regression

4. **Test and Commit:**
   ```bash
   pytest tests/
   git add .
   git commit -m "Fix: description of bug fix"
   ```

### Code Review Process

1. **Self Review:**
   - Check code style and formatting
   - Verify tests pass
   - Review documentation updates

2. **Peer Review:**
   - Create pull request
   - Request reviews from team members
   - Address feedback

3. **Automated Checks:**
   - CI/CD pipeline runs tests
   - Code quality checks pass
   - Coverage requirements met

## Architecture Guidelines

### Component Design

#### Single Responsibility
Each component should have a single, well-defined responsibility:

```python
# Good: Focused on file watching
class FilesystemWatcher:
    def __init__(self, watch_dir, callback):
        self.watch_dir = watch_dir
        self.callback = callback
```

#### Dependency Injection
Use dependency injection for testability:

```python
# Good: Dependencies injected
class Overseer:
    def __init__(self, config, agent=None, watcher=None):
        self.config = config
        self.agent = agent or VerifierAgent(config)
        self.watcher = watcher or FilesystemWatcher(config.watch_dirs[0])
```

#### Error Handling
Implement comprehensive error handling:

```python
async def process_changes(self, changes):
    try:
        result = await self.agent.process_file_changes(changes)
        return result
    except TimeoutError:
        logger.error("Agent timeout while processing changes")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

### Configuration Management

#### Environment Variables
Support environment variable overrides:

```python
import os

class VerifierConfig(BaseModel):
    claude_timeout: int = Field(
        default=300,
        description="Claude Code timeout in seconds"
    )
    
    @classmethod
    def from_env(cls):
        return cls(
            claude_timeout=int(os.getenv("CLAUDE_TIMEOUT", "300"))
        )
```

#### Validation
Validate configuration at startup:

```python
def validate_config(config: VerifierConfig):
    for watch_dir in config.watch_dirs:
        if not Path(watch_dir).exists():
            raise ValueError(f"Watch directory does not exist: {watch_dir}")
```

### Performance Considerations

#### Async Operations
Use async/await for I/O operations:

```python
async def process_file_changes(self, changes):
    tasks = []
    for change in changes:
        task = asyncio.create_task(self._process_single_change(change))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

#### Memory Management
Clean up resources properly:

```python
class ResourceManager:
    def __init__(self):
        self.resources = []
    
    def add_resource(self, resource):
        self.resources.append(resource)
    
    def cleanup(self):
        for resource in self.resources:
            try:
                resource.close()
            except Exception as e:
                logger.warning(f"Error cleaning up resource: {e}")
```

## Debugging

### Logging Setup

Add comprehensive logging:

```python
import logging

# In main module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('verifier.log'),
        logging.StreamHandler()
    ]
)

# In each module
logger = logging.getLogger(__name__)
```

### Debug Mode

Support debug mode in configuration:

```python
class VerifierConfig(BaseModel):
    debug: bool = Field(default=False, description="Enable debug mode")
    
    def setup_logging(self):
        level = logging.DEBUG if self.debug else logging.INFO
        logging.getLogger().setLevel(level)
```

### Troubleshooting Tools

#### Health Check
```python
def health_check(config: VerifierConfig):
    """Check system health"""
    checks = {
        "config_valid": True,
        "watch_dirs_exist": all(Path(d).exists() for d in config.watch_dirs),
        "working_set_writable": Path(config.working_set_dir).parent.exists(),
        "claude_code_available": shutil.which("claude") is not None,
    }
    return checks
```

#### Performance Profiling
```python
import cProfile
import pstats

def profile_function(func):
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        result = func(*args, **kwargs)
        pr.disable()
        
        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative')
        stats.print_stats()
        
        return result
    return wrapper
```

## Contributing

### Contribution Guidelines

1. **Follow Code Style**: Use Black, flake8, and mypy
2. **Write Tests**: All new features must include tests
3. **Update Documentation**: Update relevant documentation
4. **Atomic Commits**: Make small, focused commits
5. **Descriptive Messages**: Use clear commit messages

### Pull Request Process

1. **Fork the Repository**
2. **Create Feature Branch**
3. **Make Changes**
4. **Write/Update Tests**
5. **Update Documentation**
6. **Submit Pull Request**

### Issue Reporting

When reporting issues:

1. **Use Issue Template**
2. **Provide Reproduction Steps**
3. **Include Configuration**
4. **Add Error Messages**
5. **Specify Environment**

### Feature Requests

For new features:

1. **Describe Use Case**
2. **Explain Benefit**
3. **Consider Alternatives**
4. **Provide Examples**

## Release Process

### Version Management

Use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Checklist

1. **Update Version**: In `pyproject.toml`
2. **Update Changelog**: Document changes
3. **Run All Tests**: Ensure quality
4. **Update Documentation**: Reflect changes
5. **Tag Release**: Create git tag
6. **Build Package**: Create distribution
7. **Publish**: Upload to PyPI

### Deployment

For deployment:

```bash
# Build package
uv build

# Test upload
uv publish --repository-url https://test.pypi.org/legacy/

# Production upload
uv publish
```

## Future Enhancements

### Planned Features

1. **Web Interface**: Real-time monitoring dashboard
2. **Plugin System**: Custom agent behaviors
3. **Integration APIs**: REST API for external tools
4. **Multi-language Support**: Support for more languages
5. **Performance Metrics**: Detailed performance tracking

### Architecture Improvements

1. **Microservices**: Split into smaller services
2. **Event Sourcing**: Better event handling
3. **Distributed Processing**: Handle large codebases
4. **Caching**: Improve performance
5. **Security**: Enhanced security features

### Community

1. **Documentation**: Expand documentation
2. **Examples**: More usage examples
3. **Tutorials**: Step-by-step guides
4. **Community**: Build user community
5. **Ecosystem**: Integration with other tools