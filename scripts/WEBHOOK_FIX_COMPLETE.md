# 🚨 WEBHOOK ISSUE - COMPLETE SOLUTION GUIDE

## The Problem
When clicking location selection buttons in the Streamlit UI, instead of calling your local backend (`http://localhost:8001/query/select`), it's calling a Fivetran webhook (`https://webhooks.fivetran.com/webhooks/...`).

This is **NOT normal** and indicates external configuration interference.

## Immediate Solutions

### 1. 🟢 Use the Safe Runner (RECOMMENDED)
```bash
# This forces correct configuration
python scripts/run_streamlit_safe.py
```

### 2. 🟡 Test Without Streamlit
```bash
# Terminal 1: Ensure backend is running
python -m uvicorn src.api.main:app --reload --port 8001

# Terminal 2: Test with standalone HTML
python scripts/serve_test_page.py
# Open browser to http://localhost:8502/test_api_standalone.html
```

If the HTML page works but Streamlit doesn't, the issue is Streamlit-specific.

### 3. 🔵 Debug with Direct API Test
```bash
# Test the backend directly
python scripts/test_backend_selection.py
```

## What I've Fixed

### Updated Files:
1. **src/ui/streamlit_pm_query.py**
   - Added webhook URL detection and blocking
   - Explicit backend URL validation
   - Debug logging for all API calls
   - Forced local backend URL

2. **Configuration Files Created:**
   ```
   ~/.streamlit/secrets.toml    # Correct backend URL
   ~/.streamlit/config.toml     # Streamlit settings
   ```

3. **Debug Tools Created:**
   ```
   scripts/run_streamlit_safe.py       # Force correct config
   scripts/test_backend_selection.py   # Direct backend test
   scripts/debug_streamlit_config.py   # Check configuration
   scripts/serve_test_page.py          # Serve HTML test
   src/ui/debug_buttons.py            # Debug UI
   test_api_standalone.html            # Standalone test page
   ```

## Root Cause Analysis

The Fivetran webhook being called suggests one of these scenarios:

### Scenario 1: Environment Variable Override
```bash
# Check for problematic variables
env | grep -E -i "(webhook|fivetran|backend|api)"

# Remove if found
unset WEBHOOK_URL
unset FIVETRAN_WEBHOOK
unset BACKEND_URL  # Then re-export correct one
export BACKEND_URL="http://localhost:8001"
```

### Scenario 2: Browser Extension/Proxy
- Check browser extensions that might intercept requests
- Try incognito mode
- Try different browser
- Check proxy settings

### Scenario 3: Streamlit Config Override
```bash
# Check all Streamlit configs
find ~ -name "secrets.toml" -o -name "config.toml" 2>/dev/null | grep streamlit

# Check for any .env files
find . -name "*.env*" -exec grep -l webhook {} \;
```

### Scenario 4: Corporate/Network Interference
- VPN or corporate proxy redirecting localhost
- Security software intercepting requests
- DNS hijacking

## Testing Sequence

### Step 1: Verify Backend
```bash
curl http://localhost:8001/health
# Should return: {"status":"healthy",...}
```

### Step 2: Test Selection Endpoint
```bash
python scripts/test_backend_selection.py
# Should complete successfully without webhooks
```

### Step 3: Test HTML Page
```bash
python scripts/serve_test_page.py
# Open http://localhost:8502/test_api_standalone.html
# Click buttons - should work without webhooks
```

### Step 4: Run Safe Streamlit
```bash
python scripts/run_streamlit_safe.py
# Should use correct backend URL
```

## Network Debugging

In browser DevTools (F12) → Network tab:
1. Clear network log
2. Click selection button
3. Check the request:
   - **Expected**: `POST http://localhost:8001/query/select`
   - **Problem**: `POST https://webhooks.fivetran.com/...`

If you see the webhook:
1. Check Request Headers → Look for redirects
2. Check Initiator → See what triggered the request
3. Check Response → See if it's a redirect

## Emergency Workaround

If nothing else works, here's a hardcoded workaround:

```python
# In streamlit_pm_query.py, replace the select_backend function:
def select_backend(state, selected_index):
    import subprocess
    import json
    
    # Use curl to bypass any Python/Streamlit interference
    cmd = [
        'curl', '-X', 'POST',
        'http://localhost:8001/query/select',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps({"state": state, "selected_index": selected_index})
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)
```

## Check These Files

Make sure no webhook URLs in:
```bash
grep -r "webhook" . --include="*.py" --include="*.toml" --include="*.yaml"
grep -r "fivetran" . --include="*.py" --include="*.toml" --include="*.yaml"
```

## Final Resolution

If all else fails:

1. **Create Fresh Environment:**
   ```bash
   python -m venv fresh_venv
   source fresh_venv/bin/activate  # or fresh_venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Run with Explicit Config:**
   ```bash
   BACKEND_URL=http://localhost:8001 streamlit run src/ui/streamlit_pm_query.py
   ```

3. **Use Docker:**
   ```dockerfile
   # Create isolated environment
   docker run -it --net=host python:3.9 bash
   # Install and run inside container
   ```

## Success Criteria

You know it's working when:
1. Browser DevTools shows: `POST http://localhost:8001/query/select`
2. Backend console shows: `[API] Selection received: index=0`
3. PM2.5 data appears in chat

## Get Help

If still not working after all these steps:
1. Run: `python scripts/debug_streamlit_config.py > debug_output.txt`
2. Screenshot browser network tab when clicking button
3. Share both for analysis

The webhook should NEVER be called - this is absolutely a configuration issue that can be fixed.
