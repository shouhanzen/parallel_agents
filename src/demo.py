def add_numbers(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b


def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers together"""
    return a * b


def divide_numbers(a: int, b: int) -> float:
    """Divide two numbers"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


class Calculator:
    """A simple calculator class"""
    
    def __init__(self):
        self.history = []
    
    def calculate(self, operation: str, a: int, b: int) -> float:
        """Perform a calculation and store in history"""
        if operation == "add":
            result = add_numbers(a, b)
        elif operation == "multiply":
            result = multiply_numbers(a, b)
        elif operation == "divide":
            result = divide_numbers(a, b)
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        self.history.append(f"{operation}({a}, {b}) = {result}")
        return result
    
    def get_history(self) -> list:
        """Get calculation history"""
        return self.history.copy()