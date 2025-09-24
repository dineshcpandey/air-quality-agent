#!/usr/bin/env python3
"""
Run the Air Quality app with explicit backend URL configuration

This ensures the correct backend URL is used regardless of other configurations.
"""

import os
import subprocess
import sys
from pathlib import Path

def main():
    # Set the backend URL explicitly
    os.environ['BACKEND_URL'] = 'http://localhost:8001'
    os.environ['STREAMLIT_BACKEND_URL'] = 'http://localhost:8001'
    
    # Remove any webhook-related environment variables
    for key in list(os.environ.keys()):
        if 'WEBHOOK' in key.upper() or 'FIVETRAN' in key.upper():
            print(f"Removing environment variable: {key}")
            del os.environ[key]
    
    print("=" * 60)
    print("Starting Air Quality Q&A Agent with correct configuration")
    print("=" * 60)
    print(f"Backend URL: {os.environ['BACKEND_URL']}")
    print("=" * 60)
    
    # Get project root
    root = Path(__file__).parent.parent
    
    # Start streamlit with explicit command
    streamlit_cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(root / "src" / "ui" / "streamlit_pm_query.py"),
        "--server.port", "8501",
        "--server.address", "localhost"
    ]
    
    print(f"Running: {' '.join(streamlit_cmd)}")
    print("\nIMPORTANT: Make sure the backend is running in another terminal:")
    print("  python -m uvicorn src.api.main:app --reload --port 8001")
    print("=" * 60)
    
    # Run streamlit
    subprocess.run(streamlit_cmd, cwd=str(root))

if __name__ == "__main__":
    main()
