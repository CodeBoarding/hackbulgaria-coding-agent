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
- **File Reading**: Read files with line numbers
- **File Writing**: Write or modify files at specific line ranges
- **Google Gemini**: Powered by Google's Gemini LLM

## Development

This project uses Python 3.12 with uv for fast dependency management.
