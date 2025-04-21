# 🛣️ Code Way

Code Way is a CLI tool that uses the Anthropic Claude API to analyze code files using a structured framework with symbolic anchors.

## Features

- Analyze code files using the Code Way framework
- Supports multiple programming languages
- Uses symbolic anchors to organize different types of programming assistance

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/codeway.git
cd codeway

# Install with Poetry
poetry install
```

## Usage

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY='your_secret_key_here'

# Analyze one or more code files
codeway my_script.py utils.py

# Specify a different Claude model
codeway my_script.py --model claude-3-opus-20240229

# Control response length
codeway my_script.py --max-tokens 8000

# Enable verbose output
codeway my_script.py -v
```

## Framework

Code Way uses a structured framework with emoji symbolic anchors to organize different types of programming assistance:

- 🏗️ (generate): Code Generation
- 🔍 (examine): Debugging
- 📖 (explain): Code Explanation
- 🧪 (test): Test Generation
- 📋 (document): Documentation
- 🔧 (improve): Refactoring & Optimization
- 🏛️ (structure): Design & Architecture
- 📊 (analyze): Requirements Analysis

## Requirements

- Python 3.12+
- Anthropic API Key
