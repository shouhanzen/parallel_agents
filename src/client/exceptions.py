"""
Exception classes for the Parallel Agents client
"""


class ClientError(Exception):
    """Base exception for client-side errors"""
    pass


class ServerError(ClientError):
    """Exception for server-side errors"""
    pass


class AgentNotFoundError(ClientError):
    """Exception for when an agent is not found"""
    pass


class ConfigurationError(ClientError):
    """Exception for configuration-related errors"""
    pass


class ConnectionError(ClientError):
    """Exception for connection-related errors"""
    pass


class TimeoutError(ClientError):
    """Exception for timeout-related errors"""
    pass 