# src/ui/streamlit_pm_query.py
import streamlit as st
import asyncio
from src.graphs.disambiguation_workflow import DisambiguationWorkflow
from src.agents.location_resolver import LocationResolverAgent
from src.agents.pm_data_agent import PMDataAgent
from src.utils.database import DatabaseConnection

async def initialize_agents():
    """Initialize all agents with database connection"""
    db = DatabaseConnection()
    await db.connect()
    
    location_agent = LocationResolverAgent(db)
    pm_agent = PMDataAgent(db)
    workflow = DisambiguationWorkflow(location_agent, pm_agent)
    
    return workflow, db

def main():
    st.title("🌍 Air Quality Query System")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "workflow_state" not in st.session_state:
        st.session_state.workflow_state = None
    if "waiting_for_selection" not in st.session_state:
        st.session_state.waiting_for_selection = False
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Show disambiguation options if waiting
    if st.session_state.waiting_for_selection and st.session_state.workflow_state:
        st.info("Please select which location you meant:")
        
        options = st.session_state.workflow_state.get("disambiguation_options", [])
        
        for option in options:
            if st.button(option["display"], key=option["id"]):
                # User selected an option
                workflow, db = asyncio.run(initialize_agents())
                
                # Resume workflow with selection
                final_state = asyncio.run(
                    workflow.resume_with_selection(
                        st.session_state.workflow_state,
                        option
                    )
                )
                
                # Show response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_state["final_response"]
                })
                
                # Clear waiting state
                st.session_state.waiting_for_selection = False
                st.session_state.workflow_state = None
                
                st.rerun()
    
    # Chat input
    if query := st.chat_input("Ask about PM levels..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Process query
        workflow, db = asyncio.run(initialize_agents())
        
        # Run workflow
        state = asyncio.run(workflow.run_until_disambiguation(query))
        
        if state.get("waiting_for_user"):
            # Need disambiguation
            st.session_state.waiting_for_selection = True
            st.session_state.workflow_state = state
            st.session_state.messages.append({
                "role": "assistant",
                "content": "I found multiple matches for that location. Please select one:"
            })
        else:
            # Direct response
            st.session_state.messages.append({
                "role": "assistant",
                "content": state["final_response"]
            })
        
        st.rerun()

if __name__ == "__main__":
    main()