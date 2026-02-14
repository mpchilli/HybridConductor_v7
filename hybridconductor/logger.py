"""
hybridconductor.logger - Centralized Logging Infrastructure

Unifies logging across orchestrator and worker with:
- Console output (INFO+)
- File rotation (DEBUG+)
- SQLite database logging for AI conversation tracking
"""

import logging
import sqlite3
import time
from pathlib import Path
from typing import Optional

def setup_logging(name: str = "hybrid_conductor", log_dir: Optional[Path] = None, debug: bool = False) -> logging.Logger:
    """
    Configure standardized logging.
    
    Args:
        name: Logger name
        log_dir: Directory to store log files (optional)
        debug: Enable debug level logging
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File Handler (if log_dir provided)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / f"{name}.log", encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
    return logger

def log_ai_conversation(role: str, message: str, db_path: Path) -> None:
    """
    Log AI interaction to SQLite database.
    
    Args:
        role: Sender role (USER, AI, SYSTEM)
        message: Content message
        db_path: Path to sqlite database file
    """
    try:
        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use context manager for safe connection handling
        with sqlite3.connect(f"file:{db_path}?mode=rwc", uri=True) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_conversation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            """)
            conn.execute(
                "INSERT INTO ai_conversation (role, message) VALUES (?, ?)",
                (role, message)
            )
            conn.commit()
    except Exception as e:
        # Fallback to standard logging if DB fails
        logging.getLogger("hybrid_conductor.db").error(f"Failed to log conversation: {e}")
