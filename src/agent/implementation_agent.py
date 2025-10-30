"""Implementation agent for multi-agent system."""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from src.tools.file_tools import read_file, write_file, set_home_directory
from src.tools.bash_tools import run_bash_command
from src.tools.lint_tools import lint_file
from src.config import get_google_api_key, MODEL_NAME, TEMPERATURE
from src.agent.models import ImplementationReport
from src.agent.extractors import extract_implementation
from typing import Optional


# System prompt for the implementation agent
IMPLEMENTATION_AGENT_PROMPT = """You are an expert implementation agent specialized in executing coding plans and creating high-quality code.

**Your Role**: Execute plans created by the planning agent with precision and care.

**Your Capabilities** (READ/WRITE ACCESS):
- read_file: Read files to understand context
- write_file: Create new files or modify existing files
- lint_file: Validate Python code quality (AST syntax check + pylint)
- run_bash_command: Execute bash commands when needed

**Your Responsibilities**:
1. **Follow the Plan**: Execute each step in the plan sequentially
2. **Write Clean Code**: Create well-structured, idiomatic code
3. **Validate Quality**: Run lint_file on every Python file you create/modify
4. **Fix Issues**: If linting finds problems, fix them immediately
5. **Report Progress**: Clearly communicate what you've done

**Workflow**:
1. Read the execution plan carefully
2. For each step in order:
   - Read relevant files if needed for context
   - Create or modify the file as specified
   - If it's a Python file, run lint_file immediately
   - If linting shows issues (especially syntax errors), fix them
   - Re-lint to confirm fixes worked
3. Aim for pylint scores of 8.0 or higher
4. Report your results with file paths and linting scores

**Code Quality Standards**:
- Always check for syntax errors first (lint_file does this via AST)
- Fix unused imports and variables
- Use proper naming conventions (snake_case for functions/variables)
- Add docstrings to functions and classes
- Keep functions focused and modular
- Handle errors appropriately

You will be asked to return a structured ImplementationReport object with these fields:
- status: "success", "partial", or "failed"
- files_created: List of file paths created
- files_modified: List of file paths modified
- linting_results: Dict of file paths to LintingResult objects
- summary: Brief summary of what was implemented
- issues_encountered: Any problems or deviations from plan

**Remember**: Quality over speed. It's better to create correct, well-linted code than to rush through the plan.
"""


def create_implementation_agent(home_directory: Optional[str] = None):
    """Create and configure the implementation agent.
    
    The implementation agent has read/write access and is responsible for:
    - Executing the plan created by the planning agent
    - Creating and modifying files
    - Running linting and fixing issues
    - Producing high-quality code
    
    Args:
        home_directory: Optional home directory path where the agent will work
    
    Returns:
        A configured implementation agent
    """
    # Set home directory for file operations if provided
    if home_directory:
        set_home_directory(home_directory)
    
    # Initialize Gemini LLM (without structured output for ReACT agent)
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        google_api_key=get_google_api_key()
    )
    
    # Define read/write tools
    tools = [read_file, write_file, lint_file, run_bash_command]
    
    # Create memory for conversation history
    memory = MemorySaver()
    
    # Create ReACT agent with implementation prompt
    agent = create_react_agent(llm, tools, checkpointer=memory)
    
    return agent


def extract_implementation_report(response: dict) -> ImplementationReport:
    """Extract the implementation report from agent response using trustcall extractor.
    
    Args:
        response: Agent response containing messages
        
    Returns:
        ImplementationReport object (extracted using trustcall)
    """
    # Get the last AI message
    messages = response.get("messages", [])
    
    for message in reversed(messages):
        if hasattr(message, 'type') and message.type == 'ai':
            content = message.content
            
            # Handle content as list of blocks (new format)
            if isinstance(content, list):
                # Extract text from content blocks
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'text':
                        text_parts.append(block.get('text', ''))
                content = '\n'.join(text_parts)
            
            # Handle content as string (old format)
            if isinstance(content, str) and len(content.strip()) > 50:
                # Use trustcall extractor to extract structured report
                return extract_implementation(content)
    
    # Fallback: return minimal report
    return ImplementationReport(
        status="failed",
        summary="Failed to generate structured report from agent response"
    )

