"""Git operation tools for the coding agent."""

from langchain_core.tools import tool
import subprocess
from src.tools.file_tools import _home_directory


@tool
def git_diff(file_path: str = "") -> str:
    """Show git diff of changes made to files.
    
    This tool shows what changes have been made to files in the working directory
    compared to the last commit. Operates in the home directory (set via --home flag).
    
    Args:
        file_path: Optional specific file to diff (empty string = all changes)
                  Path should be relative to the home directory
        
    Returns:
        Git diff output showing additions, deletions, and modifications
    """
    try:
        # Import the global variable at runtime to ensure we get the current value
        from src.tools.file_tools import _home_directory as home_dir
        
        # Set working directory to home directory if set
        cwd = str(home_dir) if home_dir else None
        
        # Build git diff command
        cmd = ["git", "diff"]
        if file_path:
            cmd.append(file_path)
        
        # Run git diff
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd
        )
        
        if result.returncode != 0:
            # Check if it's not a git repository
            if "not a git repository" in result.stderr.lower():
                return "Error: Not a git repository. Initialize git with 'git init' first."
            return f"Error running git diff: {result.stderr}"
        
        output = result.stdout
        
        if not output.strip():
            return "No changes detected (working directory is clean)"
        
        # Limit output size
        max_output = 10000
        if len(output) > max_output:
            output = output[:max_output] + f"\n\n... (diff truncated, showing first {max_output} characters)"
        
        return output
    
    except subprocess.TimeoutExpired:
        return "Error: Git diff command timed out after 30 seconds"
    except FileNotFoundError:
        return "Error: Git is not installed or not in PATH"
    except Exception as e:
        return f"Error running git diff: {str(e)}"


@tool
def git_status() -> str:
    """Show git status of the working directory.
    
    This tool shows which files have been modified, created, deleted, or are untracked
    in the home directory (set via --home flag). Useful for understanding what changes
    exist in the working directory.
    
    Returns:
        Git status output listing modified, staged, and untracked files
    """
    try:
        # Import the global variable at runtime to ensure we get the current value
        from src.tools.file_tools import _home_directory as home_dir
        
        # Set working directory to home directory if set
        cwd = str(home_dir) if home_dir else None
        
        # Run git status
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd
        )
        
        if result.returncode != 0:
            # Check if it's not a git repository
            if "not a git repository" in result.stderr.lower():
                return "Error: Not a git repository. Initialize git with 'git init' first."
            return f"Error running git status: {result.stderr}"
        
        output = result.stdout
        
        if not output.strip():
            return "Working directory is clean (no changes)"
        
        # Parse and format the output
        lines = output.strip().split('\n')
        modified = []
        added = []
        deleted = []
        untracked = []
        
        for line in lines:
            if not line.strip():
                continue
            
            status = line[:2]
            filename = line[3:].strip()
            
            if '??' in status:
                untracked.append(filename)
            elif 'M' in status:
                modified.append(filename)
            elif 'A' in status:
                added.append(filename)
            elif 'D' in status:
                deleted.append(filename)
        
        # Format output
        result_lines = ["Git Status:"]
        
        if modified:
            result_lines.append(f"\nModified ({len(modified)}):")
            for f in modified:
                result_lines.append(f"  M {f}")
        
        if added:
            result_lines.append(f"\nAdded ({len(added)}):")
            for f in added:
                result_lines.append(f"  A {f}")
        
        if deleted:
            result_lines.append(f"\nDeleted ({len(deleted)}):")
            for f in deleted:
                result_lines.append(f"  D {f}")
        
        if untracked:
            result_lines.append(f"\nUntracked ({len(untracked)}):")
            for f in untracked:
                result_lines.append(f"  ?? {f}")
        
        return '\n'.join(result_lines)
    
    except subprocess.TimeoutExpired:
        return "Error: Git status command timed out after 30 seconds"
    except FileNotFoundError:
        return "Error: Git is not installed or not in PATH"
    except Exception as e:
        return f"Error running git status: {str(e)}"
