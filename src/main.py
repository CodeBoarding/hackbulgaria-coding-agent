"""Main entry point for the coding agent."""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.react_agent import create_coding_agent


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
    args = parser.parse_args()
    
    print("=== HackBulgaria Coding Agent ===")
    if args.home:
        print(f"Working directory: {args.home}")
    print("Type your request or 'quit' to exit\n")
    
    # Create agent with optional home directory
    agent = create_coding_agent(home_directory=args.home)
    
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
            print("\nAgent:")
            result = agent.invoke({"messages": [("user", user_input)]})
            
            # Display result
            for message in result["messages"]:
                if hasattr(message, 'content') and message.content:
                    formatted_output = format_message_content(message.content)
                    print(f"{formatted_output}\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}\n")


if __name__ == "__main__":
    main()
