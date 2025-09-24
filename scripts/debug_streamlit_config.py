#!/usr/bin/env python3
"""
Debug script to check Streamlit configuration and backend URL

Run this to see what backend URL is being used.
"""

import streamlit as st
import os
import sys
from pathlib import Path

print("=" * 60)
print("Streamlit Configuration Debug")
print("=" * 60)

# Check environment variables
print("\n1. Environment Variables:")
print(f"   STREAMLIT_BACKEND_URL: {os.getenv('STREAMLIT_BACKEND_URL', 'Not set')}")
print(f"   BACKEND_URL: {os.getenv('BACKEND_URL', 'Not set')}")
print(f"   API_URL: {os.getenv('API_URL', 'Not set')}")

# Check .streamlit directory locations
print("\n2. Streamlit Config Locations:")
possible_locations = [
    Path.home() / ".streamlit",
    Path.cwd() / ".streamlit",
    Path(__file__).parent.parent / ".streamlit"
]

for loc in possible_locations:
    if loc.exists():
        print(f"   ✅ Found: {loc}")
        secrets_file = loc / "secrets.toml"
        if secrets_file.exists():
            print(f"      - secrets.toml exists")
            with open(secrets_file) as f:
                content = f.read()
                if content:
                    print(f"      - Content preview: {content[:100]}")
    else:
        print(f"   ❌ Not found: {loc}")

# Try to access Streamlit secrets
print("\n3. Streamlit Secrets Access:")
try:
    if hasattr(st, 'secrets'):
        print("   ✅ st.secrets is available")
        
        # Try to get backend_url
        backend_url = st.secrets.get('backend_url', 'DEFAULT_NOT_SET')
        print(f"   - backend_url from secrets: {backend_url}")
        
        # List all available secrets (keys only for security)
        try:
            secret_keys = list(st.secrets.keys()) if hasattr(st.secrets, 'keys') else []
            if secret_keys:
                print(f"   - Available secret keys: {secret_keys}")
        except:
            print("   - Could not list secret keys")
    else:
        print("   ❌ st.secrets not available")
except Exception as e:
    print(f"   ❌ Error accessing secrets: {e}")

# Check the actual value that would be used
print("\n4. Actual Backend URL Resolution:")
try:
    # This mimics what the streamlit app does
    BACKEND_URL = st.secrets.get('backend_url', 'http://127.0.0.1:8001')
    print(f"   Final BACKEND_URL: {BACKEND_URL}")
except:
    print("   Using fallback: http://127.0.0.1:8001")

print("\n" + "=" * 60)
print("Debug complete!")
print("=" * 60)
