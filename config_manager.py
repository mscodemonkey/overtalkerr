"""
Configuration file management for .env file.

Provides safe reading and writing of environment variables
while preserving comments and formatting.
"""
import os
import re
from typing import Dict, Optional
from pathlib import Path


class ConfigManager:
    """Manages reading and writing .env configuration files"""

    def __init__(self, env_file: str = ".env"):
        self.env_file = Path(env_file)
        self.env_example = Path(".env.example")

    def read_config(self) -> Dict[str, str]:
        """
        Read current configuration from .env file.

        Returns:
            Dictionary of environment variables
        """
        config = {}

        # If .env doesn't exist, try to create it from .env.example
        if not self.env_file.exists():
            if self.env_example.exists():
                self.env_file.write_text(self.env_example.read_text())
            else:
                return config

        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse KEY=VALUE
                match = re.match(r'^([A-Z_]+)=(.*)$', line)
                if match:
                    key, value = match.groups()
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    config[key] = value

        return config

    def write_config(self, config: Dict[str, str]) -> None:
        """
        Write configuration to .env file while preserving comments.

        Args:
            config: Dictionary of environment variables to write
        """
        # Read existing file to preserve comments and structure
        existing_lines = []
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                existing_lines = f.readlines()

        # Build new file content
        new_lines = []
        updated_keys = set()

        for line in existing_lines:
            stripped = line.strip()

            # Preserve comments and empty lines
            if not stripped or stripped.startswith('#'):
                new_lines.append(line)
                continue

            # Update existing KEY=VALUE lines
            match = re.match(r'^([A-Z_]+)=', stripped)
            if match:
                key = match.group(1)
                if key in config:
                    # Update with new value
                    new_lines.append(f"{key}={config[key]}\n")
                    updated_keys.add(key)
                else:
                    # Keep existing line
                    new_lines.append(line)
            else:
                # Keep any other lines
                new_lines.append(line)

        # Add any new keys that weren't in the original file
        for key, value in config.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}\n")

        # Write back to file
        with open(self.env_file, 'w') as f:
            f.writelines(new_lines)

    def test_backend_connection(self, url: str, api_key: str) -> Dict[str, any]:
        """
        Test connection to media backend.

        Args:
            url: Backend URL
            api_key: Backend API key

        Returns:
            Dictionary with success status and details
        """
        import requests

        # Try Overseerr/Jellyseerr API
        try:
            headers = {"X-Api-Key": api_key}
            response = requests.get(f"{url}/api/v1/status", headers=headers, timeout=5)

            if response.ok:
                data = response.json()
                version = data.get("version", "unknown")

                # Detect backend type
                if "jellyseerr" in version.lower():
                    backend_type = "Jellyseerr"
                else:
                    backend_type = "Overseerr"

                return {
                    "success": True,
                    "backend_type": backend_type,
                    "version": version,
                    "message": f"Version {version}"
                }
        except Exception as e:
            pass

        # Try Ombi API
        try:
            headers = {"ApiKey": api_key}
            response = requests.get(f"{url}/api/v1/Status", headers=headers, timeout=5)

            if response.ok:
                return {
                    "success": True,
                    "backend_type": "Ombi",
                    "message": "Connection successful"
                }
        except Exception as e:
            pass

        # Both failed
        return {
            "success": False,
            "error": "Could not connect to backend. Check URL and API key."
        }

    def validate_config(self, config: Dict[str, str]) -> tuple[bool, Optional[str]]:
        """
        Validate configuration values.

        Args:
            config: Configuration dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        required_fields = ['MEDIA_BACKEND_URL', 'MEDIA_BACKEND_API_KEY']

        for field in required_fields:
            if field not in config or not config[field]:
                return False, f"Missing required field: {field}"

        # Validate URL format
        backend_url = config.get('MEDIA_BACKEND_URL', '')
        if backend_url and not backend_url.startswith(('http://', 'https://')):
            return False, "MEDIA_BACKEND_URL must start with http:// or https://"

        public_url = config.get('PUBLIC_BASE_URL', '')
        if public_url and not public_url.startswith(('http://', 'https://')):
            return False, "PUBLIC_BASE_URL must start with http:// or https://"

        # Validate numeric values
        try:
            session_ttl = config.get('SESSION_TTL_HOURS', '24')
            if session_ttl and int(session_ttl) < 1:
                return False, "SESSION_TTL_HOURS must be at least 1"
        except ValueError:
            return False, "SESSION_TTL_HOURS must be a number"

        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        log_level = config.get('LOG_LEVEL', 'INFO')
        if log_level and log_level not in valid_log_levels:
            return False, f"LOG_LEVEL must be one of: {', '.join(valid_log_levels)}"

        return True, None

    def restart_service(self) -> tuple[bool, str]:
        """
        Restart the Overtalkerr service.

        Returns:
            Tuple of (success, message)
        """
        import subprocess
        import sys

        try:
            # Check if running under systemd
            is_systemd = os.path.exists('/etc/systemd/system/overtalkerr.service')

            if is_systemd:
                # Running as systemd service - use systemctl
                result = subprocess.run(
                    ['systemctl', 'restart', 'overtalkerr'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return True, "Service restart initiated"
                else:
                    return False, f"Failed to restart service: {result.stderr}"

            else:
                # Running directly (development/docker) - restart via sys.exit
                # Gunicorn/systemd will automatically restart the process
                import signal
                os.kill(os.getpid(), signal.SIGTERM)
                return True, "Restart initiated (process will be restarted by process manager)"

        except subprocess.TimeoutExpired:
            return False, "Restart command timed out"
        except PermissionError:
            return False, "Permission denied. Service may need sudo privileges."
        except Exception as e:
            return False, f"Error restarting service: {str(e)}"
