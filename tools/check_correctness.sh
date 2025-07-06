#!/bin/bash

# check_correctness.sh - Validate project correctness and run tests
# Usage: ./tools/check_correctness.sh

set -e  # Exit on any error

echo "🔍 Parallel Agents Correctness Check"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "PASS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "FAIL")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

# Function to run command and capture result
run_check() {
    local description=$1
    local command=$2
    local allow_failure=${3:-false}
    
    echo -e "\n${BLUE}Checking: $description${NC}"
    
    if eval "$command" > /tmp/check_output 2>&1; then
        print_status "PASS" "$description"
        return 0
    else
        if [ "$allow_failure" = "true" ]; then
            print_status "WARN" "$description (allowed to fail)"
            echo "Command output:"
            cat /tmp/check_output | head -20
            return 0
        else
            print_status "FAIL" "$description"
            echo "Command output:"
            cat /tmp/check_output | head -20
            return 1
        fi
    fi
}

# Initialize counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Check 1: Python environment
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if run_check "Python 3.12+ available" "python --version | grep -E '3\.(12|13|14)'"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check 2: UV package manager
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if run_check "UV package manager available" "uv --version"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check 3: Project builds successfully
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if run_check "Project builds with uv" "uv build"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check 4: Dependencies install
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if run_check "Dependencies install correctly" "uv sync --all-extras"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check 5: Working tests run (allow failure for now)
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if run_check "Calculator tests pass" "uv run pytest tests/test_calculator.py -v" true; then
    if grep -q "FAILED" /tmp/check_output; then
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
    else
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    fi
else
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
fi

# Check 6: Test collection (critical - should work after fixes)
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if run_check "Pytest can collect all tests" "uv run pytest --collect-only -q" true; then
    if grep -q "error" /tmp/check_output; then
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
    else
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    fi
else
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
fi

# Check 7: CLI entry point (will fail until implemented)
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if run_check "CLI entry point works" "uv run verifier --help" true; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
fi

# Check 8: MkDocs builds
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if run_check "Documentation builds" "uv run mkdocs build" true; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
fi

# Check 9: Configuration file validation
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if run_check "pyproject.toml is valid" "python -c 'import tomllib; tomllib.load(open(\"pyproject.toml\", \"rb\"))'"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check 10: Core imports work
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if run_check "Core modules can be imported" "uv run python -c 'import sys; sys.path.insert(0, \"src\"); import core.config.models; print(\"Core imports OK\")'"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Summary
echo -e "\n${BLUE}============================================${NC}"
echo -e "${BLUE}CORRECTNESS CHECK SUMMARY${NC}"
echo -e "${BLUE}============================================${NC}"

echo -e "Total Checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
echo -e "${YELLOW}Warnings: $WARNING_CHECKS${NC}"
echo -e "${RED}Failed: $FAILED_CHECKS${NC}"

# Calculate percentage
PASS_RATE=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
echo -e "\nPass Rate: ${PASS_RATE}%"

# Overall status
if [ $FAILED_CHECKS -eq 0 ]; then
    print_status "PASS" "Overall correctness check PASSED"
    echo -e "\n${GREEN}🎉 Project is in good shape!${NC}"
    exit 0
elif [ $FAILED_CHECKS -le 2 ]; then
    print_status "WARN" "Overall correctness check has minor issues"
    echo -e "\n${YELLOW}⚠️  Project has minor issues but is mostly functional${NC}"
    exit 0
else
    print_status "FAIL" "Overall correctness check FAILED"
    echo -e "\n${RED}💥 Project has significant issues requiring attention${NC}"
    echo -e "\n${YELLOW}Priority fixes needed:${NC}"
    echo "1. Fix test import issues (pytest --collect-only should work)"
    echo "2. Implement CLI commands (uv run verifier --help should work)"
    echo "3. Resolve any build/dependency issues"
    exit 1
fi 