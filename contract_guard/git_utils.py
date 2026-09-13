"""
Git revision utilities for extracting base specifications from repository history.
"""

import subprocess
from typing import Optional


def get_file_content_from_git(ref: str, file_path: str) -> Optional[str]:
    cmd = ["git", "show", f"{ref}:{file_path}"]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            encoding="utf-8",
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None
