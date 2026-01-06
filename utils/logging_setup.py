"""
Centralized Logging Setup for CleanSheet
Provides file and console logging with rotation and platform-specific paths
"""

import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import platform


def get_log_directory() -> Path:
    """
    Get platform-specific log directory

    Returns:
        Path to logs directory (creates if doesn't exist)
    """
    system = platform.system()

    if system == "Windows":
        # Windows: %APPDATA%/CleanSheet/logs
        appdata = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        log_dir = appdata / 'CleanSheet' / 'logs'
    else:
        # Linux/macOS: ~/.config/CleanSheet/logs
        config_home = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
        log_dir = config_home / 'CleanSheet' / 'logs'

    # Create directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logging(app_name: str = "CleanSheet", version: str = None) -> Path:
    """
    Setup centralized logging with file rotation and console output

    Args:
        app_name: Name of the application
        version: Application version string

    Returns:
        Path to log directory
    """

    # Get log directory
    log_dir = get_log_directory()
    log_file = log_dir / 'cleansheet.log'

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # File handler with rotation (2MB max, 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=2_000_000,  # 2MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)

    # Console handler (for development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Log startup banner
    logger = logging.getLogger(__name__)
    logger.info("=" * 70)
    logger.info(f"{app_name} - Logging Initialized")
    if version:
        logger.info(f"Version: {version}")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info(f"Python: {sys.version.split()[0]}")

    # Log pandas version
    try:
        import pandas as pd
        logger.info(f"Pandas: {pd.__version__}")
    except ImportError:
        logger.warning("Pandas not available")

    logger.info(f"Log file: {log_file}")
    logger.info("=" * 70)

    return log_dir


def get_recent_logs(num_lines: int = 50) -> str:
    """
    Get the last N lines from the log file

    Args:
        num_lines: Number of lines to retrieve from end of log

    Returns:
        String containing recent log lines
    """
    log_dir = get_log_directory()
    log_file = log_dir / 'cleansheet.log'

    if not log_file.exists():
        return "No log file found"

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent = lines[-num_lines:] if len(lines) > num_lines else lines
            return ''.join(recent)
    except Exception as e:
        return f"Error reading log file: {e}"


def get_debug_info(version: str = None) -> str:
    """
    Get comprehensive debug information for troubleshooting

    Args:
        version: Application version string

    Returns:
        Formatted debug information string
    """
    import pandas as pd

    log_dir = get_log_directory()

    info = []
    info.append("=" * 70)
    info.append("CleanSheet Debug Information")
    info.append("=" * 70)

    if version:
        info.append(f"Version: {version}")

    info.append(f"Platform: {platform.system()} {platform.release()}")
    info.append(f"Python: {sys.version}")
    info.append(f"Pandas: {pd.__version__}")
    info.append(f"Log Directory: {log_dir}")
    info.append("")
    info.append("Recent Logs (last 50 lines):")
    info.append("-" * 70)
    info.append(get_recent_logs(50))

    return '\n'.join(info)
