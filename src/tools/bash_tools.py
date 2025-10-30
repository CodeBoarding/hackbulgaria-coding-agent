"""Bash/shell command tools for the coding agent."""

from langchain_core.tools import tool
from pathlib import Path
import subprocess
from src.tools.file_tools import _home_directory


@tool
def run_bash_command(command: str) -> str:
    """Run a bash command to explore the codebase.
    
    Useful for:
    - Listing directory contents (ls, find, tree)
    - Searching files (grep, ag, rg)
    - Checking file info (wc, file, stat)
    - Git operations (git status, git log, git diff)
    - Other read-only exploration commands
    
    Args:
        command: The bash command to execute
        
    Returns:
        Command output or error message
    """
    # Security: Block potentially dangerous commands
    dangerous_patterns = [
        'rm ', 'rm\t', 'rm\n',  # delete
        'sudo', 'su ',  # privilege escalation
        '> ', '>>',  # file redirection (write)
        'mkfs', 'dd ',  # disk operations
        'chmod', 'chown',  # permission changes
        '&& rm', '| rm',  # piped deletion
    ]
    
    cmd_lower = command.lower()
    for pattern in dangerous_patterns:
        if pattern in cmd_lower:
            return f"Error: Command blocked for safety reasons. Pattern '{pattern}' is not allowed."
    
    try:
        # Set working directory to home directory if set
        cwd = str(_home_directory) if _home_directory else None
        
        # Run command with timeout
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
            cwd=cwd
        )
        
        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]:\n{result.stderr}"
        
        # Limit output size
        max_output = 5000
        if len(output) > max_output:
            output = output[:max_output] + f"\n\n... (output truncated, showing first {max_output} characters)"
        
        # Add exit code if non-zero
        if result.returncode != 0:
            output += f"\n\n[Exit code: {result.returncode}]"
        
        return output if output.strip() else "[No output]"
    
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"
