# Usage Examples

## Basic Usage Examples

### 1. Quick Start

The simplest way to get started with the verifier system:

```bash
# Initialize configuration
python -m src.cli init

# Start monitoring with default settings
python -m src.cli start
```

This will:
- Create a default `verifier.json` configuration
- Watch the `src` directory for Python files
- Generate tests automatically when files change

### 2. Custom Configuration

Create a custom configuration for your project:

```bash
# Create custom config
python -m src.cli init --output my-verifier.json

# Edit the configuration file
{
  "watch_dirs": ["src", "lib", "api"],
  "test_dir": "tests",
  "working_set_dir": "tests/generated",
  "watch_extensions": [".py", ".js", ".ts"],
  "agent_mission": "testing",
  "claude_timeout": 300
}

# Start with custom config
python -m src.cli start --config my-verifier.json
```

### 3. Demo Mode

Try the system without Claude Code using mock agents:

```bash
# Start in demo mode
python -m src.cli demo

# Watch it generate mock tests
echo "def hello(): return 'world'" > src/example.py
```

## Advanced Usage Examples

### 1. Documentation Generation

Configure the system to generate documentation instead of tests:

```bash
# Start with documentation mission
python -m src.cli start --mission docs

# Or configure in JSON
{
  "agent_mission": "docs",
  "working_set_dir": "docs/generated",
  "watch_dirs": ["src", "lib"]
}
```

When you create or modify code:

```python
# src/new_api.py
class UserAPI:
    """API for user management"""
    
    def create_user(self, name: str, email: str) -> dict:
        """Create a new user"""
        return {"name": name, "email": email, "id": generate_id()}
    
    def get_user(self, user_id: str) -> dict:
        """Get user by ID"""
        return database.get_user(user_id)
```

The system will automatically generate:
- API documentation with method signatures
- Usage examples
- Parameter documentation
- Return value documentation

### 2. Multi-Directory Monitoring

Monitor multiple directories with different configurations:

```bash
# Monitor source and API directories
python -m src.cli start \
  --watch-dir src \
  --watch-dir api \
  --watch-dir lib
```

Or in configuration:

```json
{
  "watch_dirs": ["src", "api", "lib", "utils"],
  "watch_extensions": [".py", ".js", ".ts", ".go"],
  "agent_mission": "testing"
}
```

### 3. Custom Working Set Directory

Organize generated files in a custom location:

```json
{
  "working_set_dir": "automation/generated",
  "test_dir": "tests",
  "error_report_file": "automation/generated/errors.jsonl",
  "claude_log_file": "automation/generated/claude.jsonl"
}
```

## Programming Examples

### 1. Programmatic Usage

Use the verifier system programmatically in your scripts:

```python
import asyncio
from src.config import VerifierConfig
from src.overseer import Overseer

async def main():
    # Create configuration
    config = VerifierConfig(
        watch_dirs=['src', 'lib'],
        agent_mission='testing',
        claude_timeout=600
    )
    
    # Create and start overseer
    overseer = Overseer(config)
    
    try:
        await overseer.start()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await overseer.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Custom Agent Implementation

Create a custom agent for specific needs:

```python
from src.agent import VerifierAgent
from src.config import VerifierConfig

class SecurityAgent(VerifierAgent):
    """Agent focused on security testing"""
    
    def _get_mission_prompt(self) -> str:
        return """
        You are a security testing agent. Your mission is to:
        1. Generate security tests for new code
        2. Check for common vulnerabilities
        3. Validate input sanitization
        4. Test authentication and authorization
        5. Report security issues with high priority
        """
    
    def _get_file_deltas_prompt(self, file_changes):
        base_prompt = super()._get_file_deltas_prompt(file_changes)
        return f"{base_prompt}\n\nFocus on security implications of these changes."

# Usage
config = VerifierConfig(agent_mission="security")
security_agent = SecurityAgent(config)
```

### 3. Working Set Management

Manage generated tests and artifacts:

```python
from src.working_set import WorkingSetManager
from pathlib import Path

# Create manager
manager = WorkingSetManager('tests/working_set')

# Create directory structure
manager.ensure_directory_structure()

# Generate a test file
test_content = """
import unittest
from src.calculator import Calculator

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()
    
    def test_addition(self):
        result = self.calc.add(2, 3)
        self.assertEqual(result, 5)
    
    def test_division_by_zero(self):
        with self.assertRaises(ValueError):
            self.calc.divide(10, 0)
"""

# Save test
test_file = manager.create_test_file('test_calculator_advanced', test_content)
print(f"Created test: {test_file}")

# List all tests
for test in manager.list_test_files():
    print(f"Test: {test.name}")

# Create metadata
metadata = {
    "version": "1.0.0",
    "generated_at": "2025-07-05T08:20:00Z",
    "total_tests": manager.get_working_set_size()
}
manager.create_metadata_file(metadata)
```

## Real-World Scenarios

### 1. Web API Development

Configuration for a web API project:

```json
{
  "watch_dirs": ["api", "models", "services"],
  "watch_extensions": [".py", ".js"],
  "agent_mission": "testing",
  "working_set_dir": "tests/api_tests",
  "claude_timeout": 300
}
```

Example file change:

```python
# api/users.py
from flask import Flask, request, jsonify
from models.user import User

app = Flask(__name__)

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    user = User.create(data['name'], data['email'])
    return jsonify(user.to_dict()), 201

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = User.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict())
```

Generated test:

```python
# tests/api_tests/test_users_api.py
import unittest
import json
from api.users import app

class TestUsersAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
    
    def test_create_user(self):
        response = self.app.post('/users', 
            json={'name': 'John Doe', 'email': 'john@example.com'})
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'John Doe')
    
    def test_get_user(self):
        # Create user first
        create_response = self.app.post('/users',
            json={'name': 'Jane Doe', 'email': 'jane@example.com'})
        user_id = json.loads(create_response.data)['id']
        
        # Get user
        response = self.app.get(f'/users/{user_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'Jane Doe')
    
    def test_get_nonexistent_user(self):
        response = self.app.get('/users/nonexistent')
        self.assertEqual(response.status_code, 404)
```

### 2. Data Processing Pipeline

Configuration for a data processing project:

```json
{
  "watch_dirs": ["processors", "transformers", "validators"],
  "watch_extensions": [".py"],
  "agent_mission": "testing",
  "working_set_dir": "tests/data_tests",
  "claude_timeout": 600
}
```

Example file:

```python
# processors/data_cleaner.py
import pandas as pd
from typing import List, Dict

class DataCleaner:
    """Cleans and validates data for processing"""
    
    def clean_csv(self, filepath: str) -> pd.DataFrame:
        """Clean CSV data by removing nulls and duplicates"""
        df = pd.read_csv(filepath)
        df = df.dropna()
        df = df.drop_duplicates()
        return df
    
    def validate_schema(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """Validate that DataFrame has required columns"""
        return all(col in df.columns for col in required_columns)
    
    def normalize_data(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """Normalize specified columns to 0-1 range"""
        for col in columns:
            if col in df.columns:
                df[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
        return df
```

Generated test:

```python
# tests/data_tests/test_data_cleaner.py
import unittest
import pandas as pd
import tempfile
import os
from processors.data_cleaner import DataCleaner

class TestDataCleaner(unittest.TestCase):
    def setUp(self):
        self.cleaner = DataCleaner()
    
    def test_clean_csv(self):
        # Create test CSV
        test_data = pd.DataFrame({
            'A': [1, 2, None, 4, 2],
            'B': ['a', 'b', 'c', 'd', 'b']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            test_data.to_csv(f.name, index=False)
            cleaned = self.cleaner.clean_csv(f.name)
            
        # Should remove null and duplicate rows
        self.assertEqual(len(cleaned), 3)
        self.assertFalse(cleaned.isnull().any().any())
        
        os.unlink(f.name)
    
    def test_validate_schema(self):
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        
        # Valid schema
        self.assertTrue(self.cleaner.validate_schema(df, ['A', 'B']))
        
        # Invalid schema
        self.assertFalse(self.cleaner.validate_schema(df, ['A', 'C']))
    
    def test_normalize_data(self):
        df = pd.DataFrame({'A': [1, 2, 3, 4], 'B': [10, 20, 30, 40]})
        normalized = self.cleaner.normalize_data(df, ['A', 'B'])
        
        # Check normalization
        self.assertAlmostEqual(normalized['A'].min(), 0.0)
        self.assertAlmostEqual(normalized['A'].max(), 1.0)
        self.assertAlmostEqual(normalized['B'].min(), 0.0)
        self.assertAlmostEqual(normalized['B'].max(), 1.0)
```

### 3. Machine Learning Model

Configuration for ML model development:

```json
{
  "watch_dirs": ["models", "features", "training"],
  "agent_mission": "testing",
  "working_set_dir": "tests/ml_tests",
  "claude_timeout": 900
}
```

Example model:

```python
# models/classifier.py
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

class TextClassifier:
    """Text classification model using Random Forest"""
    
    def __init__(self, n_estimators=100):
        self.model = RandomForestClassifier(n_estimators=n_estimators)
        self.is_trained = False
    
    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        """Train the classifier"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Return training metrics
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        return {
            'accuracy': accuracy,
            'train_size': len(X_train),
            'test_size': len(X_test)
        }
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        return self.model.predict(X)
```

Generated test:

```python
# tests/ml_tests/test_text_classifier.py
import unittest
import numpy as np
from models.classifier import TextClassifier

class TestTextClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = TextClassifier()
        # Create sample data
        self.X = np.random.randn(100, 10)
        self.y = np.random.randint(0, 2, 100)
    
    def test_initialization(self):
        self.assertFalse(self.classifier.is_trained)
        self.assertIsNotNone(self.classifier.model)
    
    def test_train(self):
        metrics = self.classifier.train(self.X, self.y)
        
        self.assertTrue(self.classifier.is_trained)
        self.assertIn('accuracy', metrics)
        self.assertIn('train_size', metrics)
        self.assertIn('test_size', metrics)
        self.assertGreaterEqual(metrics['accuracy'], 0.0)
        self.assertLessEqual(metrics['accuracy'], 1.0)
    
    def test_predict_before_training(self):
        with self.assertRaises(ValueError):
            self.classifier.predict(self.X)
    
    def test_predict_after_training(self):
        self.classifier.train(self.X, self.y)
        predictions = self.classifier.predict(self.X[:10])
        
        self.assertEqual(len(predictions), 10)
        self.assertTrue(all(p in [0, 1] for p in predictions))
```

## Error Handling Examples

### 1. Monitoring Error Reports

```python
from src.reporter import ReportMonitor
import time

# Create monitor
monitor = ReportMonitor('tests/working_set/error_report.jsonl')

# Check for errors periodically
while True:
    if monitor.has_new_reports():
        reports = monitor.get_new_reports()
        for report in reports:
            print(f"🚨 {report['severity'].upper()}: {report['description']}")
            print(f"   File: {report['file']}:{report['line']}")
            if report['suggested_fix']:
                print(f"   Fix: {report['suggested_fix']}")
    time.sleep(5)
```

### 2. Custom Error Handling

```python
from src.reporter import ErrorReporter

class CustomErrorHandler:
    def __init__(self, report_file):
        self.reporter = ErrorReporter(report_file)
    
    def handle_syntax_error(self, file_path, line_no, error_msg):
        self.reporter.report_error(
            file_path=file_path,
            line=line_no,
            severity='high',
            description=f'Syntax error: {error_msg}',
            suggested_fix='Check syntax and fix compilation errors'
        )
    
    def handle_style_issue(self, file_path, line_no, issue):
        self.reporter.report_error(
            file_path=file_path,
            line=line_no,
            severity='low',
            description=f'Style issue: {issue}',
            suggested_fix='Follow PEP8 style guidelines'
        )
```

## Integration Examples

### 1. CI/CD Integration

```yaml
# .github/workflows/verifier.yml
name: Automated Verification
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run verifier
      run: |
        python -m src.cli start --config ci-verifier.json
        # Let it run for a bit to process files
        sleep 30
        
    - name: Check for errors
      run: |
        if [ -f "tests/working_set/error_report.jsonl" ]; then
          echo "Errors found:"
          cat tests/working_set/error_report.jsonl
          exit 1
        fi
```

### 2. Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run verifier on staged files
staged_files=$(git diff --cached --name-only --diff-filter=AM | grep -E "\.(py|js|ts)$")

if [ -n "$staged_files" ]; then
    echo "Running verifier on staged files..."
    python -m src.cli demo --config pre-commit.json
    
    # Check for high severity errors
    if [ -f "tests/working_set/error_report.jsonl" ]; then
        high_errors=$(grep '"severity": "high"' tests/working_set/error_report.jsonl | wc -l)
        if [ $high_errors -gt 0 ]; then
            echo "High severity errors found. Commit blocked."
            exit 1
        fi
    fi
fi
```

These examples demonstrate the flexibility and power of the verifier system across different use cases and integration scenarios.