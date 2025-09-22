# src/ui/streamlit_chat.py
import streamlit as st
import asyncio
from src.graphs.query_graph import QueryGraph

st.title("🌍 Air Quality Q&A Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask about air quality..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Process query through your agent system
    with st.spinner("Analyzing..."):
        response = asyncio.run(process_query(prompt))
    
    # Add assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})