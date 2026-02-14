"""
hybridconductor.config - Centralized Configuration

Manages:
- Environment variables (loading .env)
- Default values
- Platform-specific paths
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Authentication and environment configuration."""
    
    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path(os.getcwd())
        self._load_env()
        
    def _load_env(self) -> None:
        """Load .env file if present."""
        env_path = self.root_dir / ".env"
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, value = line.split("=", 1)
                        # Don't overwrite existing env vars
                        if key not in os.environ:
                            os.environ[key] = value
            except Exception:
                pass  # Fallback to system env

    @property
    def offline_mode(self) -> bool:
        """Check if offline mode is forced."""
        return os.environ.get("HYBRIDCONDUCTOR_OFFLINE", "false").lower() == "true"

    @property
    def gui_renderer(self) -> Optional[str]:
        """Get preferred GUI renderer."""
        return os.environ.get("PYWEBVIEW_GUI")

    @property
    def discord_webhook(self) -> Optional[str]:
        """Get Discord webhook URL."""
        return os.environ.get("DISCORD_WEBHOOK_URL")

    @property
    def telegram_token(self) -> Optional[str]:
        """Get Telegram bot token."""
        return os.environ.get("TELEGRAM_BOT_TOKEN")

    @property
    def telegram_chat_id(self) -> Optional[str]:
        """Get Telegram chat ID."""
        return os.environ.get("TELEGRAM_CHAT_ID")

    def get_provider_config(self) -> Dict[str, Any]:
        """Get LLM provider configuration."""
        return {
            "provider": os.environ.get("LLM_PROVIDER", "gemini"),
            "api_key": os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY"),
            "model": os.environ.get("LLM_MODEL", "gemini-2.0-flash-exp"),
            "temperature": float(os.environ.get("LLM_TEMPERATURE", "0.7"))
        }

# Global instance for easy import
config = Config()
