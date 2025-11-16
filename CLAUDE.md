# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Somsiad is a Polish Discord bot written in Python using discord.py. It provides numerous features including music playback, search capabilities, moderation tools, user statistics, and AI chat functionality. The bot integrates with multiple external APIs (Google, YouTube, Spotify, OpenAI, etc.) and uses PostgreSQL, ClickHouse, and Redis for data storage.

## Architecture

- **Main bot file**: `somsiad.py` - Core Discord bot implementation with command handling and event listeners
- **Entry point**: `run.py` - Application startup with Sentry integration and debugging support
- **Core functionality**: `core.py` - Command invocation tracking and data processing opt-out management
- **Configuration**: `configuration.py` - Environment variable handling and bot configuration
- **Data layer**: `data.py` - SQLAlchemy models and database schema definitions
- **Utilities**: `utilities.py` - Common helper functions and API clients
- **Plugin system**: `plugins/` directory contains modular command implementations
- **Web interface**: `web/` directory contains Flask web application for bot status and documentation

## Development Commands

### Environment Setup
```bash
# Set up development environment with Python virtual environment
./develop.sh

# Activate virtual environment manually
source venv/bin/activate
```

### Running the Bot
```bash
# Development mode with Docker Compose (recommended)
docker-compose -f docker-compose.dev.yml up

# Run in background
docker-compose -f docker-compose.dev.yml up -d

# Production mode
docker-compose up
```

### Code Quality
```bash
# Format code with Black (via ruff)
ruff format .

# Lint with ruff
ruff check . --fix

# Type checking with mypy  
mypy .

# Run pre-commit hooks manually
pre-commit run --all-files
```

### Database and Dependencies
```bash
# Update and install Python dependencies
uv sync
```

## Configuration

The bot requires numerous API keys and tokens configured via environment variables:
- `DISCORD_TOKEN` - Discord bot token
- `ANTHROPIC_API_KEY` - For AI chat functionality
- `GOOGLE_KEY` + `GOOGLE_CUSTOM_SEARCH_ENGINE_ID` - For search features
- Database URLs for PostgreSQL, ClickHouse, and Redis
- Various third-party API keys (Spotify, Last.fm, TMDb, etc.)

Copy `.template.env` to `.env` and configure according to your setup.

## Testing

Tests are located in the `tests/` directory. The project uses a basic testing setup:
```bash
# Run tests (check for specific test runner in pyproject.toml or CI configuration)
python -m pytest tests/
```

## Key Dependencies

- `discord.py[voice]` - Discord API wrapper with voice support
- `openai` + `tiktoken` - AI chat integration  
- `SQLAlchemy` + `psycopg2` - Database ORM and PostgreSQL driver
- `aiochclient` - ClickHouse async client for analytics
- `redis` - Caching and session storage
- `ruff` + `black` + `mypy` - Code formatting, linting, and type checking
- `sentry-sdk` - Error tracking and monitoring

## Plugin Development

Commands are organized as plugins in the `plugins/` directory. Each plugin typically:
- Inherits from `commands.Cog`
- Uses the `@commands.command()` decorator
- Follows the existing patterns for error handling and data processing opt-outs
- May integrate with external APIs through utility classes in `utilities.py`
