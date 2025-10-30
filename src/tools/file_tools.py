"""File manipulation tools for the coding agent."""

from langchain_core.tools import tool
from pathlib import Path
from typing import Optional


# Global home directory for the agent
_home_directory: Optional[Path] = None


def set_home_directory(home_dir: str) -> None:
    """Set the home directory for file operations."""
    global _home_directory
    _home_directory = Path(home_dir).resolve()


def _resolve_path(file_path: str) -> Path:
    """Resolve a file path relative to home directory if set."""
    path = Path(file_path)
    
    # If home directory is set and path is not absolute, make it relative to home
    if _home_directory and not path.is_absolute():
        path = _home_directory / path
    
    return path.resolve()


@tool
def read_file(file_path: str) -> str:
    """Read content from a file with line numbers.
    
    File paths are resolved relative to the home directory (set via --home flag).
    Absolute paths are also supported.
    
    Args:
        file_path: Path to the file to read (relative to home directory if set)
        
    Returns:
        File content with line numbers, or error message
    """
    try:
        path = _resolve_path(file_path)
        if not path.exists():
            return f"Error: File '{file_path}' not found"
        
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Add line numbers
        numbered_lines = [f"{i+1}: {line}" for i, line in enumerate(lines)]
        return ''.join(numbered_lines)
    
    except PermissionError:
        return f"Error: Permission denied reading '{file_path}'"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_file(file_path: str, content: str, start_line: int = 1, end_line: int = -1) -> str:
    """Write content to a file at specified line range.
    
    File paths are resolved relative to the home directory (set via --home flag).
    Absolute paths are also supported. Directories are created automatically if needed.
    
    Args:
        file_path: Path to the file to write (relative to home directory if set)
        content: New content to write
        start_line: Starting line number (1-indexed, default: 1)
        end_line: Ending line number (1-indexed, default: -1 means end of file)
        
    Returns:
        Success confirmation or error message
    """
    try:
        path = _resolve_path(file_path)
        
        # Create directory if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing content if file exists
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Adjust indices (convert from 1-indexed to 0-indexed)
        start_idx = start_line - 1
        end_idx = len(lines) if end_line == -1 else end_line
        
        # Split new content into lines
        new_lines = content.splitlines(keepends=True)
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines[-1] += '\n'
        
        # Replace the specified range
        lines[start_idx:end_idx] = new_lines
        
        # Write back to file
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return f"Successfully wrote to '{file_path}' (lines {start_line}-{end_idx})"
    
    except PermissionError:
        return f"Error: Permission denied writing to '{file_path}'"
    except Exception as e:
        return f"Error writing file: {str(e)}"
