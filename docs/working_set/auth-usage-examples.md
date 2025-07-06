# UserAuth Usage Examples

## Basic Usage

### Creating an Authentication System

```python
from src.auth import UserAuth

# Initialize the authentication system
auth = UserAuth()
```

### User Registration

```python
# Register a new user
try:
    auth.register_user("alice", "password123")
    print("User registered successfully!")
except ValueError as e:
    print(f"Registration failed: {e}")

# Attempting to register the same user again
try:
    auth.register_user("alice", "different_password")
except ValueError as e:
    print(f"Registration failed: {e}")  # Output: Registration failed: User already exists
```

### User Authentication

```python
# Authenticate existing user
if auth.authenticate("alice", "password123"):
    print("Authentication successful!")
else:
    print("Authentication failed!")

# Authenticate with wrong password
if auth.authenticate("alice", "wrong_password"):
    print("Authentication successful!")
else:
    print("Authentication failed!")  # This will be printed

# Authenticate non-existent user
if auth.authenticate("bob", "any_password"):
    print("Authentication successful!")
else:
    print("Authentication failed!")  # This will be printed
```

### Getting User Count

```python
# Check number of registered users
print(f"Total users: {auth.get_user_count()}")

# Register more users
auth.register_user("bob", "bob_password")
auth.register_user("charlie", "charlie_password")

print(f"Total users: {auth.get_user_count()}")  # Output: Total users: 3
```

## Complete Example

```python
from src.auth import UserAuth

def main():
    # Initialize authentication system
    auth = UserAuth()
    
    # Register multiple users
    users_to_register = [
        ("admin", "admin_password"),
        ("user1", "user1_password"),
        ("user2", "user2_password")
    ]
    
    for username, password in users_to_register:
        try:
            auth.register_user(username, password)
            print(f"✓ Registered user: {username}")
        except ValueError as e:
            print(f"✗ Failed to register {username}: {e}")
    
    # Display user count
    print(f"\nTotal registered users: {auth.get_user_count()}")
    
    # Test authentication
    test_credentials = [
        ("admin", "admin_password"),     # Valid
        ("user1", "wrong_password"),     # Invalid password
        ("nonexistent", "any_password"), # User doesn't exist
        ("user2", "user2_password")      # Valid
    ]
    
    print("\nAuthentication tests:")
    for username, password in test_credentials:
        if auth.authenticate(username, password):
            print(f"✓ {username}: Authentication successful")
        else:
            print(f"✗ {username}: Authentication failed")

if __name__ == "__main__":
    main()
```

## Error Handling

```python
from src.auth import UserAuth

auth = UserAuth()

# Handle registration errors
def safe_register(username, password):
    try:
        result = auth.register_user(username, password)
        return {"success": True, "message": f"User {username} registered successfully"}
    except ValueError as e:
        return {"success": False, "message": str(e)}

# Handle authentication with logging
def safe_authenticate(username, password):
    result = auth.authenticate(username, password)
    if result:
        print(f"User {username} authenticated successfully")
    else:
        print(f"Authentication failed for user {username}")
    return result

# Example usage
registration_result = safe_register("test_user", "test_password")
print(registration_result)

auth_result = safe_authenticate("test_user", "test_password")
```

## Integration Example

```python
from src.auth import UserAuth

class SimpleApp:
    def __init__(self):
        self.auth = UserAuth()
        self.current_user = None
    
    def register(self, username, password):
        try:
            self.auth.register_user(username, password)
            return {"status": "success", "message": "Registration successful"}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
    
    def login(self, username, password):
        if self.auth.authenticate(username, password):
            self.current_user = username
            return {"status": "success", "message": f"Welcome, {username}!"}
        else:
            return {"status": "error", "message": "Invalid credentials"}
    
    def logout(self):
        if self.current_user:
            user = self.current_user
            self.current_user = None
            return {"status": "success", "message": f"Goodbye, {user}!"}
        else:
            return {"status": "error", "message": "No user logged in"}
    
    def get_stats(self):
        return {
            "total_users": self.auth.get_user_count(),
            "current_user": self.current_user,
            "logged_in": self.current_user is not None
        }

# Example usage
app = SimpleApp()
print(app.register("alice", "password123"))
print(app.login("alice", "password123"))
print(app.get_stats())
print(app.logout())
```