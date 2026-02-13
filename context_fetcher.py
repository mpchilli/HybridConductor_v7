#!/usr/bin/env python3
"""
context_fetcher.py - Semantic Context Retrieval

WHY THIS SCRIPT EXISTS:
- Provides primary context retrieval via Openground semantic search
- Falls back to regex scanning if Openground unavailable
- Satisfies Windows-native requirement with zero WSL dependencies
- Enables efficient context loading for LLM agents

KEY ARCHITECTURAL DECISIONS:
- OPENGROUND PRIMARY: Semantic search provides better relevance than regex
- REGEX FALLBACK: Ensures resilience if Openground fails to install
- WINDOWS-NATIVE: Both methods work without WSL/Docker
- OFFLINE-CAPABLE: Functions completely offline once indexed

WINDOWS-SPECIFIC CONSIDERATIONS:
- Openground installs to user-space via pip (no admin rights)
- LanceDB embedded engine stores data directly to NTFS
- All file operations use pathlib with Windows semantics
- Subprocess calls use shell=False + CREATE_NO_WINDOW
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List

def fetch_context(query: str) -> str:
    """
    Primary context retrieval using Openground semantic search.
    Fallback to regex scanning if Openground unavailable.
    """
    try:
        # Primary: Semantic search via Openground
        result = subprocess.run(
            ["openground", "search", query],
            capture_output=True,
            text=True,
            shell=False,  # Critical: Prevents shell injection
            timeout=10,   # Prevent hanging on large repos
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW  # Windows-specific
        )
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Log the failure but continue with fallback
        print(f"⚠️  Openground failed for query: {query}. Using regex fallback.")
        return _regex_fallback_search(query)

def _regex_fallback_search(query: str) -> str:
    """
    Fallback context retrieval using naive regex scanning.
    """
    results = []
    query_lower = query.lower()
    
    # Scan project files for relevant content
    for root, _, files in os.walk(Path.cwd()):
        for file in files:
            if _is_relevant_file(file):
                file_path = Path(root) / file
                try:
                    content = file_path.read_text(encoding="utf-8-sig")
                    if query_lower in content.lower():
                        results.append(f"--- FILE: {file_path.as_posix()} ---\n{content}\n")
                except (UnicodeDecodeError, PermissionError):
                    # Skip binary or locked files
                    continue
    
    return "\n".join(results[:5])  # Return top 5 matches

def _is_relevant_file(filename: str) -> bool:
    """
    Determine if file is relevant for context retrieval.
    """
    relevant_extensions = {".py", ".js", ".ts", ".md", ".txt", ".json", ".yaml", ".yml"}
    return any(filename.endswith(ext) for ext in relevant_extensions)

# Test function
if __name__ == "__main__":
    context = fetch_context("authentication middleware")
    print(f"Retrieved context:\n{context[:200]}...")
