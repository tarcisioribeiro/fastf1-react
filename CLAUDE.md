# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Streamlit-based web application for displaying Formula 1 data using the FastF1 library. Despite the name "fastf1-react", this is a Python Streamlit application, not a React application.

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Or use a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application
```bash
streamlit run app.py
```

The application will start on http://localhost:8501 by default.

## Architecture

### Application Structure
- **app.py**: Main dashboard UI with tabs for different views
- **f1_data.py**: Data management layer that handles FastF1 API calls and formatting
- **database.py**: SQLite cache layer for storing processed data

The application is organized in a modular way:
- UI layer (app.py) - Handles rendering and user interaction
- Data layer (f1_data.py) - Handles API calls, data fetching and formatting
- Cache layer (database.py) - SQLite database for persistent caching

### Key Dependencies
- **streamlit**: Web framework for the UI
- **fastf1**: Library for accessing Formula 1 timing and telemetry data
- **pandas**: Data manipulation (used by FastF1)
- **sqlite3**: Database for caching processed data

### Caching Strategy
The application uses a two-tier caching system:
1. **FastF1 Cache** (`.fastf1_cache/`) - Raw API data cache
2. **SQLite Cache** (`f1_cache.db`) - Processed data cache with 24-hour TTL

This significantly improves load times and reduces API calls.

### Data Formatting
- All dates are formatted in Brazilian format (DD/MM/YYYY)
- All data is displayed for the 2025 season
- The application automatically finds the latest available race/qualifying session
- Podium positions are highlighted with gold/silver/bronze styling

## Development Notes

- The application automatically finds the latest race by iterating backwards from round 24
- Session types in FastF1: 'FP1', 'FP2', 'FP3', 'Q' (Qualifying), 'S' (Sprint), 'R' (Race)
- Streamlit automatically reruns the script on file changes when running in development mode
- FastF1 data is cached in `.fastf1_cache/` directory
- SQLite database (`f1_cache.db`) stores processed standings and results

## Docker Deployment

The application includes Docker support:
- `Dockerfile` - Container image definition
- `docker-compose.yml` - Orchestration with volume persistence
- Volumes are used to persist both FastF1 cache and SQLite database
