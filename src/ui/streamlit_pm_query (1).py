# src/ui/streamlit_pm_query.py
import streamlit as st
import requests
import json
import os
from typing import Any, Dict, List
import time

# Backend URL configuration - MUST be local
# Check multiple sources for backend URL
def get_backend_url():
    """Get backend URL with validation"""
    # Try streamlit secrets first
    try:
        url = st.secrets.get('backend_url', None)
        if url and not url.startswith(('http://localhost', 'http://127.0.0.1', 'http://0.0.0.0')):
            print(f"⚠️ WARNING: Non-local backend URL in secrets: {url}")
            url = None
    except:
        url = None
    
    # Check environment variable
    if not url:
        url = os.environ.get('BACKEND_URL', None)
        if url and not url.startswith(('http://localhost', 'http://127.0.0.1', 'http://0.0.0.0')):
            print(f"⚠️ WARNING: Non-local backend URL in environment: {url}")
            url = None
    
    # Use default local URL
    if not url:
        url = 'http://localhost:8001'
    
    # Safety check - prevent webhook URLs
    if 'webhook' in url.lower() or 'fivetran' in url.lower():
        print(f"❌ ERROR: Webhook URL detected: {url}")
        print("❌ Forcing local backend URL")
        url = 'http://localhost:8001'
    
    print(f"✅ Using backend URL: {url}")
    return url

BACKEND_URL = get_backend_url()


def query_backend(query_text: str) -> Dict[str, Any]:
    """Send query to backend API"""
    url = f"{BACKEND_URL}/query"
    print(f"[DEBUG] Calling backend: {url}")
    print(f"[DEBUG] Query: {query_text}")
    
    try:
        resp = requests.post(url, json={"query": query_text}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"Backend connection error: {e}")
        print(f"[ERROR] Backend call failed: {e}")
        return {"error": str(e)}


def select_backend(state: Dict[str, Any], selected_index: int) -> Dict[str, Any]:
    """Send selection to backend API"""
    url = f"{BACKEND_URL}/query/select"
    print(f"[DEBUG] Calling backend selection: {url}")
    print(f"[DEBUG] Selected index: {selected_index}")
    print(f"[DEBUG] Locations available: {len(state.get('locations', []))}")
    
    # Safety check the URL
    if 'webhook' in url.lower() or 'fivetran' in url.lower():
        print(f"❌ ERROR: Webhook URL detected in select_backend: {url}")
        st.error("Configuration error: Wrong backend URL detected. Please check settings.")
        return {"error": "Invalid backend URL configuration"}
    
    try:
        resp = requests.post(url, json={"state": state, "selected_index": selected_index}, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        print(f"[DEBUG] Selection response received successfully")
        return result
    except requests.HTTPError as e:
        try:
            detail = e.response.json()
        except:
            detail = e.response.text if hasattr(e, 'response') else str(e)
        print(f"[ERROR] Backend selection failed: {detail}")
        return {"error": f"Backend error ({e.response.status_code}): {detail}"}
    except requests.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return {"error": str(e)}


def _append_message(role: str, content: str, metadata: Dict = None):
    """Append message to chat history"""
    message = {"role": role, "content": content}
    if metadata:
        message["metadata"] = metadata
    st.session_state.messages.append(message)


def _show_raw_data(raw: Any):
    """Display raw data in an expander"""
    if raw is None:
        return
    with st.expander("📊 Show raw data"):
        st.json(raw)


def main():
    st.set_page_config(
        page_title="Air Quality Chat", 
        page_icon="🌍",
        layout="wide"
    )
    
    st.title("🌍 Air Quality Chat — PM2.5 Assistant")
    st.caption("Ask about PM2.5 levels in any location")

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I can help you check PM2.5 levels. Try asking:\n- 'What is the current PM2.5 in Delhi?'\n- 'Show me PM levels in Ambedkar Nagar'"
            }
        ]
    if 'workflow_state' not in st.session_state:
        st.session_state.workflow_state = None
    if 'waiting_for_selection' not in st.session_state:
        st.session_state.waiting_for_selection = False
    if 'last_error' not in st.session_state:
        st.session_state.last_error = None

    # Create layout
    chat_col, side_col = st.columns([3, 1])

    with chat_col:
        # Display chat history
        for message in st.session_state.messages:
            role = message.get('role', 'assistant')
            content = message.get('content', '')
            
            with st.chat_message(role):
                st.markdown(content)
                
                # If this message has disambiguation options, show them
                if message.get('metadata', {}).get('has_disambiguation'):
                    locations = message.get('metadata', {}).get('locations', [])
                    if locations and st.session_state.waiting_for_selection:
                        st.divider()
                        st.info("📍 Please select a location:")
                        
                        # Display location buttons
                        for idx, loc in enumerate(locations):
                            # Format button label
                            name = loc.get('display_name') or loc.get('name', f'Option {idx+1}')
                            level = loc.get('level', '')
                            state_name = loc.get('state', '')
                            
                            button_label = f"**{name}**"
                            details = []
                            if level:
                                details.append(f"Type: {level}")
                            if state_name:
                                details.append(f"State: {state_name}")
                            if details:
                                button_label += f"\n{' | '.join(details)}"
                            
                            # Create button
                            if st.button(
                                button_label, 
                                key=f"select_loc_{idx}_{time.time()}",
                                use_container_width=True
                            ):
                                # Process selection
                                with st.spinner('Fetching PM2.5 data...'):
                                    result = select_backend(st.session_state.workflow_state, idx)
                                    
                                    if 'error' in result:
                                        _append_message('assistant', f"❌ Error: {result['error']}")
                                    else:
                                        data = result.get('data', {})
                                        formatted = data.get('formatted_response')
                                        raw = data.get('raw_data')
                                        
                                        if formatted:
                                            _append_message('assistant', formatted)
                                            _show_raw_data(raw)
                                        else:
                                            _append_message('assistant', "No data received from backend")
                                    
                                    # Clear selection state
                                    st.session_state.waiting_for_selection = False
                                    st.session_state.workflow_state = None
                                    st.rerun()
                
                # Show raw data if present
                if message.get('metadata', {}).get('raw_data'):
                    _show_raw_data(message['metadata']['raw_data'])

        # Chat input (disabled when waiting for selection)
        user_input = st.chat_input(
            "Ask me: e.g. 'What is the PM2.5 in Delhi?'",
            disabled=st.session_state.waiting_for_selection
        )
        
        if user_input:
            # Add user message
            _append_message('user', user_input)
            
            # Process query
            with st.spinner('Searching...'):
                result = query_backend(user_input)
            
            if 'error' in result:
                _append_message('assistant', f"❌ Error: {result['error']}")
                st.rerun()
            
            # Debug logging
            print(f"\n[Streamlit] Query: {user_input}")
            print(f"[Streamlit] Backend response: {json.dumps(result, indent=2)[:500]}...")
            
            data = result.get('data', {}) or {}
            state = result.get('state')
            
            if state and state.get('waiting_for_user'):
                # Multiple locations found
                locations = state.get('locations', [])
                st.session_state.workflow_state = state
                st.session_state.waiting_for_selection = True
                
                # Create disambiguation message
                location_list = []
                for i, loc in enumerate(locations):
                    name = loc.get('display_name', loc.get('name', 'Unknown'))
                    location_list.append(f"{i+1}. {name}")
                
                disambiguation_text = f"I found **{len(locations)} locations** matching your query:\n\n"
                disambiguation_text += "\n".join(location_list)
                
                _append_message(
                    'assistant', 
                    disambiguation_text,
                    metadata={
                        'has_disambiguation': True,
                        'locations': locations
                    }
                )
            else:
                # Direct response
                formatted = data.get('formatted_response')
                raw = data.get('raw_data')
                
                if formatted:
                    _append_message(
                        'assistant', 
                        formatted,
                        metadata={'raw_data': raw} if raw else None
                    )
                else:
                    _append_message('assistant', "No response received from backend")
            
            st.rerun()

    with side_col:
        # Sidebar content
        st.header('ℹ️ Information')
        
        # Status indicator
        if st.session_state.waiting_for_selection:
            st.warning("⏳ Waiting for location selection")
        else:
            st.success("✅ Ready for queries")
        
        st.divider()
        
        # Help section
        st.subheader('📝 Tips')
        st.markdown("""
        - Ask about PM2.5 in any location
        - Examples:
          - "What is PM2.5 in Delhi?"
          - "Current PM levels in Mumbai"
          - "Show PM2.5 for Bangalore"
        - If multiple matches found, select from the list
        """)
        
        st.divider()
        
        # Debug information
        with st.expander("🔧 Debug Info"):
            st.text(f"Backend URL: {BACKEND_URL}")
            st.text(f"Messages: {len(st.session_state.messages)}")
            st.text(f"Waiting: {st.session_state.waiting_for_selection}")
            if st.session_state.workflow_state:
                locations = st.session_state.workflow_state.get('locations', [])
                st.text(f"Pending locations: {len(locations)}")
        
        st.divider()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Chat cleared. How can I help you check PM2.5 levels?"
                }
            ]
            st.session_state.workflow_state = None
            st.session_state.waiting_for_selection = False
            st.rerun()
        
        # Retry button if there's an error
        if st.session_state.last_error:
            if st.button("🔄 Retry Last Query", use_container_width=True):
                # Implement retry logic
                st.session_state.last_error = None
                st.rerun()


if __name__ == '__main__':
    main()
