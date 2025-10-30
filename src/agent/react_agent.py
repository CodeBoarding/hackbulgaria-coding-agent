"""ReACT agent implementation using LangChain and Google Gemini."""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from src.tools.file_tools import read_file, write_file, set_home_directory
from src.tools.lint_tools import lint_file
from src.config import get_google_api_key, MODEL_NAME, TEMPERATURE
from typing import Optional


def create_coding_agent(home_directory: Optional[str] = None):
    """Create and configure the ReACT coding agent.
    
    Args:
        home_directory: Optional home directory path where the agent will work.
                       All relative file paths will be resolved relative to this directory.
    
    Returns:
        A configured ReACT agent
    """
    # Set home directory for file operations if provided
    if home_directory:
        set_home_directory(home_directory)
    
    # Initialize Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        google_api_key=get_google_api_key()
    )
    
    # Define tools
    tools = [read_file, write_file, lint_file]
    
    # Create memory for conversation history
    memory = MemorySaver()
    
    # Create ReACT agent using LangGraph's prebuilt agent with memory
    agent = create_react_agent(llm, tools, checkpointer=memory)
    
    return agent
