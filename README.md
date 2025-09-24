# Air Quality Q&A Agent

This project implements a multi-agent architecture for natural language querying of air quality data, using LangGraph orchestration and progressive enhancement from rule-based to LLM-powered agents.

## Project Structure

```
air-quality-agent/
├── src/
│   ├── agents/          # Query processing agents
│   ├── tools/           # Database tools
│   ├── graphs/          # LangGraph workflows  
│   ├── utils/           # Utilities (cache, db, etc)
│   ├── api/             # FastAPI endpoints
│   └── training/        # SLM data collection
├── config/              # Configuration files
├── tests/               # Test suite
├── docs/                # Documentation
├── scripts/             # Deployment scripts
├── logs/                # Application logs
├── data/                # Training data collection
└── README.md
```

## Implementation Plan & Progress
See `docs/implementation_progress.md` for the step-by-step plan, progress log, and deviations.

## Getting Startedz
1. Set up the development environment and install dependencies (see `requirements.txt`).
2. Follow the implementation plan in `docs/implementation_progress.md`.
3. Run tests in the `tests/` folder to validate agent functionality.

## Contact & Support
- Project Lead: [Your Name]
- Technical Questions: [Slack/Email]
- Documentation: See `docs/`

---



# Air Quality Q&A Agent - Quick Start Guide

## 🚀 Running the Application

### Option 1: Run Everything Together (Recommended)
```bash
python scripts/run_app.py
```
This starts both:
- Backend API at http://localhost:8001
- Streamlit UI at http://localhost:8501

### Option 2: Run Services Separately

**Backend (Terminal 1):**
```bash
python -m uvicorn src.api.main:app --reload --port 8001
```

**Frontend (Terminal 2):**
```bash
streamlit run src/ui/streamlit_pm_query.py
```

## 🧪 Testing the Disambiguation Flow

### Test with Script
```bash
# Test the complete flow
python scripts/test_disambiguation_flow.py "ambedkar nagar"

# Test with other locations
python scripts/test_disambiguation_flow.py "delhi"
python scripts/test_disambiguation_flow.py "araria"
```

### Test Manually in UI
1. Open http://localhost:8501
2. Type: "What is the current PM2.5 in ambedkar nagar"
3. You should see a list of locations to choose from
4. Click on one of the location buttons
5. PM2.5 data will be displayed

## 🔍 Debugging

### Check Console Output
When you run a query, check the terminal running the backend for debug output:
```
[API] New query received: 'what is the current PM2.5 in ambedkar nagar'
[API] Workflow returned state:
  - waiting_for_user: True
  - locations count: 3
  - has error: False
  - has response: False
```

### Common Issues and Fixes

#### Issue 1: No Locations Displayed
**Symptom:** Query runs but no disambiguation options shown  
**Fix:** Check that the backend returns `waiting_for_user: true` and non-empty `locations`

#### Issue 2: "1" Shows as Query
**Symptom:** Typing "1" in chat instead of selecting option  
**Fix:** Click the location buttons, don't type numbers in chat

#### Issue 3: Backend Connection Error
**Symptom:** "Backend connection error" in UI  
**Fix:** 
- Ensure backend is running on port 8001
- Check `.streamlit/secrets.toml` has correct backend_url

#### Issue 4: Database Connection Failed
**Symptom:** Backend startup fails  
**Fix:** 
- Check `.env` file has correct database credentials
- Verify PostgreSQL is running
- Test with: `python test_db_connection.py`

## 📊 Expected Behavior

### Single Location Match
**Query:** "What is PM2.5 in Delhi"  
**Result:** Direct display of PM2.5 value

### Multiple Location Matches
**Query:** "What is PM2.5 in Ambedkar Nagar"  
**Result:** 
1. Shows list of matching locations
2. User clicks a location button
3. PM2.5 value displayed for selected location

### No Location Found
**Query:** "What is PM2.5 in XYZ123"  
**Result:** Error message about location not found

## 📝 Key Files Changed

1. **src/ui/streamlit_pm_query.py**
   - Improved disambiguation display in chat flow
   - Better button layout and visibility
   - Enhanced error handling

2. **src/api/main.py**
   - Added detailed debug logging
   - Better error messages
   - Health check endpoints

3. **src/graphs/pm_query_workflow.py**
   - Improved location extraction from queries
   - Better response formatting
   - Enhanced error messages

4. **src/agents/location_resolver.py**
   - Better display name formatting
   - Emoji indicators for location types
   - Hierarchical location context

## 🛠️ Configuration

### Backend Settings (.env)
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=airquality
DB_USER=postgres
DB_PASSWORD=yourpassword
```

### Frontend Settings (.streamlit/secrets.toml)
```toml
backend_url = "http://127.0.0.1:8001"
```

## 📈 Monitoring

### Backend Logs
- Location extraction: `[Workflow] Extracted location: 'ambedkar nagar'`
- Database queries: `[LocationResolver] Found 3 location(s)`
- PM data fetch: `[PMDataAgent] Fetching PM2.5 for...`

### Frontend Logs
- Console shows backend responses
- Check browser DevTools for network requests

## 🎯 Next Steps

1. **Test Different Queries:**
   - Try various location formats
   - Test edge cases (misspellings, partial names)

2. **Enhance Features:**
   - Add trend queries
   - Implement comparison between locations
   - Add time-based queries

3. **Optimize Performance:**
   - Implement caching
   - Add query batching
   - Optimize database queries

## 💡 Tips

- Always check console output when debugging
- Use the test script to isolate backend issues
- Clear chat and retry if UI gets stuck
- Backend must be running before frontend

## 📞 Support

If you encounter issues:
1. Check console output for errors
2. Verify all services are running
3. Test with the disambiguation flow script
4. Check database connectivity
_Last updated: 21 Sep 2025_
