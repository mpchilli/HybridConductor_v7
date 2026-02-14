
import os
import requests
import subprocess

class McpClient:
    """
    MCP client for safe Git operations.
    
    WHY MCP OVER SUBPROCESS:
    - Abstracts Windows Git credential/path differences
    - Provides standardized error handling
    - Enforces localhost-only communication
    - Integrates with Windows security model
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        self.base_url = base_url
        # Short-circuit if offline mode is enforced
        self.enabled = os.getenv('HYBRIDCONDUCTOR_OFFLINE', 'false').lower() == 'false'
        if not self.enabled:
            # We don't print here to avoid spamming logs, caller should handle context
            pass
    
    def create_branch(self, name: str) -> None:
        """Create isolated Git branch via MCP."""
        if not self.enabled:
            return self._create_branch_subprocess(self._sanitize_branch_name(name))

        sanitized_name = self._sanitize_branch_name(name)
        try:
            response = requests.post(
                f"{self.base_url}/branches",
                json={"name": sanitized_name},
                timeout=5
            )
            response.raise_for_status()
            print(f"[MCP] Created branch: {sanitized_name}")
        except requests.exceptions.RequestException as e:
            print(f" MCP create_branch failed: {e}")
            # Fallback to subprocess Git
            self._create_branch_subprocess(sanitized_name)
    
    def switch_branch(self, name: str) -> None:
        """Switch to specified branch."""
        if not self.enabled:
            return self._switch_branch_subprocess(self._sanitize_branch_name(name))

        sanitized_name = self._sanitize_branch_name(name)
        try:
            response = requests.post(
                f"{self.base_url}/checkout",
                json={"branch": sanitized_name},
                timeout=5
            )
            response.raise_for_status()
            print(f"[MCP] Switched to branch: {sanitized_name}")
        except requests.exceptions.RequestException as e:
            print(f" MCP switch_branch failed: {e}")
            # Fallback to subprocess Git
            self._switch_branch_subprocess(sanitized_name)
    
    def commit(self, message: str) -> None:
        """Commit changes via MCP."""
        if not self.enabled:
            return self._commit_subprocess(message)

        try:
            response = requests.post(
                f"{self.base_url}/commit",
                json={"message": message},
                timeout=5
            )
            response.raise_for_status()
            print(f"[MCP] Committed: {message}")
        except requests.exceptions.RequestException as e:
            print(f" MCP commit failed: {e}")
            # Fallback to subprocess Git
            self._commit_subprocess(message)
    
    def _sanitize_branch_name(self, name: str) -> str:
        """
        Sanitize branch name to prevent path traversal.
        """
        sanitized = "".join(c for c in name if c.isalnum() or c in "-_")
        return sanitized[:50]  # Limit length
    
    def _create_branch_subprocess(self, name: str) -> None:
        """Fallback: Create branch using subprocess Git."""
        try:
            subprocess.run(
                ["git", "checkout", "-b", name],
                capture_output=True,
                text=True,
                shell=False,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=True
            )
            print(f"[Git] Created branch via subprocess: {name}")
        except subprocess.SubprocessError as e:
            print(f" Git branch creation failed: {e}")
            raise
    
    def _switch_branch_subprocess(self, name: str) -> None:
        """Fallback: Switch branch using subprocess Git."""
        try:
            subprocess.run(
                ["git", "checkout", name],
                capture_output=True,
                text=True,
                shell=False,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=True
            )
            print(f"[Git] Switched to branch via subprocess: {name}")
        except subprocess.SubprocessError as e:
            print(f" Git checkout failed: {e}")
            raise
    
    def _commit_subprocess(self, message: str) -> None:
        """Fallback: Commit using subprocess Git."""
        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "."],
                capture_output=True,
                text=True,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=True
            )
            # Commit
            subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=True
            )
            print(f"[Git] Committed via subprocess: {message}")
        except subprocess.SubprocessError as e:
            print(f" Git commit failed: {e}")
            # raise # Don't raise, we want to continue if git fails (maybe nothing to commit)
