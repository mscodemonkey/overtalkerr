"""
Configuration and environment variable validation.
"""
import os
import sys
from typing import Optional
from dotenv import load_dotenv
from logger import logger

# Load environment variables
load_dotenv()


class ConfigError(Exception):
    """Raised when configuration is invalid or missing"""
    pass


class Config:
    """Application configuration with validation"""

    # Flask
    SECRET_KEY: str
    FLASK_ENV: str
    PUBLIC_BASE_URL: Optional[str]

    # Media Backend (supports Overseerr, Jellyseerr, Ombi)
    MEDIA_BACKEND_URL: str
    MEDIA_BACKEND_API_KEY: str
    MOCK_BACKEND: bool

    # Database
    DATABASE_URL: str
    SESSION_TTL_HOURS: int

    # Authentication
    BASIC_AUTH_USER: Optional[str]
    BASIC_AUTH_PASS: Optional[str]

    # Logging
    LOG_LEVEL: str
    LOG_FORMAT: str

    @classmethod
    def load(cls) -> None:
        """Load and validate all configuration"""
        cls.FLASK_ENV = os.getenv("FLASK_ENV", "production")
        cls.SECRET_KEY = cls._get_required("SECRET_KEY", warn_on_default=True)
        cls.PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")

        # Media Backend configuration
        cls.MOCK_BACKEND = os.getenv("MOCK_BACKEND", "false").lower() in {"1", "true", "yes", "on"}

        if cls.MOCK_BACKEND:
            logger.warning("Running in MOCK mode - no real backend API calls will be made")
            cls.MEDIA_BACKEND_URL = os.getenv("MEDIA_BACKEND_URL", "http://localhost:5055")
            cls.MEDIA_BACKEND_API_KEY = os.getenv("MEDIA_BACKEND_API_KEY", "mock-key")
        else:
            cls.MEDIA_BACKEND_URL = cls._get_required("MEDIA_BACKEND_URL")
            cls.MEDIA_BACKEND_API_KEY = cls._get_required("MEDIA_BACKEND_API_KEY")

        # Database
        cls.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./overtalkerr.db")
        cls.SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "24"))

        # Authentication
        cls.BASIC_AUTH_USER = os.getenv("BASIC_AUTH_USER")
        cls.BASIC_AUTH_PASS = os.getenv("BASIC_AUTH_PASS")

        # Logging
        cls.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        cls.LOG_FORMAT = os.getenv("LOG_FORMAT", "json")

        # Validate configuration
        cls._validate()

        logger.info("Configuration loaded successfully", extra={
            "flask_env": cls.FLASK_ENV,
            "mock_mode": cls.MOCK_BACKEND,
            "database": cls.DATABASE_URL.split("://")[0],  # Just show db type
            "session_ttl_hours": cls.SESSION_TTL_HOURS,
        })

    @classmethod
    def _get_required(cls, key: str, warn_on_default: bool = False) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if not value:
            if key == "SECRET_KEY" and warn_on_default:
                # Allow missing SECRET_KEY in development, but warn
                if cls.FLASK_ENV != "production":
                    logger.warning(f"{key} not set - using insecure default for development")
                    return "dev-secret-change-in-production"
            raise ConfigError(f"Required environment variable {key} is not set")
        return value

    @classmethod
    def _validate(cls) -> None:
        """Validate configuration values"""
        # Validate URLs
        if cls.PUBLIC_BASE_URL:
            if cls.FLASK_ENV == "production" and not cls.PUBLIC_BASE_URL.startswith("https://"):
                logger.warning("PUBLIC_BASE_URL should use HTTPS in production")

        if not cls.MOCK_BACKEND:
            if not cls.MEDIA_BACKEND_URL.startswith(("http://", "https://")):
                raise ConfigError("MEDIA_BACKEND_URL must start with http:// or https://")

        # Validate TTL
        if cls.SESSION_TTL_HOURS < 1:
            raise ConfigError("SESSION_TTL_HOURS must be at least 1")

        # Validate log level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if cls.LOG_LEVEL not in valid_levels:
            logger.warning(f"Invalid LOG_LEVEL '{cls.LOG_LEVEL}', defaulting to INFO")
            cls.LOG_LEVEL = "INFO"

    @classmethod
    def check_connectivity(cls) -> bool:
        """
        Check connectivity to media backend (if not in mock mode).

        Returns:
            True if connection successful, False otherwise
        """
        if cls.MOCK_BACKEND:
            logger.info("Skipping connectivity check (mock mode)")
            return True

        try:
            import requests
            url = f"{cls.MEDIA_BACKEND_URL}/api/v1/status"
            headers = {"X-Api-Key": cls.MEDIA_BACKEND_API_KEY}
            response = requests.get(url, headers=headers, timeout=5)

            if response.ok:
                logger.info("Media backend connectivity check passed", extra={
                    "url": cls.MEDIA_BACKEND_URL,
                    "status": response.status_code
                })
                return True
            else:
                logger.error("Media backend connectivity check failed", extra={
                    "url": cls.MEDIA_BACKEND_URL,
                    "status": response.status_code
                })
                return False
        except Exception as e:
            logger.error("Failed to connect to media backend", extra={
                "url": cls.MEDIA_BACKEND_URL,
                "error": str(e)
            })
            return False


# Load configuration on module import
try:
    Config.load()
except ConfigError as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(1)
