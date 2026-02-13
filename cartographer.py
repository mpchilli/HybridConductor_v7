#!/usr/bin/env python3
"""
cartographer.py - L0 Codebase Mapping

WHY THIS SCRIPT EXISTS:
- Generates architectural map of codebase using codesum
- Provides L0 structural awareness for LLM agents
- Falls back to custom file walker if codesum unavailable
- Enables context-aware code generation from the start

KEY ARCHITECTURAL DECISIONS:
- CODESUM PRIMARY: Professional AST-based codebase analysis
- CUSTOM FALLBACK: Basic file structure if codesum unavailable
- WINDOWS-NATIVE: Both methods work without WSL/Docker
- PERSISTENT ARTIFACT: codebase_map.md stored in state directory

WINDOWS-SPECIFIC CONSIDERATIONS:
- codesum installed to user-space via setup.py
- All paths use pathlib with Windows semantics
- Subprocess calls use shell=False + CREATE_NO_WINDOW
- File operations use UTF-8+BOM encoding
"""

import os
import subprocess
from pathlib import Path

def generate_codebase_map(project_root: Path) -> None:
    """
    Generate L0 codebase map using codesum or fallback.
    """
    try:
        # Primary: Use codesum for professional AST-based analysis
        result = subprocess.run(
            ["codesum", str(project_root)],
            capture_output=True,
            text=True,
            shell=False,
            timeout=60,  # 60s timeout for large repos
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # Save to state directory
        map_path = project_root / "state" / "codebase_map.md"
        with open(map_path, "w", encoding="utf-8-sig") as f:
            f.write(result.stdout)
        
        print(f"🗺️  Codebase map generated: {map_path}")
        
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: Generate basic file structure
        print("⚠️  codesum unavailable. Generating basic file structure.")
        _generate_basic_map(project_root)

def _generate_basic_map(project_root: Path) -> None:
    """
    Generate basic file structure as fallback.
    """
    structure = ["# Codebase Structure\n\n"]
    
    def _walk_directory(current_path: Path, depth: int = 0) -> None:
        """Recursively walk directory and build structure."""
        indent = "  " * depth
        structure.append(f"{indent}- {current_path.name}/\n")
        
        # Limit depth to prevent excessive output
        if depth >= 3:
            return
            
        try:
            for item in sorted(current_path.iterdir()):
                if item.is_dir() and not item.name.startswith((".", "__")):
                    _walk_directory(item, depth + 1)
                elif item.is_file():
                    structure.append(f"{indent}  - {item.name}\n")
        except PermissionError:
            structure.append(f"{indent}  - [ACCESS DENIED]\n")
    
    _walk_directory(project_root)
    
    # Save to state directory
    map_path = project_root / "state" / "codebase_map.md"
    map_path.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
    with open(map_path, "w", encoding="utf-8-sig") as f:
        f.write("".join(structure))
    
    print(f"🗺️  Basic codebase map generated: {map_path}")

# Test function
if __name__ == "__main__":
    generate_codebase_map(Path.cwd())
