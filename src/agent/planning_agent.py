"""Planning agent for multi-agent system."""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from src.tools.file_tools import read_file, set_home_directory
from src.tools.bash_tools import run_bash_command
from src.tools.search_tools import grep_search
from src.config import get_google_api_key, MODEL_NAME, TEMPERATURE
from src.agent.models import PlanOutput
from src.agent.extractors import extract_plan
from typing import Optional


# System prompt for the planning agent
PLANNING_AGENT_PROMPT = """You are an expert planning agent specialized in analyzing coding tasks and creating detailed execution plans.

**Your Role**: Analyze user requests and create comprehensive, actionable plans for implementation.

**Your Capabilities** (READ-ONLY ACCESS):
- read_file: Read existing files to understand the codebase
- run_bash_command: Explore directory structure (ls, find, tree, git commands)
- grep_search: Search for patterns across multiple files

**Your Responsibilities**:
1. **Understand the Request**: Carefully analyze what the user is asking for
2. **Explore the Codebase**: Use your tools to understand existing code structure
3. **Research Context**: Find relevant files, functions, patterns using grep_search
4. **Create Detailed Plan**: Produce a structured plan with specific steps

**IMPORTANT**: After using tools to gather information, provide your final response as a JSON object in a markdown code fence like this:

```json
{
  "analysis": "Brief summary of what needs to be done and why",
  "context": "Key findings from codebase exploration",
  "files_to_create": [
    {
      "path": "path/to/new_file.py",
      "purpose": "Brief description of what this file does"
    }
  ],
  "files_to_modify": [
    {
      "path": "path/to/existing_file.py",
      "purpose": "What changes are needed and why"
    }
  ],
  "steps": [
    {
      "sequence": 1,
      "action": "create",
      "file": "path/to/file.py",
      "description": "Detailed description of what to do"
    }
  ],
  "considerations": [
    "Important edge cases",
    "Dependencies to be aware of"
  ]
}
```

**Best Practices**:
- Be thorough in exploration - use grep_search to find patterns
- List files in order of creation/modification
- Be specific about what changes are needed
- Consider dependencies and import statements
- Note any existing code that should be reused
- Identify potential conflicts or issues

**Remember**: You are read-only. You plan but don't implement. The implementation agent will follow your plan exactly, so be clear and detailed. Always end with the JSON plan in a code fence.
"""


def create_planning_agent(home_directory: Optional[str] = None):
    """Create and configure the planning agent.
    
    The planning agent has read-only access and is responsible for:
    - Analyzing user requests
    - Exploring the codebase
    - Creating detailed execution plans
    
    Args:
        home_directory: Optional home directory path where the agent will work
    
    Returns:
        A configured planning agent
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
    
    # Define read-only tools
    tools = [read_file, run_bash_command, grep_search]
    
    # Create memory for conversation history
    memory = MemorySaver()
    
    # Create ReACT agent with planning prompt
    agent = create_react_agent(llm, tools, checkpointer=memory)
    
    return agent


def extract_plan_from_response(response: dict) -> PlanOutput:
    """Extract the structured plan from agent response using trustcall extractor.
    
    Args:
        response: Agent response containing messages
        
    Returns:
        PlanOutput object (extracted using trustcall)
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
                # Use trustcall extractor to extract structured plan
                return extract_plan(content)
    
    # Fallback: return minimal plan
    return PlanOutput(
        analysis="Failed to generate structured plan from agent response",
        context="Agent did not provide parseable output",
        steps=[]
    )

