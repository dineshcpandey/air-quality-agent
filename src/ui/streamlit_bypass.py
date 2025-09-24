# Streamlit PM Query - Webhook Bypass Version
import streamlit as st
import subprocess
import json
import os
import asyncio
from typing import Any, Dict, List
import time
import traceback
from pathlib import Path
import sys

# Add src to path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / 'src'))

from utils.database import DatabaseConnection
from agents.location_resolver import LocationResolverAgent
from agents.pm_data_agent import PMDataAgent
from graphs.pm_query_workflow import PMQueryWorkflow

# ============================================================================
# BYPASS METHOD CONFIGURATION
# ============================================================================

# Choose bypass method (change this to try different approaches)
BYPASS_METHOD = st.sidebar.selectbox(
    "Select Bypass Method",
    ["CURL", "DIRECT_WORKFLOW", "SUBPROCESS_PYTHON", "URLLIB"],
    help="Different methods to bypass webhook interception"
)

st.sidebar.write(f"Using: {BYPASS_METHOD}")

# ============================================================================
# METHOD 1: CURL BYPASS
# ============================================================================

def select_backend_curl(state: Dict[str, Any], selected_index: int) -> Dict[str, Any]:
    """Use curl command to bypass Python requests library"""
    import subprocess
    import json
    
    url = "http://localhost:8001/query/select"
    data = json.dumps({"state": state, "selected_index": selected_index})
    
    cmd = [
        'curl', '-X', 'POST', url,
        '-H', 'Content-Type: application/json',
        '-d', data,
        '-s',  # Silent
        '--connect-timeout', '10'
    ]
    
    print(f"[CURL] Running: {' '.join(cmd[:3])}...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"error": f"Curl failed: {result.stderr}"}
    except Exception as e:
        return {"error": f"Curl exception: {e}"}

# ============================================================================
# METHOD 2: DIRECT WORKFLOW (NO HTTP)
# ============================================================================

@st.cache_resource
def get_workflow():
    """Get cached workflow instance"""
    try:
        db = DatabaseConnection()
        asyncio.run(db.connect())
        
        location_agent = LocationResolverAgent(db)
        pm_agent = PMDataAgent(db)
        workflow = PMQueryWorkflow(location_agent, pm_agent)
        
        return workflow
    except Exception as e:
        st.error(f"Failed to initialize workflow: {e}")
        return None

def select_backend_direct(state: Dict[str, Any], selected_index: int) -> Dict[str, Any]:
    """Call workflow directly without HTTP"""
    workflow = get_workflow()
    if not workflow:
        return {"error": "Workflow not initialized"}
    
    # Run workflow directly
    try:
        final_state = asyncio.run(
            workflow.continue_with_selection(state, selected_index)
        )
        
        return {
            "data": {
                "formatted_response": final_state.get('response'),
                "raw_data": final_state.get('pm_data')
            }
        }
    except Exception as e:
        return {"error": f"Direct workflow error: {e}"}

# ============================================================================
# METHOD 3: SUBPROCESS PYTHON
# ============================================================================

def select_backend_subprocess(state: Dict[str, Any], selected_index: int) -> Dict[str, Any]:
    """Run Python in subprocess to make the request"""
    
    script = f'''
import requests
import json
import sys

state = {json.dumps(state)}
index = {selected_index}

try:
    response = requests.post(
        "http://localhost:8001/query/select",
        json={{"state": state, "selected_index": index}},
        timeout=10
    )
    print(response.text)
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
'''
    
    try:
        result = subprocess.run(
            [sys.executable, '-c', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": f"Subprocess error: {e}"}

# ============================================================================
# METHOD 4: URLLIB (BYPASS REQUESTS)
# ============================================================================

def select_backend_urllib(state: Dict[str, Any], selected_index: int) -> Dict[str, Any]:
    """Use urllib instead of requests library"""
    import urllib.request
    import urllib.parse
    
    url = "http://localhost:8001/query/select"
    data = json.dumps({"state": state, "selected_index": selected_index})
    data = data.encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": f"Urllib error: {e}"}

# ============================================================================
# MAIN APP
# ============================================================================

def select_backend(state: Dict[str, Any], selected_index: int) -> Dict[str, Any]:

    """Debug version of select_backend to trace execution"""
    import requests
    import json
    import streamlit as st
    import traceback
    import sys 
    
    print("\n" + "="*70)
    print("🔍 SELECT_BACKEND CALLED - DETAILED TRACE")
    print("="*70)
    
    # Log the call
    print(f"✅ Function called at: {time.time()}")
    print(f"📍 Selected index: {selected_index}")
    print(f"📍 Number of locations: {len(state.get('locations', []))}")
    
    # Check BACKEND_URL
    url = f"{BACKEND_URL}/query/select"
    print(f"📍 Target URL: {url}")
    
    # Verify URL is correct
    if 'webhook' in url.lower() or 'fivetran' in url.lower():
        print(f"❌ ERROR: Webhook URL detected: {url}")
        st.error(f"Webhook URL detected: {url}")
        return {"error": f"Webhook URL: {url}"}
    
    if not url.startswith(('http://localhost', 'http://127.0.0.1')):
        print(f"⚠️ WARNING: Non-local URL: {url}")
    
    # Show what we're sending
    payload = {
        "state": state,
        "selected_index": selected_index
    }
    print(f"\n📤 Payload size: {len(json.dumps(payload))} bytes")
    print(f"📤 Payload preview: {json.dumps(payload)[:200]}...")
    
    # Try multiple methods to make the request
    print("\n🔄 Attempting HTTP POST...")
    
    # Method 1: Standard requests
    print("\n1️⃣ Trying requests.post()...")
    try:
        print(f"   Calling: requests.post('{url}', ...)")
        response = requests.post(url, json=payload, timeout=10)
        print(f"   ✅ Response status: {response.status_code}")
        print(f"   ✅ Response URL: {response.url}")
        
        if response.url != url:
            print(f"   ⚠️ REDIRECT DETECTED! Original: {url}, Final: {response.url}")
            
        result = response.json()
        print(f"   ✅ Got response: {json.dumps(result)[:100]}...")
        return result
        
    except Exception as e:
        print(f"   ❌ requests.post failed: {type(e).__name__}: {e}")
        print(f"   Stack trace:")
        traceback.print_exc()
    
    # Method 2: Try urllib as fallback
    print("\n2️⃣ Trying urllib as fallback...")
    try:
        import urllib.request
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        print(f"   Calling: urllib.request.urlopen('{url}', ...)")
        with urllib.request.urlopen(req, timeout=10) as response:
            result_text = response.read().decode('utf-8')
            print(f"   ✅ urllib successful!")
            result = json.loads(result_text)
            print(f"   ✅ Got response: {json.dumps(result)[:100]}...")
            return result
            
    except Exception as e:
        print(f"   ❌ urllib failed: {type(e).__name__}: {e}")
    
    # Method 3: Try curl as last resort
    print("\n3️⃣ Trying curl as last resort...")
    try:
        import subprocess
        
        cmd = [
            'curl', '-X', 'POST', url,
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(payload),
            '-s'
        ]
        
        print(f"   Running: curl -X POST {url} ...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"   ✅ curl successful!")
            response_data = json.loads(result.stdout)
            print(f"   ✅ Got response: {json.dumps(response_data)[:100]}...")
            return response_data
        else:
            print(f"   ❌ curl failed with code {result.returncode}")
            print(f"   stderr: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ curl failed: {type(e).__name__}: {e}")
    
    # All methods failed
    print("\n❌ ALL METHODS FAILED TO REACH BACKEND")
    print("="*70)
    
    return {"error": "Could not reach backend with any method"}




def query_backend(query_text: str) -> Dict[str, Any]:
    """Query backend - try multiple methods if needed"""
    
    # First try urllib
    import urllib.request
    url = "http://localhost:8001/query"
    data = json.dumps({"query": query_text}).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        st.error(f"Query failed: {e}")
        return {"error": str(e)}

def main():
    st.set_page_config(
        page_title="Air Quality Chat (Bypass)", 
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Air Quality Chat - Webhook Bypass Edition")
    st.caption(f"Using {BYPASS_METHOD} method to avoid webhook interception")
    
    # Initialize
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'workflow_state' not in st.session_state:
        st.session_state.workflow_state = None
    if 'waiting_for_selection' not in st.session_state:
        st.session_state.waiting_for_selection = False
    
    # Chat display
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])
            
            # Handle disambiguation in message
            if message.get('show_locations'):
                locations = message.get('locations', [])
                for idx, loc in enumerate(locations):
                    if st.button(
                        f"📍 {loc.get('display_name', loc.get('name'))}",
                        key=f"msg_loc_{idx}_{id(message)}"
                    ):
                        with st.spinner('Fetching PM2.5 data...'):
                            result = select_backend(st.session_state.workflow_state, idx)
                            
                            if 'error' in result:
                                st.error(f"Error: {result['error']}")
                            else:
                                data = result.get('data', {})
                                response = data.get('formatted_response', 'No response')
                                st.session_state.messages.append({
                                    'role': 'assistant',
                                    'content': response
                                })
                                st.session_state.waiting_for_selection = False
                                st.session_state.workflow_state = None
                                st.rerun()
    
    # Chat input
    if prompt := st.chat_input("Ask about PM2.5..."):
        st.session_state.messages.append({'role': 'user', 'content': prompt})
        
        with st.spinner('Processing...'):
            result = query_backend(prompt)
            
            if 'error' in result:
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': f"❌ Error: {result['error']}"
                })
            else:
                state = result.get('state')
                data = result.get('data', {})
                
                if state and state.get('waiting_for_user'):
                    # Disambiguation needed
                    locations = state.get('locations', [])
                    st.session_state.workflow_state = state
                    st.session_state.waiting_for_selection = True
                    
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': f"Found {len(locations)} locations. Select one:",
                        'show_locations': True,
                        'locations': locations
                    })
                else:
                    # Direct response
                    response = data.get('formatted_response', 'No response')
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': response
                    })
        
        st.rerun()
    
    # Sidebar info
    with st.sidebar:
        st.header("🔧 Debug Info")
        st.write(f"Messages: {len(st.session_state.messages)}")
        st.write(f"Waiting: {st.session_state.waiting_for_selection}")
        
        if st.button("Test Backend"):
            try:
                import urllib.request
                with urllib.request.urlopen("http://localhost:8001/health", timeout=2) as response:
                    health = json.loads(response.read().decode('utf-8'))
                    st.success(f"✅ Backend OK: {health}")
            except Exception as e:
                st.error(f"❌ Backend error: {e}")
        
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.session_state.workflow_state = None
            st.session_state.waiting_for_selection = False
            st.rerun()
        
        st.divider()
        st.caption("This version bypasses webhook interception")

if __name__ == "__main__":
    main()
