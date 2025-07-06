# UserAuth API Documentation

## Overview

The `UserAuth` class provides a simple user authentication system with user registration and authentication capabilities. This class is designed for basic authentication needs and stores user credentials in memory.

## Class: UserAuth

### Constructor

```python
def __init__(self):
```

Initializes a new UserAuth instance with an empty users dictionary.

**Parameters:** None

**Returns:** None

### Methods

#### register_user(username, password)

Registers a new user with the provided username and password.

**Parameters:**
- `username` (str): The username for the new user
- `password` (str): The password for the new user

**Returns:**
- `bool`: Returns `True` if registration is successful

**Raises:**
- `ValueError`: If the username already exists in the system

**Example:**
```python
auth = UserAuth()
auth.register_user("john_doe", "secure_password")
```

#### authenticate(username, password)

Authenticates a user with the provided credentials.

**Parameters:**
- `username` (str): The username to authenticate
- `password` (str): The password to verify

**Returns:**
- `bool`: Returns `True` if authentication is successful, `False` otherwise

**Example:**
```python
auth = UserAuth()
auth.register_user("john_doe", "secure_password")
is_authenticated = auth.authenticate("john_doe", "secure_password")  # Returns True
```

#### get_user_count()

Returns the total number of registered users.

**Parameters:** None

**Returns:**
- `int`: The number of registered users

**Example:**
```python
auth = UserAuth()
auth.register_user("user1", "password1")
auth.register_user("user2", "password2")
count = auth.get_user_count()  # Returns 2
```

## Security Considerations

**⚠️ Important Security Notice:**

This implementation is for demonstration purposes only and should not be used in production environments without proper security enhancements:

1. **Password Storage**: Passwords are stored in plain text. In production, use proper password hashing (e.g., bcrypt, scrypt, or argon2).
2. **Memory Storage**: User data is stored in memory and will be lost when the application restarts.
3. **Input Validation**: No input validation is performed on usernames or passwords.
4. **Rate Limiting**: No protection against brute force attacks.

## File Location

- **Source File**: `src/auth.py`
- **Lines**: 2-19

## Version Information

- **Last Modified**: Based on detected changes in `/tmp/tmpzmxjpe9o/src/auth.py`
- **Documentation Generated**: 2025-07-05