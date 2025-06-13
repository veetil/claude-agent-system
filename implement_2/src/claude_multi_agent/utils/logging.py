"""Logging configuration for Claude Multi-Agent System"""

import logging
import sys
from pathlib import Path
from typing import Optional

from ..core.constants import DEFAULT_LOG_LEVEL, DEFAULT_LOG_FORMAT


def setup_logging(
    level: str = DEFAULT_LOG_LEVEL,
    log_file: Optional[Path] = None,
    format_str: Optional[str] = None
) -> None:
    """Configure logging for the entire application
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file to write logs to
        format_str: Optional custom format string
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Use provided format or default
    format_string = format_str or DEFAULT_LOG_FORMAT
    
    # Create handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format=format_string,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Set specific logger levels to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={level}, file={log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)