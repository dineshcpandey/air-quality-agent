# Minimal test page for debugging button clicks
import streamlit as st
import requests
import json

st.set_page_config(page_title="Debug Button Test", layout="wide")

st.title("🔍 Debug Button Click Test")

# Force local backend URL
BACKEND_URL = "http://localhost:8001"
st.write(f"Backend URL: `{BACKEND_URL}`")

# Test backend connectivity
col1, col2 = st.columns(2)

with col1:
    if st.button("Test Backend Health"):
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=2)
            st.success(f"✅ Backend is healthy: {response.json()}")
        except Exception as e:
            st.error(f"❌ Backend error: {e}")

with col2:
    if st.button("Test Query Endpoint"):
        try:
            response = requests.post(
                f"{BACKEND_URL}/query",
                json={"query": "test"},
                timeout=2
            )
            st.success(f"✅ Query endpoint works: Status {response.status_code}")
        except Exception as e:
            st.error(f"❌ Query endpoint error: {e}")

st.divider()

# Simulate disambiguation scenario
st.header("Test Disambiguation Flow")

if 'test_state' not in st.session_state:
    st.session_state.test_state = None

# Step 1: Get disambiguation state
if st.button("1. Get Ambedkar Nagar Locations"):
    with st.spinner("Fetching..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/query",
                json={"query": "What is PM2.5 in Ambedkar Nagar"},
                timeout=10
            )
            result = response.json()
            state = result.get('state')
            
            if state and state.get('waiting_for_user'):
                st.session_state.test_state = state
                st.success(f"✅ Got {len(state.get('locations', []))} locations")
                st.json(state.get('locations'))
            else:
                st.error("No disambiguation state received")
                st.json(result)
        except Exception as e:
            st.error(f"Error: {e}")

# Step 2: Show selection buttons
if st.session_state.test_state:
    locations = st.session_state.test_state.get('locations', [])
    
    st.subheader(f"2. Select from {len(locations)} locations:")
    
    for idx, loc in enumerate(locations):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{idx}.** {loc.get('display_name', loc.get('name'))}")
        
        with col2:
            # Direct API call on button click
            button_key = f"select_{idx}_{id(loc)}"
            if st.button(f"Select {idx}", key=button_key):
                st.write(f"Clicked button {idx}")
                
                # Make the selection API call
                selection_url = f"{BACKEND_URL}/query/select"
                st.write(f"Calling: `{selection_url}`")
                
                try:
                    payload = {
                        "state": st.session_state.test_state,
                        "selected_index": idx
                    }
                    
                    st.write("Sending payload:")
                    st.json({"selected_index": idx, "locations_count": len(locations)})
                    
                    response = requests.post(
                        selection_url,
                        json=payload,
                        timeout=10
                    )
                    
                    st.write(f"Response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Selection successful!")
                        
                        data = result.get('data', {})
                        if data.get('formatted_response'):
                            st.markdown("### Result:")
                            st.info(data['formatted_response'])
                        
                        if data.get('raw_data'):
                            st.json(data['raw_data'])
                    else:
                        st.error(f"Selection failed: {response.status_code}")
                        st.text(response.text)
                        
                except Exception as e:
                    st.error(f"Exception during selection: {e}")
                    import traceback
                    st.text(traceback.format_exc())

st.divider()
st.caption("This is a debug page to test button clicks and API calls")
