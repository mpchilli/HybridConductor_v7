
import os
import shutil
import time
from pathlib import Path
from contextlib import contextmanager

@contextmanager
def safe_tempdir(prefix="hc_task_"):
    """Guaranteed cleanup with Windows handle release retries"""
    temp_dir = Path(os.environ.get("TEMP", "/tmp")) / f"{prefix}{os.getpid()}_{int(time.time()*1000)}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        yield temp_dir
    finally:
        _force_delete(temp_dir)

def _force_delete(path: Path, retries=5, delay=0.3):
    """Aggressive Windows-safe deletion with handle release"""
    for attempt in range(retries):
        try:
            if path.is_file():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=False)
            
            if not path.exists():
                return True
        except (PermissionError, OSError) as e:
            if attempt == retries - 1:
                print(f" Warning: Failed to delete {path} after {retries} attempts ({e})")
                # raise RuntimeError(f"Failed to delete {path} after {retries} attempts") from e
                # Don't crash for cleanup failures
                return False
            
            time.sleep(delay * (attempt + 1))  # Exponential backoff
            # Force GC to release dangling handles
            import gc
            gc.collect()
    return False
