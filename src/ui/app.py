# src/ui/app.py
import streamlit as st
import asyncio
from src.graphs.pm_query_workflow import PMQueryWorkflow
from src.agents.location_resolver import LocationResolverAgent
from src.agents.pm_data_agent import PMDataAgent
from src.utils.database import DatabaseConnection

# Page config
st.set_page_config(
    page_title="Air Quality Assistant",
    page_icon="🌍",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_state" not in st.session_state:
    st.session_state.current_state = None
if "workflow" not in st.session_state:
    st.session_state.workflow = None
if "db" not in st.session_state:
    st.session_state.db = None

async def initialize_system():
    """Initialize database and agents"""
    if st.session_state.db is None:
        db = DatabaseConnection()
        await db.connect()
        st.session_state.db = db
        
        location_agent = LocationResolverAgent(db)
        pm_agent = PMDataAgent(db)
        workflow = PMQueryWorkflow(location_agent, pm_agent)
        st.session_state.workflow = workflow
    
    return st.session_state.workflow, st.session_state.db

def main():
    st.title("🌍 Air Quality Query System")
    st.caption("Ask about PM2.5 levels in any Indian location")
    
    # Sidebar with examples
    with st.sidebar:
        st.header("💡 Example Queries")
        examples = [
            "What is PM level in Araria?",
            "Show me PM2.5 in Delhi",
            "Current air quality in Mumbai",
            "PM levels in Bangalore"
        ]
        for example in examples:
            if st.button(example, key=f"ex_{example[:10]}"):
                st.session_state.pending_query = example
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Handle disambiguation if needed
    if st.session_state.current_state and st.session_state.current_state.get("waiting_for_user"):
        locations = st.session_state.current_state.get("locations", [])
        
        if locations:
            st.info("🤔 Multiple locations found. Please select one:")
            
            # Create columns for options
            cols = st.columns(min(len(locations), 3))
            
            for idx, location in enumerate(locations):
                col = cols[idx % 3]
                with col:
                    if st.button(
                        location["display_name"],
                        key=f"loc_{location['code']}_{location['level']}",
                        use_container_width=True
                    ):
                        # User selected this location
                        workflow, db = asyncio.run(initialize_system())
                        
                        # Continue with selection
                        final_state = asyncio.run(
                            workflow.continue_with_selection(
                                st.session_state.current_state,
                                idx
                            )
                        )
                        
                        # Add response
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": final_state["response"]
                        })
                        
                        # Clear state
                        st.session_state.current_state = None
                        st.rerun()
    
    # Handle pending query from sidebar
    if "pending_query" in st.session_state:
        query = st.session_state.pending_query
        del st.session_state.pending_query
        
        # Process as if user typed it
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Process query
        workflow, db = asyncio.run(initialize_system())
        state = asyncio.run(workflow.process_query(query))
        
        if state.get("waiting_for_user"):
            st.session_state.current_state = state
        else:
            st.session_state.messages.append({
                "role": "assistant",
                "content": state["response"]
            })
        
        st.rerun()
    
    # Chat input
    if query := st.chat_input("Ask about PM2.5 levels...", 
                              disabled=bool(st.session_state.current_state)):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Process query
        with st.spinner("Processing..."):
            workflow, db = asyncio.run(initialize_system())
            state = asyncio.run(workflow.process_query(query))
            
            if state.get("waiting_for_user"):
                # Need disambiguation
                st.session_state.current_state = state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "I found multiple locations matching your query:"
                })
            else:
                # Direct response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": state["response"]
                })
                st.session_state.current_state = None
        
        st.rerun()

if __name__ == "__main__":
    main()