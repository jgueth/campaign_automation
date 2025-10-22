"""
Credentials Management

This module handles loading API credentials from credentials.json file.
"""

import json
from pathlib import Path
from typing import Dict, Any


def get_project_root() -> Path:
    """Get the project root directory (where credentials.json is located)."""
    # Start from this file and go up to project root
    current = Path(__file__).resolve()
    # Go up: credentials.py -> campaign_automation -> src -> project_root
    return current.parent.parent.parent


def load_credentials() -> Dict[str, Any]:
    """
    Load API credentials from credentials.json file.

    Returns:
        Dictionary containing all credentials

    Raises:
        FileNotFoundError: If credentials.json doesn't exist
        json.JSONDecodeError: If credentials.json is not valid JSON
    """
    creds_file = get_project_root() / 'credentials.json'

    if not creds_file.exists():
        raise FileNotFoundError(
            f"credentials.json not found at {creds_file}\n"
            "Copy credentials.json.example and add your API keys:\n"
            "  cp credentials.json.example credentials.json"
        )

    try:
        with open(creds_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in credentials.json: {e.msg}",
            e.doc,
            e.pos
        )


def get_openai_api_key() -> str:
    """
    Get OpenAI API key from credentials.

    Returns:
        OpenAI API key string

    Raises:
        KeyError: If openai.api_key is not found in credentials
    """
    creds = load_credentials()
    try:
        return creds['openai']['api_key']
    except KeyError:
        raise KeyError(
            "OpenAI API key not found in credentials.json. "
            "Make sure 'openai.api_key' is defined."
        )


def get_gemini_api_key() -> str:
    """
    Get Google Gemini API key from credentials.

    Returns:
        Gemini API key string

    Raises:
        KeyError: If google.gemini_api_key is not found in credentials
    """
    creds = load_credentials()
    try:
        return creds['google']['gemini_api_key']
    except KeyError:
        raise KeyError(
            "Gemini API key not found in credentials.json. "
            "Make sure 'google.gemini_api_key' is defined."
        )


def get_dropbox_access_token() -> str:
    """
    Get Dropbox access token from credentials.

    Returns:
        Dropbox access token string

    Raises:
        KeyError: If dropbox.access_token is not found in credentials
    """
    creds = load_credentials()
    try:
        return creds['dropbox']['access_token']
    except KeyError:
        raise KeyError(
            "Dropbox access token not found in credentials.json. "
            "Make sure 'dropbox.access_token' is defined."
        )


# Example usage
if __name__ == "__main__":
    """Test credentials loading."""
    try:
        creds = load_credentials()
        print("Credentials loaded successfully!")
        print(f"Available services: {list(creds.keys())}")

        openai_key = get_openai_api_key()
        print(f"OpenAI API key: {openai_key[:20]}...")

        gemini_key = get_gemini_api_key()
        print(f"Gemini API key: {gemini_key[:20]}...")

        try:
            dropbox_token = get_dropbox_access_token()
            print(f"Dropbox access token: {dropbox_token[:20]}...")
        except KeyError:
            print("Dropbox access token: Not configured (optional)")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except KeyError as e:
        print(f"Error: {e}")
