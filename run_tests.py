#!/usr/bin/env python3
"""Test runner script for the verifier project"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"❌ {description} failed with exit code {result.returncode}")
        return False
    else:
        print(f"✅ {description} passed")
        return True


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run verifier tests")
    
    # Test type options
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--fast", action="store_true", help="Run fast tests only (exclude slow tests)")
    
    # Coverage options
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--coverage-html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--coverage-xml", action="store_true", help="Generate XML coverage report")
    
    # Output options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
    parser.add_argument("--failfast", "-x", action="store_true", help="Stop on first failure")
    
    # Test selection
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    parser.add_argument("--file", help="Run specific test file")
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Test selection
    if args.unit:
        cmd.extend(["-m", "not integration and not e2e"])
    elif args.integration:
        cmd.extend(["--run-integration", "-m", "integration"])
    elif args.e2e:
        cmd.extend(["--run-e2e", "-m", "e2e"])
    elif args.all:
        cmd.extend(["--run-slow", "--run-integration", "--run-e2e"])
    
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    # Coverage options
    if args.coverage or args.coverage_html or args.coverage_xml:
        cmd.extend(["--cov=verifier", "--cov=src"])
        
        if args.coverage_html:
            cmd.extend(["--cov-report=html"])
            
        if args.coverage_xml:
            cmd.extend(["--cov-report=xml"])
            
        if not args.coverage_html and not args.coverage_xml:
            cmd.extend(["--cov-report=term-missing"])
    
    # Output options
    if args.verbose:
        cmd.append("-vv")
    elif args.quiet:
        cmd.append("-q")
        
    if args.failfast:
        cmd.append("-x")
    
    # Test pattern
    if args.pattern:
        cmd.extend(["-k", args.pattern])
    
    # Specific file
    if args.file:
        cmd.append(args.file)
    
    # Add tests directory if no specific file
    if not args.file:
        cmd.append("tests/")
    
    # Run the tests
    success = run_command(cmd, "Test execution")
    
    if success:
        print(f"\n🎉 All tests passed!")
        
        if args.coverage or args.coverage_html or args.coverage_xml:
            print("\n📊 Coverage report generated:")
            if args.coverage_html:
                html_path = Path("htmlcov/index.html")
                if html_path.exists():
                    print(f"  HTML: {html_path.absolute()}")
            if args.coverage_xml:
                xml_path = Path("coverage.xml")
                if xml_path.exists():
                    print(f"  XML: {xml_path.absolute()}")
    else:
        print(f"\n💥 Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()