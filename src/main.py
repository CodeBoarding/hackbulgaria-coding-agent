"""Main entry point for the coding agent."""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.react_agent import create_coding_agent
from src.agent.orchestrator import orchestrate_multi_agent

# System prompt for the coding agent
SYSTEM_PROMPT = """You are an expert coding assistant specialized in Python development. Your role is to help users with their coding tasks by:

1. **Reading and Writing Files**: You can read files to understand existing code and write new files or modify existing ones.

2. **Code Quality**: Always validate Python code you create or modify using the lint_file tool. This ensures:
   - No syntax errors (checked via AST parsing)
   - No unused imports or variables
   - Code follows Python best practices
   - Proper code style and conventions

3. **Best Practices**:
   - After creating or modifying a Python file, ALWAYS run lint_file on it to check for issues
   - The lint_file tool will first check for syntax errors using AST parsing
   - If syntax errors are found, fix them immediately before continuing
   - After syntax is valid, pylint will check for style and quality issues
   - If linting reveals problems, fix them and lint again
   - Aim for a pylint score of 8.0 or higher
   - Explain any linting issues you find and how you fixed them

4. **Workflow**:
   - Understand the user's request
   - Read relevant files if needed
   - Create or modify files as requested
   - Validate with lint_file (catches both syntax errors and style issues)
   - Fix any issues found
   - Re-validate to ensure fixes worked
   - Report the final result with the pylint score

5. **Communication**:
   - Be clear and concise
   - Explain your reasoning
   - Ask for confirmation before making significant changes
   - Report the results of your actions

You have access to these tools:
- read_file: Read contents of a file with line numbers
- write_file: Create or modify files at specific line ranges
- lint_file: Validate Python files (AST syntax check + pylint analysis)
- run_bash_command: Execute bash commands to explore the codebase (ls, grep, find, git, etc.)

Use run_bash_command to:
- Explore directory structure (ls, tree, find)
- Search for patterns in files (grep, ag)
- Check git status and history (git status, git log)
- Count lines of code (wc -l)
- Find files by name or extension (find . -name "*.py")

Always strive for clean, well-structured, and properly linted code."""


def format_message_content(content):
    """Format message content for better readability.
    
    Handles both string content and list of content blocks.
    Truncates signatures in metadata.
    """
    if isinstance(content, str):
        return content
    
    if isinstance(content, list):
        formatted_parts = []
        for item in content:
            if isinstance(item, dict):
                # Extract text and handle metadata
                text = item.get('text', '')
                if text:
                    formatted_parts.append(text)
                
                # Show truncated metadata if present
                if 'extras' in item:
                    extras = item['extras'].copy()
                    if 'signature' in extras:
                        sig = extras['signature']
                        extras['signature'] = f"{sig[:50]}..." if len(sig) > 50 else sig
                    formatted_parts.append(f"\n[Metadata: {extras}]")
            elif isinstance(item, str):
                formatted_parts.append(item)
        
        return ''.join(formatted_parts)
    
    return str(content)


def main():
    """Run the coding agent CLI."""
    parser = argparse.ArgumentParser(description="HackBulgaria Coding Agent")
    parser.add_argument(
        "--home",
        type=str,
        default=None,
        help="Home directory for the agent (where it will create/read files)"
    )
    parser.add_argument(
        "--multi-agent",
        action="store_true",
        help="Use multi-agent mode (planning + implementation + validation agents)"
    )
    args = parser.parse_args()
    
    print("=== HackBulgaria Coding Agent ===")
    if args.home:
        print(f"Working directory: {args.home}")
    if args.multi_agent:
        print("Mode: Multi-Agent (Planning → Implementation → Validation)")
    else:
        print("Mode: Single Agent")
    print("Type your request or 'quit' to exit\n")
    
    # Multi-agent mode
    if args.multi_agent:
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Run multi-agent orchestration
                result = orchestrate_multi_agent(user_input, home_directory=args.home)
                
                # Display final summary
                print("\n" + "="*70)
                print("FINAL SUMMARY")
                print("="*70)
                print(f"\nStatus: {result['status']}")
                print(f"Fix iterations: {result['iterations']}")
                
                if result['status'] == 'approved':
                    print("\n✅ Implementation approved and ready!")
                else:
                    print("\n⚠️  Implementation needs review.")
                
                print("\n" + "="*70 + "\n")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}\n")
        return
    
    # Single agent mode (existing)
    agent = create_coding_agent(home_directory=args.home)
    
    # Thread ID for maintaining conversation memory
    thread_id = "default_session"
    
    # Flag to track if system prompt has been sent
    system_prompt_sent = False
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Run agent
            print("\nAgent working...\n")
            
            # Include system prompt only on first message
            if not system_prompt_sent:
                messages = [("system", SYSTEM_PROMPT), ("user", user_input)]
                system_prompt_sent = True
            else:
                messages = [("user", user_input)]
            
            # Stream the agent's execution to see tools in real-time
            for chunk in agent.stream(
                {"messages": messages},
                config={"configurable": {"thread_id": thread_id}}
            ):
                # Display tool calls and results in real-time
                if "agent" in chunk:
                    for message in chunk["agent"]["messages"]:
                        if hasattr(message, 'tool_calls') and message.tool_calls:
                            for tool_call in message.tool_calls:
                                tool_name = tool_call.get('name', 'unknown')
                                tool_args = tool_call.get('args', {})
                                print(f"🔧 Using tool: {tool_name}")
                                if 'file_path' in tool_args:
                                    print(f"   → File: {tool_args['file_path']}")
                                print()
                
                if "tools" in chunk:
                    for message in chunk["tools"]["messages"]:
                        if hasattr(message, 'content'):
                            # Show first 200 chars of tool output
                            content_preview = str(message.content)[:200]
                            if len(str(message.content)) > 200:
                                content_preview += "..."
                            print(f"✓ Tool result: {content_preview}\n")
            
            # Get final result to display
            final_result = agent.invoke(
                {"messages": messages},
                config={"configurable": {"thread_id": thread_id}}
            )
            
            # Display final agent response
            print("\n" + "="*50)
            print("Agent Response:")
            print("="*50 + "\n")
            for message in final_result["messages"]:
                if hasattr(message, 'content') and message.content:
                    # Only show AI messages (not tool calls)
                    if hasattr(message, 'type') and message.type == 'ai':
                        formatted_output = format_message_content(message.content)
                        if formatted_output.strip():
                            print(f"{formatted_output}\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}\n")


if __name__ == "__main__":
    main()
