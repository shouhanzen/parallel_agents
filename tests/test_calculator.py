#!/usr/bin/env python3
"""Unit tests for the calculator module"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.calculator import add, subtract, multiply


class TestCalculatorFunctions:
    """Test the calculator functions"""
    
    def test_add_positive_numbers(self):
        """Test adding positive numbers"""
        assert add(2, 3) == 5
        assert add(10, 20) == 30
        assert add(1, 1) == 2
        
    def test_add_negative_numbers(self):
        """Test adding negative numbers"""
        assert add(-2, -3) == -5
        assert add(-10, -20) == -30
        assert add(-1, -1) == -2
        
    def test_add_mixed_numbers(self):
        """Test adding positive and negative numbers"""
        assert add(5, -3) == 2
        assert add(-5, 3) == -2
        assert add(10, -10) == 0
        
    def test_add_zero(self):
        """Test adding with zero"""
        assert add(0, 0) == 0
        assert add(5, 0) == 5
        assert add(0, 5) == 5
        assert add(-5, 0) == -5
        
    def test_add_floats(self):
        """Test adding floating point numbers"""
        assert add(1.5, 2.5) == 4.0
        assert add(0.1, 0.2) == pytest.approx(0.3)
        assert add(-1.5, 1.5) == 0.0
        
    def test_subtract_positive_numbers(self):
        """Test subtracting positive numbers"""
        assert subtract(5, 3) == 2
        assert subtract(10, 4) == 6
        assert subtract(1, 1) == 0
        
    def test_subtract_negative_numbers(self):
        """Test subtracting negative numbers"""
        assert subtract(-5, -3) == -2
        assert subtract(-10, -4) == -6
        assert subtract(-1, -1) == 0
        
    def test_subtract_mixed_numbers(self):
        """Test subtracting mixed positive and negative numbers"""
        assert subtract(5, -3) == 8
        assert subtract(-5, 3) == -8
        assert subtract(0, 5) == -5
        
    def test_subtract_zero(self):
        """Test subtracting with zero"""
        assert subtract(0, 0) == 0
        assert subtract(5, 0) == 5
        assert subtract(0, 5) == -5
        assert subtract(-5, 0) == -5
        
    def test_subtract_floats(self):
        """Test subtracting floating point numbers"""
        assert subtract(2.5, 1.5) == 1.0
        assert subtract(0.3, 0.1) == pytest.approx(0.2)
        assert subtract(-1.5, -1.5) == 0.0
        
    def test_multiply_positive_numbers(self):
        """Test multiplying positive numbers"""
        assert multiply(2, 3) == 6
        assert multiply(4, 5) == 20
        assert multiply(1, 10) == 10
        
    def test_multiply_negative_numbers(self):
        """Test multiplying negative numbers"""
        assert multiply(-2, -3) == 6
        assert multiply(-4, -5) == 20
        assert multiply(-1, -10) == 10
        
    def test_multiply_mixed_numbers(self):
        """Test multiplying positive and negative numbers"""
        assert multiply(2, -3) == -6
        assert multiply(-4, 5) == -20
        assert multiply(10, -1) == -10
        
    def test_multiply_zero(self):
        """Test multiplying with zero"""
        assert multiply(0, 0) == 0
        assert multiply(5, 0) == 0
        assert multiply(0, 5) == 0
        assert multiply(-5, 0) == 0
        
    def test_multiply_one(self):
        """Test multiplying with one"""
        assert multiply(1, 1) == 1
        assert multiply(5, 1) == 5
        assert multiply(1, 5) == 5
        assert multiply(-5, 1) == -5
        
    def test_multiply_floats(self):
        """Test multiplying floating point numbers"""
        assert multiply(2.5, 2.0) == 5.0
        assert multiply(0.5, 0.4) == pytest.approx(0.2)
        assert multiply(-1.5, 2.0) == -3.0


class TestCalculatorEdgeCases:
    """Test edge cases for calculator functions"""
    
    def test_large_numbers(self):
        """Test with large numbers"""
        large_num = 10**10
        assert add(large_num, large_num) == 2 * large_num
        assert subtract(large_num, large_num) == 0
        assert multiply(large_num, 2) == 2 * large_num
        
    def test_very_small_numbers(self):
        """Test with very small floating point numbers"""
        small_num = 1e-10
        assert add(small_num, small_num) == pytest.approx(2 * small_num)
        assert subtract(small_num, small_num) == pytest.approx(0.0)
        assert multiply(small_num, 2) == pytest.approx(2 * small_num)
        
    def test_precision_edge_cases(self):
        """Test floating point precision edge cases"""
        # Test cases that might cause floating point precision issues
        result = add(0.1, 0.1)
        assert result == pytest.approx(0.2)
        
        result = subtract(1.0, 0.9)
        assert result == pytest.approx(0.1)
        
        result = multiply(0.1, 10)
        assert result == pytest.approx(1.0)


class TestCalculatorParameterTypes:
    """Test calculator functions with different parameter types"""
    
    def test_integer_parameters(self):
        """Test with integer parameters"""
        assert isinstance(add(1, 2), int)
        assert isinstance(subtract(5, 3), int)
        assert isinstance(multiply(2, 4), int)
        
    def test_float_parameters(self):
        """Test with float parameters"""
        assert isinstance(add(1.0, 2.0), float)
        assert isinstance(subtract(5.0, 3.0), float)
        assert isinstance(multiply(2.0, 4.0), float)
        
    def test_mixed_parameters(self):
        """Test with mixed int and float parameters"""
        assert isinstance(add(1, 2.0), float)
        assert isinstance(subtract(5.0, 3), float)
        assert isinstance(multiply(2, 4.0), float)


class TestCalculatorDocstrings:
    """Test that calculator functions have proper documentation"""
    
    def test_add_docstring(self):
        """Test that add function has docstring"""
        assert add.__doc__ is not None
        assert "Add" in add.__doc__ or "add" in add.__doc__
        
    def test_subtract_docstring(self):
        """Test that subtract function has docstring"""
        assert subtract.__doc__ is not None
        assert "Subtract" in subtract.__doc__ or "subtract" in subtract.__doc__
        
    def test_multiply_docstring(self):
        """Test that multiply function has docstring"""
        assert multiply.__doc__ is not None
        assert "Multiply" in multiply.__doc__ or "multiply" in multiply.__doc__


class TestCalculatorIntegration:
    """Integration tests combining multiple calculator operations"""
    
    def test_chained_operations(self):
        """Test chaining multiple operations"""
        # (2 + 3) * 4 - 1 = 19
        result = subtract(multiply(add(2, 3), 4), 1)
        assert result == 19
        
        # (10 - 5) + (3 * 2) = 11
        result = add(subtract(10, 5), multiply(3, 2))
        assert result == 11
        
    def test_commutative_properties(self):
        """Test commutative properties of operations"""
        # Addition is commutative
        assert add(3, 5) == add(5, 3)
        assert add(-2, 7) == add(7, -2)
        
        # Multiplication is commutative
        assert multiply(4, 6) == multiply(6, 4)
        assert multiply(-3, 8) == multiply(8, -3)
        
        # Subtraction is not commutative (verify this)
        assert subtract(5, 3) != subtract(3, 5)
        
    def test_identity_operations(self):
        """Test identity operations"""
        test_value = 42
        
        # Adding zero is identity for addition
        assert add(test_value, 0) == test_value
        assert add(0, test_value) == test_value
        
        # Subtracting zero is identity for subtraction
        assert subtract(test_value, 0) == test_value
        
        # Multiplying by one is identity for multiplication
        assert multiply(test_value, 1) == test_value
        assert multiply(1, test_value) == test_value
        
    def test_inverse_operations(self):
        """Test inverse operations"""
        test_value = 15
        
        # Addition and subtraction are inverses
        assert subtract(add(test_value, 5), 5) == test_value
        assert add(subtract(test_value, 5), 5) == test_value
        
        # Test with negative values
        assert subtract(add(test_value, -3), -3) == test_value
        assert add(subtract(test_value, -3), -3) == test_value


if __name__ == '__main__':
    pytest.main([__file__])