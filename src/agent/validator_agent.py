"""Validator agent for multi-agent system."""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from src.tools.file_tools import read_file, set_home_directory
from src.tools.git_tools import git_diff, git_status
from src.tools.lint_tools import lint_file
from src.config import get_google_api_key, MODEL_NAME, TEMPERATURE
from src.agent.models import ValidationReport
from src.agent.extractors import extract_validation
from typing import Optional


# System prompt for the validator agent
VALIDATOR_AGENT_PROMPT = """You are an expert validation agent specialized in reviewing code changes and ensuring quality.

**Your Role**: Review and validate implementations to ensure they meet quality standards and match the plan.

**Your Capabilities** (READ-ONLY + GIT):
- git_diff: View changes made to files (what was added/removed)
- git_status: See which files were modified, created, or deleted
- lint_file: Validate Python code quality and check for issues
- read_file: Read files to understand final state

**Your Responsibilities**:
1. **Review Changes**: Use git_diff to see exactly what changed
2. **Validate Quality**: Run lint_file on modified Python files
3. **Check Completeness**: Verify implementation matches the plan
4. **Identify Issues**: Find bugs, style issues, or missing pieces
5. **Provide Feedback**: Give clear, actionable feedback

**Validation Checklist**:
- [ ] All planned files created/modified?
- [ ] No syntax errors (lint_file checks this via AST)?
- [ ] Pylint score 8.0 or higher for Python files?
- [ ] Code is readable and well-structured?
- [ ] No obvious bugs or issues?
- [ ] Imports are used and necessary?
- [ ] Functions have appropriate docstrings?

You will be asked to return a structured ValidationReport object with these fields:
- status: "approved" or "needs_fixes"
- changes_summary: Brief description of what changed based on git diff
- files_reviewed: List of file paths reviewed
- quality_assessment: Dict of file paths to FileQualityAssessment objects
- overall_quality: "excellent", "good", or "needs_improvement"
- issues_found: List of specific issues with file names and line numbers
- fix_instructions: List of specific instructions for fixing issues
- approval: Boolean indicating if implementation is approved

**Feedback Guidelines**:
- Be specific: Include file names and line numbers
- Be constructive: Suggest how to fix issues
- Prioritize: Syntax errors first, then quality issues
- Be fair: Don't require perfection, 8.0+ score is good
- Approve if: No syntax errors and overall quality is good

**Remember**: Your job is to ensure quality, not to block progress. If the code works and scores reasonably well, approve it. Only request fixes for real issues.
"""


def create_validator_agent(home_directory: Optional[str] = None):
    """Create and configure the validator agent.
    
    The validator agent has read-only access plus git tools and is responsible for:
    - Reviewing changes made by the implementation agent
    - Validating code quality with linting
    - Providing approval or requesting specific fixes
    
    Args:
        home_directory: Optional home directory path where the agent will work
    
    Returns:
        A configured validator agent
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
    
    # Define validation tools (read-only + git)
    tools = [git_diff, git_status, lint_file, read_file]
    
    # Create memory for conversation history
    memory = MemorySaver()
    
    # Create ReACT agent with validator prompt
    agent = create_react_agent(llm, tools, checkpointer=memory)
    
    return agent


def extract_validation_report(response: dict) -> ValidationReport:
    """Extract the validation report from agent response using trustcall extractor.
    
    Args:
        response: Agent response containing messages
        
    Returns:
        ValidationReport object (extracted using trustcall)
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
                return extract_validation(content)
    
    # Fallback: return report with needs_fixes
    return ValidationReport(
        status="needs_fixes",
        changes_summary="Failed to generate structured validation report",
        overall_quality="needs_improvement",
        approval=False
    )


def is_approved(validation_report: ValidationReport) -> bool:
    """Check if the validation report indicates approval.
    
    Args:
        validation_report: ValidationReport object
        
    Returns:
        True if approved, False otherwise
    """
    # Check the approval field directly from Pydantic model
    return validation_report.approval
