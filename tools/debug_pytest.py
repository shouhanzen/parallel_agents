#!/usr/bin/env python3
"""Debug script to identify and fix pytest issues"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return the result"""
    print(f"\n🔍 {description}")
    print(f"   Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
        
        print(f"Exit code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return None


def check_import_issues():
    """Check for specific import issues"""
    print("\n🔬 Checking import issues...")
    
    # Test basic imports
    import_tests = [
        "from src.cli import cli",
        "from src.cli import main", 
        "from src.cli import start, demo, init, status, validate",
        "from src.cli import InteractiveVerifierCLI",
        "from src.agent import VerifierAgent",
        "from src.config import VerifierConfig"
    ]
    
    for import_test in import_tests:
        try:
            exec(import_test)
            print(f"✅ {import_test}")
        except Exception as e:
            print(f"❌ {import_test} - {e}")


def main():
    """Main debug function"""
    print("🐛 Pytest Debug Tool")
    print("=" * 50)
    
    # Check environment
    run_command(['python', '--version'], "Python version")
    run_command(['uv', '--version'], "UV version")
    
    # Check imports
    check_import_issues()
    
    # Test specific problematic files
    test_files = [
        'tests/cli/test_cli.py',
        'tests/e2e/test_e2e.py'
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            run_command(['uv', 'run', 'pytest', '--collect-only', test_file], 
                       f"Collecting tests from {test_file}")
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    # Try running all tests with verbose output
    run_command(['uv', 'run', 'pytest', '--collect-only', '-v'], 
               "Collecting all tests")


if __name__ == "__main__":
    main() 