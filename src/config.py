"""Configuration management for the coding agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in project root
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)


def get_google_api_key() -> str:
    """Get Google API key from environment variables."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    return api_key


# Model configuration
MODEL_NAME = "gemini-2.5-pro"
TEMPERATURE = 0.7
