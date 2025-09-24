#!/usr/bin/env python3
"""
Diagnose where the webhook interception is happening

This script checks all possible sources of the webhook URL.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import configparser

print("=" * 70)
print("WEBHOOK INTERCEPTION DIAGNOSTIC")
print("=" * 70)

# 1. Check Environment Variables
print("\n1️⃣ ENVIRONMENT VARIABLES CHECK:")
print("-" * 40)
suspicious_vars = []
for key, value in os.environ.items():
    if any(term in key.upper() for term in ['WEBHOOK', 'FIVETRAN', 'BACKEND', 'API', 'URL', 'ENDPOINT']):
        print(f"  {key} = {value[:50]}...")
        if 'fivetran' in value.lower() or 'webhook' in value.lower():
            suspicious_vars.append(key)
            print(f"     ⚠️ SUSPICIOUS!")

if suspicious_vars:
    print(f"\n❌ Found suspicious environment variables: {suspicious_vars}")
    print("  Fix: unset these variables")
    for var in suspicious_vars:
        print(f"    unset {var}")
else:
    print("✅ No suspicious environment variables found")

# 2. Check Streamlit Config Files
print("\n2️⃣ STREAMLIT CONFIGURATION FILES:")
print("-" * 40)

config_locations = [
    Path.home() / ".streamlit",
    Path.cwd() / ".streamlit",
    Path("/etc/streamlit"),
    Path.home() / ".config" / "streamlit"
]

for loc in config_locations:
    if loc.exists():
        print(f"\n  Found config directory: {loc}")
        
        # Check secrets.toml
        secrets_file = loc / "secrets.toml"
        if secrets_file.exists():
            print(f"    📄 secrets.toml exists")
            with open(secrets_file) as f:
                content = f.read()
                if 'webhook' in content.lower() or 'fivetran' in content.lower():
                    print(f"      ⚠️ SUSPICIOUS CONTENT FOUND!")
                    print(f"      First 200 chars: {content[:200]}")
                elif 'backend_url' in content:
                    # Extract backend_url value
                    for line in content.split('\n'):
                        if 'backend_url' in line:
                            print(f"      backend_url line: {line}")
        
        # Check config.toml
        config_file = loc / "config.toml"
        if config_file.exists():
            print(f"    📄 config.toml exists")
            with open(config_file) as f:
                content = f.read()
                if 'webhook' in content.lower() or 'fivetran' in content.lower():
                    print(f"      ⚠️ SUSPICIOUS CONTENT FOUND!")

# 3. Check Python Site Packages
print("\n3️⃣ PYTHON PACKAGES CHECK:")
print("-" * 40)

try:
    import streamlit as st
    st_location = Path(st.__file__).parent
    print(f"  Streamlit installed at: {st_location}")
    
    # Check if streamlit has been modified
    config_py = st_location / "config.py"
    if config_py.exists():
        with open(config_py) as f:
            content = f.read()
            if 'webhook' in content.lower() or 'fivetran' in content.lower():
                print("    ⚠️ Streamlit config.py has been modified with webhook!")
except Exception as e:
    print(f"  Error checking streamlit: {e}")

# 4. Check for Proxy Settings
print("\n4️⃣ PROXY SETTINGS:")
print("-" * 40)

proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY']
for var in proxy_vars:
    value = os.environ.get(var)
    if value:
        print(f"  {var} = {value}")
        if 'fivetran' in value.lower():
            print(f"    ⚠️ SUSPICIOUS PROXY!")
    else:
        print(f"  {var} = Not set")

# 5. Check Git Config (in case of hooks)
print("\n5️⃣ GIT CONFIGURATION:")
print("-" * 40)

try:
    git_config = subprocess.run(['git', 'config', '--list'], 
                               capture_output=True, text=True, timeout=2)
    if git_config.returncode == 0:
        for line in git_config.stdout.split('\n'):
            if 'webhook' in line.lower() or 'fivetran' in line.lower():
                print(f"  ⚠️ Found in git config: {line}")
except Exception as e:
    print(f"  Could not check git config: {e}")

# 6. Check for .env files
print("\n6️⃣ CHECKING .ENV FILES:")
print("-" * 40)

env_files = ['.env', '.env.local', '.env.development', '.env.production']
for env_file in env_files:
    env_path = Path.cwd() / env_file
    if env_path.exists():
        print(f"  Found: {env_path}")
        with open(env_path) as f:
            content = f.read()
            if 'webhook' in content.lower() or 'fivetran' in content.lower():
                print(f"    ⚠️ SUSPICIOUS CONTENT!")
                for line in content.split('\n'):
                    if 'webhook' in line.lower() or 'fivetran' in line.lower():
                        print(f"      {line[:80]}")

# 7. Check Browser Cache
print("\n7️⃣ BROWSER CACHE LOCATIONS:")
print("-" * 40)
print("  Browser cache might contain cached redirects.")
print("  Try:")
print("    1. Open browser in Incognito/Private mode")
print("    2. Clear browser cache and cookies")
print("    3. Disable browser extensions")
print("    4. Try a different browser")

# 8. Check System Hosts File
print("\n8️⃣ HOSTS FILE CHECK:")
print("-" * 40)

hosts_file = Path("/etc/hosts")
if hosts_file.exists():
    with open(hosts_file) as f:
        content = f.read()
        if 'fivetran' in content.lower():
            print("  ⚠️ Fivetran entry found in hosts file!")
        if 'localhost' in content:
            for line in content.split('\n'):
                if 'localhost' in line and not line.strip().startswith('#'):
                    print(f"  localhost entry: {line}")

# 9. Check Streamlit Cache
print("\n9️⃣ STREAMLIT CACHE:")
print("-" * 40)

cache_dirs = [
    Path.home() / ".streamlit" / "cache",
    Path.cwd() / ".streamlit" / "cache"
]

for cache_dir in cache_dirs:
    if cache_dir.exists():
        print(f"  Cache exists at: {cache_dir}")
        print(f"    Size: {sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file()) / 1024 / 1024:.2f} MB")
        print("    Try clearing with: rm -rf " + str(cache_dir))

# 10. Network Configuration
print("\n🔟 NETWORK CONFIGURATION:")
print("-" * 40)

try:
    # Check if port 8001 is listening
    netstat = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
    if netstat.returncode == 0:
        for line in netstat.stdout.split('\n'):
            if '8001' in line and 'LISTEN' in line:
                print(f"  ✅ Port 8001 is listening: {line[:80]}")
except:
    pass

# Summary and Recommendations
print("\n" + "=" * 70)
print("SUMMARY AND RECOMMENDATIONS")
print("=" * 70)

print("\n🔍 MOST LIKELY CAUSES:")
print("  1. Environment variable override")
print("  2. Streamlit secrets.toml misconfiguration") 
print("  3. Browser extension intercepting requests")
print("  4. Corporate proxy or security software")

print("\n🛠️ IMMEDIATE FIXES TO TRY:")
print("""
1. Clear everything and start fresh:
   rm -rf ~/.streamlit
   unset $(env | grep -i webhook | cut -d= -f1)
   unset $(env | grep -i fivetran | cut -d= -f1)
   
2. Run with explicit configuration:
   BACKEND_URL=http://localhost:8001 streamlit run src/ui/streamlit_pm_query.py
   
3. Use the direct mode (no external calls):
   streamlit run src/ui/streamlit_direct.py
   
4. Check browser console for JavaScript errors:
   - Open DevTools (F12)
   - Go to Console tab
   - Look for any errors when clicking button
   
5. Try a different browser or incognito mode
""")

print("\n💡 TO FIND THE EXACT INTERCEPTION POINT:")
print("""
In browser DevTools:
1. Network tab → Clear
2. Click the location button
3. Look for the request to fivetran
4. Right-click → Copy → Copy as cURL
5. Check the "Initiator" column to see what triggered it
""")
