# HackBulgaria Coding Agent - Implementation Plan

## Project Overview
Building a coding agent using LangChain and Google Gemini with a ReACT (Reasoning and Acting) architecture. The project will follow an iterative, minimal implementation approach.

## Phase 1: Minimal ReACT Coding Agent

### Goal
Create a basic ReACT agent that can read and write files using Google Gemini as the LLM.

### Core Components

#### 1. Tools (Minimal Set)
- **Read File Tool**: Reads content from a specified file path
  - Input: file path (string)
  - Output: file content (string) with line numbering upfront, or error message
  - Error handling: file not found, permission errors

- **Write File Tool**: Writes content to a specified file path
  - Input: file path (string), new content (string), line range in which the new content will be placed
  - Output: success confirmation or error message
  - Error handling: permission errors, directory creation if needed

#### 2. ReACT Agent
- Use LangChain's ReACT agent implementation
- Integrate Google Gemini via langchain-google-genai
- Agent should be able to:
  - Reason about what actions to take
  - Use the read/write tools appropriately
  - Provide thought process in responses

#### 3. Configuration
- Environment variables for API keys (GOOGLE_API_KEY), use .env for this
- Basic agent configuration (model name, temperature, etc.)

### Implementation Steps

1. **Setup Environment** ✅
   - Initialize Python 3.12 venv with uv
   - Install dependencies (langchain, langchain-google-genai, pylint, astroid)
   - Configure Git repository

2. **Create Tool Implementations**
   - Implement read_file tool as LangChain tool
   - Implement write_file tool as LangChain tool
   - Add basic validation and error handling

3. **Initialize Gemini LLM**
   - Configure Google Gemini model
   - Set up API key management
   - Test basic LLM functionality

4. **Build ReACT Agent**
   - Create ReACT agent with Gemini + tools (use the default from langchain/langgraph)
   - Configure agent parameters
   - Add prompt engineering for coding tasks

5. **Create Main Interface**
   - Simple CLI or Python script to interact with agent
   - Accept user prompts
   - Display agent reasoning and actions

### Success Criteria
- Agent can successfully read files from the file system
- Agent can successfully write files to the file system
- Agent demonstrates ReACT pattern (thought → action → observation)
- Agent can complete simple coding tasks (e.g., "read config.py and create a summary in summary.txt")

### Future Enhancements (Post-Phase 1)
- Additional tools (search, execute code, git operations)
- Memory and conversation history
- Multi-file operations
- Code analysis tools (using pylint/astroid)
- Improved error handling and recovery
- Structured output and logging

## Project Structure
```
hb-coding-agent/
├── .venv/                  # Virtual environment
├── .gitignore
├── README.md
├── requirements.txt
├── plan.md                 # This file
├── .env                    # API keys (not committed)
├── src/
│   ├── __init__.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── file_tools.py   # Read/write file tools
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── react_agent.py  # ReACT agent implementation
│   ├── config.py           # Configuration management
│   └── main.py             # Entry point
```

## Next Immediate Steps
1. Create project structure (src/, tests/ directories)
2. Implement file tools (read_file, write_file)
3. Set up Gemini LLM configuration
4. Build ReACT agent
5. Create simple CLI interface
