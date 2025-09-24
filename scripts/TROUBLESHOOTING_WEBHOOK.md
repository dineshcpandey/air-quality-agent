# 🔥 TROUBLESHOOTING: Fivetran Webhook Issue

## Problem
When clicking location selection buttons, the app is calling `https://webhooks.fivetran.com/webhooks/...` instead of the local backend at `http://localhost:8001/query/select`.

## Root Cause
This indicates a configuration override somewhere in your environment. The Fivetran webhook URL is being injected into the Streamlit app configuration.

## Solutions (Try in Order)

### Solution 1: Run with Explicit Configuration
```bash
# This forces the correct backend URL
python scripts/run_streamlit_safe.py
```

### Solution 2: Test Backend Directly
```bash
# Verify the backend selection endpoint works
python scripts/test_backend_selection.py

# This should show successful selection without any webhook calls
```

### Solution 3: Use Debug Interface
```bash
# Run the debug UI to isolate the issue
streamlit run src/ui/debug_buttons.py

# This page shows exactly what URLs are being called
```

### Solution 4: Check Environment Variables
```bash
# Check for any webhook-related environment variables
env | grep -i webhook
env | grep -i fivetran
env | grep -i backend

# Remove any problematic variables
unset WEBHOOK_URL
unset FIVETRAN_WEBHOOK
```

### Solution 5: Check Streamlit Configuration
```bash
# Check what configuration Streamlit is using
python scripts/debug_streamlit_config.py

# Verify secrets.toml has correct backend URL
cat ~/.streamlit/secrets.toml
# Should show: backend_url = "http://localhost:8001"
```

### Solution 6: Clear Streamlit Cache
```bash
# Clear any cached configuration
rm -rf ~/.streamlit/cache
rm -rf ~/.streamlit/config.toml
rm -rf ~/.streamlit/secrets.toml

# Recreate with correct config
mkdir -p ~/.streamlit
echo 'backend_url = "http://localhost:8001"' > ~/.streamlit/secrets.toml
```

### Solution 7: Check Browser Extensions
1. Open browser developer tools (F12)
2. Go to Network tab
3. Click a selection button
4. Check if any browser extension is intercepting/redirecting the request

### Solution 8: Direct Test with curl
```bash
# First, get disambiguation state
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is PM2.5 in Ambedkar Nagar"}'

# Copy the state from response, then test selection
curl -X POST http://localhost:8001/query/select \
  -H "Content-Type: application/json" \
  -d '{"state": <PASTE_STATE_HERE>, "selected_index": 0}'
```

## What's Been Fixed

1. **Updated streamlit_pm_query.py:**
   - Added explicit backend URL validation
   - Added safety checks to prevent webhook URLs
   - Added debug logging for all API calls

2. **Created configuration files:**
   - `~/.streamlit/secrets.toml` with correct backend URL
   - `~/.streamlit/config.toml` with proper settings

3. **Added debug tools:**
   - `scripts/test_backend_selection.py` - Direct backend test
   - `scripts/run_streamlit_safe.py` - Run with forced configuration
   - `src/ui/debug_buttons.py` - Debug UI for testing

## Expected Behavior

When you click a location button:
1. Browser should make POST request to `http://localhost:8001/query/select`
2. Backend console should show: `[API] Selection received: index=X`
3. PM2.5 data should appear in the chat

## If Still Not Working

1. **Check for proxy settings:**
   ```bash
   echo $HTTP_PROXY
   echo $HTTPS_PROXY
   ```

2. **Check hosts file:**
   ```bash
   cat /etc/hosts | grep localhost
   # Should show: 127.0.0.1 localhost
   ```

3. **Try different browser:**
   - The issue might be browser-specific
   - Try incognito/private mode

4. **Check Streamlit version:**
   ```bash
   pip show streamlit
   # Should be recent version
   ```

5. **Reinstall dependencies:**
   ```bash
   pip uninstall streamlit requests -y
   pip install streamlit requests
   ```

## Quick Test Sequence

1. Start backend:
   ```bash
   python -m uvicorn src.api.main:app --reload --port 8001
   ```

2. In new terminal, test backend:
   ```bash
   python scripts/test_backend_selection.py
   ```
   
3. If backend test works, run safe Streamlit:
   ```bash
   python scripts/run_streamlit_safe.py
   ```

4. If still seeing webhook calls, run debug UI:
   ```bash
   streamlit run src/ui/debug_buttons.py
   ```

## Contact for Help

If none of these solutions work:
1. Share the output of `python scripts/debug_streamlit_config.py`
2. Share browser network tab screenshot when clicking button
3. Share any error messages from console

The webhook URL should NEVER be called - this is a configuration issue that needs to be tracked down.
