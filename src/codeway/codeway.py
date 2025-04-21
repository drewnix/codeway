#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Code Way Analysis Command-Line Interface (CLI) Tool

This script takes one or more code file paths as input, reads their content,
combines it with a predefined Code Way framework description (read from 'codeway.md'),
sends the request to the Anthropic Claude API, and prints the analysis response.

Usage:
  python codeway.py <code_file1> [code_file2 ...]

Requirements:
  - Python 3.7+
  - anthropic library (`pip install anthropic`)
  - Anthropic API Key set as an environment variable: ANTHROPIC_API_KEY
  - A file named 'codeway.md' in the same directory, containing the
    Code Way framework description.

Example:
  # 1. Create codeway.md with the framework description
  # 2. Set API Key:
  #    export ANTHROPIC_API_KEY='your_secret_key_here'
  # 3. Run analysis:
  python codeway.py my_script.py utils.py --model claude-3-opus-20240229
"""

import argparse
import os
import sys
from anthropic import Anthropic, AnthropicError, APIStatusError, APIConnectionError

# --- Configuration ---
DEFAULT_MODEL = "claude-3-sonnet-20240229"
DEFAULT_MAX_TOKENS = 4000 # Increased default tokens for potentially detailed analysis
API_KEY_ENV_VAR = "ANTHROPIC_API_KEY"
CODEWAY_PROMPT_FILENAME = os.path.join(os.path.dirname(__file__), "prompts", "codeway.md") # Path to the fixed system prompt

# --- Helper Functions ---

def read_file_content(filepath, is_critical=False):
    """
    Reads content from a specified file path.

    Args:
        filepath (str): The path to the file.
        is_critical (bool): If True, exits the script on file read error.

    Returns:
        str: The content of the file, or None if an error occurred and not critical.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"⚠️ Error: File not found: {filepath}", file=sys.stderr)
        if is_critical:
            sys.exit(1)
        return None
    except Exception as e:
        print(f"⚠️ Error reading file {filepath}: {e}", file=sys.stderr)
        if is_critical:
            sys.exit(1)
        return None

def get_api_key(env_var_name):
    """Retrieves the API key from environment variables."""
    api_key = os.environ.get(env_var_name)
    if not api_key:
        print(f"⚠️ Error: Environment variable '{env_var_name}' not set.", file=sys.stderr)
        print("Please set the environment variable with your Anthropic API key.", file=sys.stderr)
    return api_key

def initialize_anthropic_client(api_key):
    """Initializes and returns the Anthropic client."""
    if not api_key:
        return None
    try:
        client = Anthropic(api_key=api_key)
        return client
    except Exception as e:
        print(f"⚠️ Error initializing Anthropic client: {e}", file=sys.stderr)
        return None

def call_claude_api(client, model, max_tokens, system_prompt, user_prompt):
    """Sends the request to the Claude API and returns the response text."""
    print(f"\nSending request to Claude (model: {model})...")
    try:
        # Ensure system prompt is provided
        if not system_prompt:
             print("⚠️ Error: System prompt (from codeway.md) is missing or empty.", file=sys.stderr)
             return None

        messages = [{"role": "user", "content": user_prompt}]
        api_args = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            "system": system_prompt # Use the content of codeway.md as the system prompt
        }

        message = client.messages.create(**api_args)

        response_text = ""
        if message.content and isinstance(message.content, list):
            text_block = next((block.text for block in message.content if block.type == 'text'), None)
            if text_block:
                response_text = text_block
            else:
                 print("⚠️ Warning: No text content found in Claude's response.", file=sys.stderr)
        elif hasattr(message, 'text'):
             response_text = message.text
        else:
            print("⚠️ Warning: Unexpected response structure from Claude.", file=sys.stderr)
            print(f"Full response object: {message}", file=sys.stderr)

        return response_text

    except APIConnectionError as e:
        print(f"⚠️ API Connection Error: Please check your network connection. {e}", file=sys.stderr)
        return None
    except APIStatusError as e:
        print(f"⚠️ API Status Error: {e.status_code} - {e.response}", file=sys.stderr)
        # Add specific guidance based on status code
        if e.status_code == 401:
             print("   (Check if your API key is correct and active)", file=sys.stderr)
        elif e.status_code == 429:
             print("   (You might be exceeding rate limits)", file=sys.stderr)
        elif e.status_code == 400:
             # Check for context length exceeded errors more robustly
             response_body = str(e.response).lower()
             if "context_length_exceeded" in response_body or "token limit" in response_body:
                  print(f"   (Input code + system prompt likely exceed the model's context window)", file=sys.stderr)
             else:
                  print(f"   (Bad request - check input formatting or parameters)", file=sys.stderr)
        return None
    except AnthropicError as e:
        print(f"⚠️ Anthropic API Error: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"⚠️ An unexpected error occurred during API call: {e}", file=sys.stderr)
        return None

# --- Main Execution Logic ---

def main():
    """
    Main function to parse arguments, read files, and interact with Claude API
    using the Code Way framework.
    """
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Analyzes code files using the Code Way framework via the Claude API.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    # REMOVED: --prompt argument
    parser.add_argument(
        "files",
        nargs='+',
        metavar='CODE_FILE',
        help="Path(s) to the code file(s) to be analyzed."
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"The Claude model to use.\nDefault: {DEFAULT_MODEL}"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Maximum number of tokens for Claude's analysis response.\nDefault: {DEFAULT_MAX_TOKENS}"
    )
    # REMOVED: --system argument (now fixed from file)
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output, including the full prompts sent to Claude."
    )

    args = parser.parse_args()

    # --- Initialization ---
    api_key = get_api_key(API_KEY_ENV_VAR)
    if not api_key:
        sys.exit(1)

    client = initialize_anthropic_client(api_key)
    if not client:
        sys.exit(1)

    # --- Read Fixed System Prompt (Code Way Framework) ---
    print(f"--- Reading Code Way framework from: {CODEWAY_PROMPT_FILENAME} ---")
    codeway_system_prompt = read_file_content(CODEWAY_PROMPT_FILENAME, is_critical=True)
    # No need to check if None, read_file_content exits if critical and file fails

    # --- Process Code Files ---
    code_files_aggregated = []
    valid_files_processed = 0
    print("--- Reading Code Files ---")
    for filepath in args.files:
        print(f"Processing: {filepath}...")
        content = read_file_content(filepath, is_critical=False) # Don't exit if one code file fails
        if content is not None:
            # Format the code content with clear boundaries
            code_files_aggregated.append(f"--- Start of code file: {os.path.basename(filepath)} ---")
            code_files_aggregated.append(content)
            code_files_aggregated.append(f"--- End of code file: {os.path.basename(filepath)} ---\n")
            valid_files_processed += 1
        else:
            print(f"Skipping file {filepath} due to read error.", file=sys.stderr)

    if valid_files_processed == 0:
        print("\n⚠️ Error: No valid code files could be read. Exiting.", file=sys.stderr)
        sys.exit(1)

    print(f"Successfully read {valid_files_processed} code file(s).")
    combined_code_text = "\n".join(code_files_aggregated)

    # --- Construct User Prompt for API ---
    # Instruct Claude to use the system prompt (Code Way) to analyze the provided code
    final_user_prompt = (
        f"Apply the Code Way framework (provided in the system prompt) to analyze the following code contained in {valid_files_processed} file(s):\n\n"
        f"{combined_code_text}\n\n"
        f"Provide your analysis based *only* on the framework and the code provided."
    )


    if args.verbose:
        print("\n--- Prompts Being Sent to Claude ---")
        print(f"[SYSTEM PROMPT from {CODEWAY_PROMPT_FILENAME}]:\n{codeway_system_prompt[:500]}... (truncated)") # Show beginning of system prompt
        print("\n[USER PROMPT]:")
        print(final_user_prompt)
        print("------------------------------------")


    # --- API Interaction ---
    analysis_response = call_claude_api(
        client=client,
        model=args.model,
        max_tokens=args.max_tokens,
        system_prompt=codeway_system_prompt, # Pass the framework as system prompt
        user_prompt=final_user_prompt      # Pass the code and instruction as user prompt
    )

    # --- Output ---
    if analysis_response is not None:
        print("\n--- Code Way Analysis Response ---")
        print(analysis_response)
        print("----------------------------------")
        sys.exit(0)
    else:
        print("\nFailed to get analysis from Claude.", file=sys.stderr)
        sys.exit(1)

# --- Script Entry Point ---
if __name__ == "__main__":
    main()
