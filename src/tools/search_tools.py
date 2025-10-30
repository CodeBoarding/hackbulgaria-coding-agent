"""Search tools for the coding agent."""

from langchain_core.tools import tool
from pathlib import Path
import subprocess
import re


@tool
def grep_search(pattern: str, file_pattern: str = "*.py", case_sensitive: bool = False) -> str:
    """Search for text pattern across multiple files in the codebase.
    
    This tool performs multi-file text search starting from the home directory
    (set via --home flag). All file patterns are relative to the home directory.
    
    Useful for finding function usages, class definitions, imports, TODO comments,
    and other code patterns.
    
    Args:
        pattern: Text or regex pattern to search for
        file_pattern: File glob pattern to search in (e.g., "*.py", "**/*.py", "src/**/*.py")
                     Patterns are relative to home directory
        case_sensitive: Whether the search should be case-sensitive (default: False)
        
    Returns:
        Formatted search results with file paths, line numbers, and matching lines
        
    Examples:
        grep_search("def calculate", "*.py") - Find all function definitions
        grep_search("TODO", "**/*.py") - Find all TODO comments recursively
        grep_search("import requests", "src/**/*.py") - Find imports in src/
    """
    try:
        # Import the global variable at runtime to ensure we get the current value
        from src.tools.file_tools import _home_directory as home_dir
        
        # Set working directory to home directory if set
        cwd = home_dir if home_dir else Path.cwd()
        
        # Try using grep (faster if available)
        try:
            # Build grep command
            cmd = ["grep", "-n", "-r"]  # -n: line numbers, -r: recursive
            
            if not case_sensitive:
                cmd.append("-i")  # case insensitive
            
            cmd.extend([pattern, "--include", file_pattern])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(cwd)
            )
            
            # grep returns 1 if no matches found (not an error)
            if result.returncode == 0:
                output = result.stdout
            elif result.returncode == 1:
                return f"No matches found for pattern '{pattern}' in files matching '{file_pattern}'"
            else:
                # Fall back to Python implementation
                raise Exception("grep failed, using Python fallback")
        
        except (FileNotFoundError, Exception):
            # Fallback to Python-based search if grep not available
            output = _python_grep_search(pattern, file_pattern, case_sensitive, cwd)
        
        if not output or not output.strip():
            return f"No matches found for pattern '{pattern}' in files matching '{file_pattern}'"
        
        # Parse and format results
        lines = output.strip().split('\n')
        
        # Group by file
        results_by_file = {}
        for line in lines:
            if ':' in line:
                # Format: filepath:line_number:content
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    filepath = parts[0]
                    line_num = parts[1]
                    content = parts[2].strip()
                    
                    if filepath not in results_by_file:
                        results_by_file[filepath] = []
                    results_by_file[filepath].append((line_num, content))
        
        # Format output
        result_lines = [f"Search results for '{pattern}' in '{file_pattern}':", ""]
        total_matches = 0
        
        for filepath, matches in sorted(results_by_file.items()):
            result_lines.append(f"{filepath} ({len(matches)} matches):")
            for line_num, content in matches[:10]:  # Limit to first 10 per file
                result_lines.append(f"  Line {line_num}: {content}")
                total_matches += 1
            
            if len(matches) > 10:
                result_lines.append(f"  ... and {len(matches) - 10} more matches")
            result_lines.append("")
        
        result_lines.append(f"Total: {total_matches} matches in {len(results_by_file)} files")
        
        # Limit overall output size
        output_str = '\n'.join(result_lines)
        max_output = 8000
        if len(output_str) > max_output:
            output_str = output_str[:max_output] + f"\n\n... (results truncated, showing first {max_output} characters)"
        
        return output_str
    
    except subprocess.TimeoutExpired:
        return "Error: Search timed out after 30 seconds"
    except Exception as e:
        return f"Error performing search: {str(e)}"


def _python_grep_search(pattern: str, file_pattern: str, case_sensitive: bool, cwd: Path) -> str:
    """Python-based fallback for grep search."""
    import fnmatch
    
    # Compile regex pattern
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags)
    except re.error:
        # If pattern is not valid regex, treat as literal string
        regex = re.compile(re.escape(pattern), flags)
    
    results = []
    
    # Convert glob pattern to search recursively if it contains **
    if '**' in file_pattern:
        # Recursive search
        glob_pattern = file_pattern.replace('**/', '')
        search_recursive = True
    else:
        glob_pattern = file_pattern
        search_recursive = False
    
    # Search files
    if search_recursive:
        # Search all subdirectories
        for file_path in cwd.rglob(glob_pattern):
            if file_path.is_file():
                _search_file(file_path, regex, results, cwd)
    else:
        # Search current directory only
        for file_path in cwd.glob(glob_pattern):
            if file_path.is_file():
                _search_file(file_path, regex, results, cwd)
    
    return '\n'.join(results)


def _search_file(file_path: Path, regex: re.Pattern, results: list, base_path: Path):
    """Search a single file for pattern matches."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if regex.search(line):
                    # Make path relative to base_path
                    rel_path = file_path.relative_to(base_path)
                    results.append(f"{rel_path}:{line_num}:{line.rstrip()}")
    except Exception:
        # Skip files that can't be read
        pass
