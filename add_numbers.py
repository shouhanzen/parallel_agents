def add_numbers(a, b):
    """
    A simple function that adds two numbers together.
    
    Args:
        a (int or float): The first number
        b (int or float): The second number
    
    Returns:
        int or float: The sum of a and b
    """
    return a + b

# Print the greeting message
print('Hello from Goose!')

# Example usage
if __name__ == "__main__":
    # Test the function with some example numbers
    result1 = add_numbers(5, 3)
    print(f"5 + 3 = {result1}")
    
    result2 = add_numbers(10.5, 2.7)
    print(f"10.5 + 2.7 = {result2}")
    
    result3 = add_numbers(-4, 9)
    print(f"-4 + 9 = {result3}")
