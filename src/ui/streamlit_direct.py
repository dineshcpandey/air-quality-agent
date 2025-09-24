# Simplified Air Quality Chat - No Webhook Issues
import streamlit as st
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'src'))

from utils.database import DatabaseConnection
from agents.location_resolver import LocationResolverAgent
from agents.pm_data_agent import PMDataAgent
from graphs.pm_query_workflow import PMQueryWorkflow


# Cache the workflow to avoid reconnecting
@st.cache_resource
def get_workflow():
    """Initialize and cache the workflow"""
    db = DatabaseConnection()
    asyncio.run(db.connect())
    
    location_agent = LocationResolverAgent(db)
    pm_agent = PMDataAgent(db)
    workflow = PMQueryWorkflow(location_agent, pm_agent)
    
    return workflow, db


def main():
    st.set_page_config(
        page_title="Air Quality Chat (Direct)", 
        page_icon="🌍",
        layout="wide"
    )
    
    st.title("🌍 Air Quality Chat - Direct Mode")
    st.caption("This version bypasses any webhook issues by running everything locally")
    
    # Initialize
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'pending_state' not in st.session_state:
        st.session_state.pending_state = None
    
    # Get workflow
    workflow, db = get_workflow()
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
    
    # Handle pending disambiguation
    if st.session_state.pending_state:
        state = st.session_state.pending_state
        locations = state.get('locations', [])
        
        if locations:
            st.info(f"📍 Found {len(locations)} locations. Please select one:")
            
            cols = st.columns(min(3, len(locations)))
            for idx, loc in enumerate(locations):
                col = cols[idx % 3]
                with col:
                    button_label = f"{loc.get('display_name', loc.get('name'))}"
                    if st.button(button_label, key=f"loc_{idx}", use_container_width=True):
                        # Process selection directly
                        with st.spinner('Fetching PM2.5 data...'):
                            final_state = asyncio.run(
                                workflow.continue_with_selection(state, idx)
                            )
                            
                            if final_state.get('response'):
                                st.session_state.messages.append({
                                    'role': 'assistant',
                                    'content': final_state['response']
                                })
                                
                                # Show raw data if available
                                if final_state.get('pm_data'):
                                    with st.expander("📊 Raw PM Data"):
                                        st.json(final_state['pm_data'])
                            else:
                                st.session_state.messages.append({
                                    'role': 'assistant',
                                    'content': f"❌ Error: {final_state.get('error', 'No data received')}"
                                })
                            
                            # Clear pending state
                            st.session_state.pending_state = None
                            st.rerun()
    
    # Chat input
    if prompt := st.chat_input("Ask about PM2.5 (e.g., 'What is PM2.5 in Delhi?')"):
        # Add user message
        st.session_state.messages.append({'role': 'user', 'content': prompt})
        
        # Process query
        with st.spinner('Processing...'):
            state = asyncio.run(workflow.process_query(prompt))
            
            # Debug info
            st.sidebar.write("Debug Info:")
            st.sidebar.write(f"- Waiting for user: {state.get('waiting_for_user')}")
            st.sidebar.write(f"- Locations: {len(state.get('locations', []))}")
            st.sidebar.write(f"- Has response: {bool(state.get('response'))}")
            st.sidebar.write(f"- Has error: {state.get('error')}")
            
            if state.get('waiting_for_user'):
                # Need disambiguation
                st.session_state.pending_state = state
                locations = state.get('locations', [])
                
                location_list = "\n".join([
                    f"{i+1}. {loc.get('display_name', loc.get('name'))}"
                    for i, loc in enumerate(locations)
                ])
                
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': f"I found {len(locations)} matching locations:\n\n{location_list}\n\nPlease select one above."
                })
            elif state.get('response'):
                # Direct response
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': state['response']
                })
                
                # Show raw data if available
                if state.get('pm_data'):
                    with st.expander("📊 Raw PM Data"):
                        st.json(state['pm_data'])
            else:
                # Error
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': f"❌ {state.get('error', 'Unknown error occurred')}"
                })
        
        st.rerun()
    
    # Sidebar with info
    with st.sidebar:
        st.header("ℹ️ About")
        st.write("This is a simplified version that runs everything locally without external API calls.")
        st.write("No webhooks, no external backends - just direct database queries.")
        
        st.divider()
        
        st.header("🔧 Status")
        st.success("✅ Database Connected")
        st.success("✅ Workflow Ready")
        st.info("💡 Everything runs in-process")
        
        st.divider()
        
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.pending_state = None
            st.rerun()


if __name__ == "__main__":
    main()
