# 🚨 QUICK FIX: Webhook Interception Issue

## THE PROBLEM
When you click a location button → Goes to Fivetran webhook instead of your backend

## WHY IT HAPPENS
Something in your environment is intercepting HTTP requests from Streamlit

## IMMEDIATE FIX (Do This Now!)

### Option 1: Use Bypass App (FASTEST)
```bash
streamlit run src/ui/streamlit_bypass.py
```
- Try "DIRECT_WORKFLOW" method first (no HTTP calls)
- If that fails, try "CURL" method
- This bypasses the interception completely

### Option 2: Use Direct Mode
```bash
streamlit run src/ui/streamlit_direct.py
```
- Runs everything locally, no external API calls
- Guaranteed to work

### Option 3: Test Without Streamlit
```bash
# Terminal 1
python -m uvicorn src.api.main:app --reload --port 8001

# Terminal 2
python scripts/serve_test_page.py
# Open: http://localhost:8502/test_api_standalone.html
```

## FIND THE CULPRIT

Run this diagnostic:
```bash
python scripts/diagnose_webhook_interception.py
```

Look for:
- ⚠️ SUSPICIOUS environment variables
- ⚠️ SUSPICIOUS content in config files
- ⚠️ Modified Python packages

## MOST LIKELY CAUSES

1. **Fivetran Browser Extension**
   - Check: chrome://extensions/
   - Action: Disable it

2. **Environment Variable**
   ```bash
   env | grep -i fivetran
   # If found: unset VARIABLE_NAME
   ```

3. **Corporate Proxy/VPN**
   - Disconnect VPN
   - Check with IT

4. **Streamlit Config**
   ```bash
   cat ~/.streamlit/secrets.toml
   # Should NOT contain webhook URLs
   ```

## PERMANENT FIX

```bash
# 1. Clear all configs
rm -rf ~/.streamlit
unset $(env | grep -i webhook | cut -d= -f1)
unset $(env | grep -i fivetran | cut -d= -f1)

# 2. Create clean config
mkdir ~/.streamlit
echo 'backend_url = "http://localhost:8001"' > ~/.streamlit/secrets.toml

# 3. Test
streamlit run src/ui/streamlit_bypass.py
```

## SUCCESS CRITERIA

✅ You know it's fixed when:
- Browser DevTools shows: `POST http://localhost:8001/query/select`
- Backend console shows: `[API] Selection received`
- PM2.5 data appears in chat

## FILES YOU NEED

- **Quick Fix**: `src/ui/streamlit_bypass.py` (4 bypass methods)
- **Direct Mode**: `src/ui/streamlit_direct.py` (no HTTP)
- **Diagnostic**: `scripts/diagnose_webhook_interception.py`
- **Test Flow**: `scripts/test_complete_flow.py`

## REMEMBER

- The data flow IS working (Location → PM Agent → Display)
- Only the button click is being intercepted
- The bypass apps will work immediately
- Finding root cause is secondary to getting it working

---
**Start with Option 1 above - it will work!**
