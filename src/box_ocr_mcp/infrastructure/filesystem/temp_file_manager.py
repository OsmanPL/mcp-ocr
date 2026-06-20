"""Temporary file management for infrastructure adapters."""

from pathlib import Path
from tempfile import NamedTemporaryFile


class TempFileManager:
    """Create temporary files for processed images."""

    def create_temp_path(self, suffix: str = ".png") -> str:
        """Create a temporary path and return it as a string."""
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            return str(Path(temp_file.name))
