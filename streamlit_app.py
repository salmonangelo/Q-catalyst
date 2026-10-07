"""Streamlit Community Cloud deployment entrypoint for Q-Catalyst.

Runs the luxury scientific interactive Streamlit application.
"""

import sys
from pathlib import Path

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import and execute main Streamlit application
from app.app import main

if __name__ == "__main__":
    main()
