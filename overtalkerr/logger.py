"""
Centralized logging configuration for the application.
"""
import os
import sys
import logging
from pythonjsonlogger import jsonlogger

# Determine log level from environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json or text


def setup_logger(name: str = "overtalkerr") -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        name: Logger name (default: overtalkerr)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Configure formatter based on LOG_FORMAT
    if LOG_FORMAT == "json":
        # JSON formatter for production (better for log aggregation)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Human-readable formatter for development
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# Create default logger instance
logger = setup_logger()


# Utility functions for common logging patterns
def log_request(endpoint: str, user_id: str = None, **kwargs):
    """Log an incoming request"""
    logger.info(f"Request to {endpoint}", extra={
        "endpoint": endpoint,
        "user_id": user_id,
        **kwargs
    })


def log_error(message: str, exc: Exception = None, **kwargs):
    """Log an error with optional exception details"""
    extra = kwargs.copy()
    if exc:
        extra["error_type"] = type(exc).__name__
        extra["error_message"] = str(exc)
    logger.error(message, extra=extra, exc_info=exc is not None)


def log_overseerr_call(action: str, success: bool, **kwargs):
    """Log Overseerr API calls"""
    level = logging.INFO if success else logging.WARNING
    logger.log(level, f"Overseerr {action}", extra={
        "action": action,
        "success": success,
        **kwargs
    })
