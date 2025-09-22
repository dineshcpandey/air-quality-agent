import streamlit as st
import requests
import json
from datetime import datetime
import plotly.express as px
import pandas as pd

# Page config
st.set_page_config(
    page_title="Air Quality Assistant",
    page_icon="🌍",
    layout="wide"
)

# Custom CSS for better chat UI
st.markdown("""
<style>
    .stChatMessage {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .metadata {
        font-size: 0.8em;
        color: #666;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    show_metadata = st.checkbox("Show Query Metadata", value=False)
    show_confidence = st.checkbox("Show Confidence Score", value=True)
    
    st.divider()
    
    st.header("📊 Quick Stats")
    if "query_count" not in st.session_state:
        st.session_state.query_count = 0
    st.metric("Queries Made", st.session_state.query_count)
    
    st.divider()
    
    # Example queries
    st.header("💡 Try These Queries")
    examples = [
        "What's the current PM2.5 in Delhi?",
        "Compare air quality between Delhi and Mumbai",
        "Show me pollution trends for last week",
        "Find hotspots in NCR region",
        "What's the AQI forecast for tomorrow?"
    ]
    
    for example in examples:
        if st.button(example, key=f"ex_{example[:10]}"):
            st.session_state.pending_query = example

# Main chat interface
st.title("🌍 Air Quality Q&A Assistant")
st.caption("Ask me anything about air quality in Indian cities!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Hello! I can help you with air quality information. Try asking about PM2.5 levels, AQI, or pollution trends in any Indian city.",
            "metadata": {}
        }
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show metadata if enabled
        if show_metadata and message.get("metadata"):
            with st.expander("Query Details"):
                st.json(message["metadata"])
        
        # Show confidence if enabled
        if show_confidence and message.get("metadata", {}).get("confidence"):
            conf = message["metadata"]["confidence"]
            color = "green" if conf > 0.8 else "orange" if conf > 0.5 else "red"
            st.caption(f"Confidence: :{color}[{conf:.0%}]")

# Handle pending query from sidebar
if "pending_query" in st.session_state:
    query = st.session_state.pending_query
    del st.session_state.pending_query
    
    # Process the query
    st.session_state.messages.append({"role": "user", "content": query})
    st.rerun()

# Chat input
if prompt := st.chat_input("Ask about air quality..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.query_count += 1
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your query..."):
            try:
                # Call your API
                response = requests.post(
                    "http://localhost:8000/query",
                    json={"query": prompt, "cache": True}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Display main response
                    st.markdown(data["data"]["formatted_response"])
                    
                    # Display any charts if data includes them
                    if "chart_data" in data["data"]:
                        df = pd.DataFrame(data["data"]["chart_data"])
                        fig = px.line(df, x="time", y="value", title="Trend")
                        st.plotly_chart(fig)
                    
                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": data["data"]["formatted_response"],
                        "metadata": data.get("query_metadata", {})
                    })
                else:
                    st.error("Failed to get response. Please try again.")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("Make sure the backend server is running on http://localhost:8000")
    
    st.rerun()

# Footer
st.divider()
st.caption("💡 Tip: Click example queries in the sidebar or type your own question about air quality!")