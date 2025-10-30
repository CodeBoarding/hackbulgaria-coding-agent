# HackBulgaria Coding Agent

A minimal ReACT coding agent built with LangChain and Google Gemini. The agent can read and write files using natural language commands.

## Setup

1. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

3. Configure your Google API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

## Usage

Run the agent:
```bash
python src/main.py
```

Or specify a home directory where the agent will work:
```bash
python src/main.py --home /path/to/workspace
```

When a home directory is set, all relative file paths will be resolved relative to that directory. This is useful for:
- Isolating the agent's operations to a specific project folder
- Working on multiple projects without interference
- Testing the agent in a sandboxed environment

Example commands:
- "Read the file plan.md"
- "Create a new file hello.txt with the content 'Hello World'"
- "Read config.py and create a summary in summary.txt"

## Features

- **ReACT Agent**: Uses reasoning and acting pattern for task completion
- **Conversation Memory**: Remembers conversation context throughout the session
- **File Reading**: Read files with line numbers
- **File Writing**: Write or modify files at specific line ranges
- **Code Validation**: Automatic pylint validation for Python files
- **Home Directory Support**: Sandboxed operations within a specified directory
- **Google Gemini**: Powered by Google's Gemini LLM
- **System Prompt**: Agent knows it's a coding assistant and follows best practices

## How It Works

The agent maintains conversation memory during your session, allowing it to:
- Remember previous questions and answers
- Understand context from earlier in the conversation
- Respond to confirmations like "yes" or "no" based on what was discussed

### Code Quality Assurance

The agent is programmed to automatically validate Python code it creates:
1. Creates or modifies a Python file
2. Runs `lint_file` to check for issues
3. Reports pylint score and any problems found
4. Fixes issues if needed and re-validates
5. Aims for a score of 8.0 or higher

Example workflow:
```
You: Create a Python function to calculate factorial
Agent: [Creates factorial.py]
Agent: [Runs lint_file on factorial.py]
Agent: "Created factorial.py with a pylint score of 9.5/10"
```

Example conversation flow:
```
You: Should I create a Django project structure?
Agent: I can create the following files... Should I proceed?
You: Yes
Agent: [Creates the files and validates each Python file]
```

Memory persists throughout your CLI session and clears when you exit.

## Development

This project uses Python 3.12 with uv for fast dependency management.
