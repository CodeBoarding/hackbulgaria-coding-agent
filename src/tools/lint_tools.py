"""Code linting tools for the coding agent."""

from langchain_core.tools import tool
from pathlib import Path
from io import StringIO
import sys
import ast
from pylint.lint import Run
from pylint.reporters.text import TextReporter
from src.tools.file_tools import _resolve_path, _home_directory


@tool
def lint_file(file_path: str) -> str:
    """Run pylint on a Python file and return linting results.
    
    File paths are resolved relative to the home directory (set via --home flag).
    First checks for syntax errors via AST parsing, then runs pylint for quality checks.
    
    Args:
        file_path: Path to the Python file to lint (relative to home directory if set)
        
    Returns:
        Formatted linting results with score, errors, and warnings
    """
    try:
        # Resolve path relative to home directory if set
        path = _resolve_path(file_path)
        
        if not path.exists():
            return f"Error: File '{file_path}' not found"
        
        if not path.suffix == '.py':
            return f"Error: File '{file_path}' is not a Python file"
        
        # First, check for syntax errors using AST
        try:
            with open(path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            ast.parse(source_code, filename=str(path))
        except SyntaxError as e:
            return (
                f"❌ SYNTAX ERROR in '{file_path}':\n\n"
                f"Line {e.lineno}: {e.msg}\n"
                f"  {e.text.strip() if e.text else ''}\n"
                f"  {' ' * (e.offset - 1) if e.offset else ''}^\n\n"
                f"Fix this syntax error before running pylint."
            )
        except Exception as e:
            return f"Error parsing file: {str(e)}"
        
        # Capture pylint output
        pylint_output = StringIO()
        reporter = TextReporter(pylint_output)
        
        # Run pylint
        try:
            Run([str(path)], reporter=reporter, exit=False)
        except SystemExit:
            pass  # Pylint calls sys.exit, we need to catch it
        
        # Get the output
        output = pylint_output.getvalue()
        
        # Parse output to extract key information
        lines = output.split('\n')
        
        # Extract score
        score_line = None
        for line in lines:
            if 'Your code has been rated at' in line:
                score_line = line
                break
        
        # Categorize messages
        errors = []
        warnings = []
        conventions = []
        refactors = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith(str(path)):
                # Parse message format: filepath:line:column: message-type: message
                parts = line.split(':', 3)
                if len(parts) >= 4:
                    try:
                        line_num = parts[1].strip()
                        msg_type = parts[3].strip()
                        
                        if msg_type.startswith('E'):
                            errors.append(f"Line {line_num}: {msg_type}")
                        elif msg_type.startswith('W'):
                            warnings.append(f"Line {line_num}: {msg_type}")
                        elif msg_type.startswith('C'):
                            conventions.append(f"Line {line_num}: {msg_type}")
                        elif msg_type.startswith('R'):
                            refactors.append(f"Line {line_num}: {msg_type}")
                    except (IndexError, ValueError):
                        continue
        
        # Format results
        result = []
        
        if score_line:
            result.append(f"Pylint Results for '{file_path}':")
            result.append(score_line.strip())
        else:
            result.append(f"Pylint Results for '{file_path}':")
        
        result.append("")
        
        if errors:
            result.append(f"Errors ({len(errors)}):")
            for error in errors[:10]:  # Limit to first 10
                result.append(f"  {error}")
            if len(errors) > 10:
                result.append(f"  ... and {len(errors) - 10} more errors")
            result.append("")
        
        if warnings:
            result.append(f"Warnings ({len(warnings)}):")
            for warning in warnings[:10]:  # Limit to first 10
                result.append(f"  {warning}")
            if len(warnings) > 10:
                result.append(f"  ... and {len(warnings) - 10} more warnings")
            result.append("")
        
        if conventions:
            result.append(f"Convention Issues ({len(conventions)}):")
            for conv in conventions[:5]:  # Limit to first 5
                result.append(f"  {conv}")
            if len(conventions) > 5:
                result.append(f"  ... and {len(conventions) - 5} more convention issues")
            result.append("")
        
        if not errors and not warnings and not conventions and not refactors:
            result.append("✓ No issues found!")
        
        # Add summary
        result.append(f"\nSummary: {len(errors)} errors, {len(warnings)} warnings, {len(conventions)} conventions")
        
        return '\n'.join(result)
    
    except Exception as e:
        return f"Error running pylint: {str(e)}"
