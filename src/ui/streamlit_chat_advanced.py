# src/ui/streamlit_chat_advanced.py
import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, Any, List, Optional

# Import your agents
from src.agents.location_resolver import LocationResolverAgent
from src.agents.disambiguation_agent import DisambiguationAgent
from src.graphs.query_graph import QueryGraph
from src.utils.database import DatabaseConnection

# Page configuration
st.set_page_config(
    page_title="Air Quality Q&A Assistant",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .disambiguation-button {
        margin: 5px;
        padding: 10px;
        border-radius: 5px;
        background-color: #f0f2f6;
        border: 1px solid #d0d2d6;
    }
    .metric-card {
        padding: 15px;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .chat-metadata {
        font-size: 0.8em;
        color: #666;
        padding: 5px;
        background-color: #f9f9f9;
        border-radius: 5px;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

class ChatInterface:
    def __init__(self):
        self.initialize_session_state()
        self.setup_agents()
    
    def initialize_session_state(self):
        """Initialize all session state variables"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        if "waiting_for_disambiguation" not in st.session_state:
            st.session_state.waiting_for_disambiguation = False
        
        if "disambiguation_context" not in st.session_state:
            st.session_state.disambiguation_context = {}
        
        if "query_count" not in st.session_state:
            st.session_state.query_count = 0
        
        if "chart_data_cache" not in st.session_state:
            st.session_state.chart_data_cache = {}
    
    def setup_agents(self):
        """Initialize agent system"""
        # This would be initialized with your actual database connection
        self.db = None  # DatabaseConnection() 
        self.location_agent = None  # LocationResolverAgent(self.db)
        self.disambiguation_agent = DisambiguationAgent(self.db)
        self.query_graph = None  # QueryGraph(self.db)
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process user query through agent system"""
        
        # Mock response for demonstration
        # Replace with actual agent calls
        
        # Check if query needs location resolution
        if any(word in query.lower() for word in ['delhi', 'mumbai', 'araria', 'bangalore']):
            # Simulate location resolution
            if 'araria' in query.lower():
                # Return disambiguation needed
                return {
                    "needs_disambiguation": True,
                    "disambiguation_options": [
                        {
                            "id": "araria_district",
                            "display_text": "📍 Araria District Average (Bihar)",
                            "metadata": {"level": "district", "area": "3830 km²"}
                        },
                        {
                            "id": "araria_hq",
                            "display_text": "🏛️ Araria City (District HQ)",
                            "metadata": {"level": "city", "population": "86,000"}
                        },
                        {
                            "id": "araria_station",
                            "display_text": "📡 Araria Monitoring Station",
                            "metadata": {"level": "sensor", "station_id": "BR_AR_001"}
                        }
                    ],
                    "original_query": query
                }
        
        # Check for trend queries
        if any(word in query.lower() for word in ['trend', 'last', 'week', 'month', 'history']):
            return self.generate_trend_response(query)
        
        # Default response
        return self.generate_simple_response(query)
    
    def generate_trend_response(self, query: str) -> Dict[str, Any]:
        """Generate response with trend chart"""
        # Generate sample data
        dates = pd.date_range(end=datetime.now(), periods=7, freq='D')
        pm25_values = [145, 162, 178, 156, 143, 138, 152]
        
        df = pd.DataFrame({
            'date': dates,
            'PM2.5': pm25_values,
            'AQI': [v * 0.8 for v in pm25_values]  # Simplified AQI calculation
        })
        
        return {
            "text_response": f"Here's the PM2.5 trend for the last week. The average PM2.5 was {sum(pm25_values)/len(pm25_values):.1f} µg/m³.",
            "has_chart": True,
            "chart_data": df,
            "chart_type": "trend",
            "metadata": {
                "data_points": len(df),
                "time_range": "7 days",
                "source": "historical_data"
            }
        }
    
    def generate_simple_response(self, query: str) -> Dict[str, Any]:
        """Generate simple text response"""
        return {
            "text_response": f"The current PM2.5 level in Delhi is 156 µg/m³ (Unhealthy). AQI is 206.",
            "has_chart": False,
            "metadata": {
                "confidence": 0.95,
                "source": "current_readings",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def render_chart(self, data: pd.DataFrame, chart_type: str):
        """Render different types of charts based on data"""
        
        if chart_type == "trend":
            # Create line chart with both PM2.5 and AQI
            fig = go.Figure()
            
            # Add PM2.5 trace
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=data['PM2.5'],
                mode='lines+markers',
                name='PM2.5 (µg/m³)',
                line=dict(color='#FF6B6B', width=3),
                marker=dict(size=8)
            ))
            
            # Add AQI trace on secondary y-axis
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=data['AQI'],
                mode='lines+markers',
                name='AQI',
                line=dict(color='#4ECDC4', width=3, dash='dash'),
                marker=dict(size=8),
                yaxis='y2'
            ))
            
            # Update layout
            fig.update_layout(
                title="Air Quality Trend - Last 7 Days",
                xaxis_title="Date",
                yaxis_title="PM2.5 (µg/m³)",
                yaxis2=dict(
                    title="AQI",
                    overlaying='y',
                    side='right'
                ),
                hovermode='x unified',
                template="plotly_white",
                height=400
            )
            
            # Add color bands for AQI categories
            fig.add_hrect(y0=0, y1=50, fillcolor="green", opacity=0.1, 
                         annotation_text="Good", annotation_position="right")
            fig.add_hrect(y0=51, y1=100, fillcolor="yellow", opacity=0.1, 
                         annotation_text="Moderate", annotation_position="right")
            fig.add_hrect(y0=101, y1=200, fillcolor="orange", opacity=0.1, 
                         annotation_text="Unhealthy", annotation_position="right")
            fig.add_hrect(y0=201, y1=300, fillcolor="red", opacity=0.1, 
                         annotation_text="Very Unhealthy", annotation_position="right")
            
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "comparison":
            # Bar chart for location comparison
            fig = px.bar(data, x='location', y='value', color='metric',
                        title="Air Quality Comparison",
                        barmode='group',
                        color_discrete_map={'PM2.5': '#FF6B6B', 'AQI': '#4ECDC4'})
            st.plotly_chart(fig, use_container_width=True)
    
    def render_disambiguation_options(self, options: List[Dict]):
        """Render disambiguation buttons"""
        st.info("🤔 I found multiple matches. Which one did you mean?")
        
        cols = st.columns(len(options) if len(options) <= 3 else 3)
        
        for idx, option in enumerate(options):
            col = cols[idx % 3]
            with col:
                if st.button(
                    option["display_text"],
                    key=f"disamb_{option['id']}",
                    help=f"Level: {option['metadata'].get('level', 'Unknown')}"
                ):
                    # Process with selected option
                    self.handle_disambiguation_selection(option)
    
    def handle_disambiguation_selection(self, selected_option: Dict):
        """Handle user's disambiguation choice"""
        st.session_state.waiting_for_disambiguation = False
        
        # Process original query with selected context
        original_query = st.session_state.disambiguation_context.get("original_query", "")
        
        # Add assistant message explaining the selection
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Got it! Fetching data for {selected_option['display_text']}...",
            "metadata": {"disambiguation_resolved": True}
        })
        
        # Clear disambiguation context
        st.session_state.disambiguation_context = {}
        
        # Rerun to process the query
        st.rerun()
    
    def render_sidebar(self):
        """Render sidebar with controls and information"""
        with st.sidebar:
            st.header("⚙️ Settings")
            
            # Display options
            show_confidence = st.checkbox("Show Confidence Scores", value=True)
            show_metadata = st.checkbox("Show Technical Details", value=False)
            auto_refresh = st.checkbox("Auto-refresh Current Data", value=False)
            
            if auto_refresh:
                refresh_interval = st.slider("Refresh Interval (seconds)", 10, 60, 30)
            
            st.divider()
            
            # Quick stats
            st.header("📊 Session Stats")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Queries", st.session_state.query_count)
            with col2:
                accuracy = 0.92  # Mock value
                st.metric("Accuracy", f"{accuracy:.0%}")
            
            st.divider()
            
            # Predefined queries
            st.header("💡 Quick Queries")
            
            query_categories = {
                "📍 Current Levels": [
                    "What's the PM2.5 in Delhi?",
                    "Current AQI in Mumbai",
                    "Air quality in Bangalore"
                ],
                "📈 Trends": [
                    "Show PM2.5 trend for last week",
                    "Monthly air quality pattern",
                    "Compare today with yesterday"
                ],
                "🔥 Hotspots": [
                    "Find pollution hotspots in NCR",
                    "Worst affected areas today",
                    "Areas exceeding safe limits"
                ],
                "🆚 Comparisons": [
                    "Compare Delhi and Mumbai",
                    "Best air quality cities today",
                    "Morning vs evening levels"
                ]
            }
            
            for category, queries in query_categories.items():
                with st.expander(category):
                    for query in queries:
                        if st.button(query, key=f"quick_{query[:10]}"):
                            st.session_state.pending_query = query
                            st.rerun()
            
            st.divider()
            
            # Data sources info
            st.header("📡 Data Sources")
            st.caption("Currently connected to:")
            st.text("• CPCB Sensors: 342")
            st.text("• Weather Stations: 45")
            st.text("• Satellite Data: Active")
            
            # Last update time
            st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    def render_chat(self):
        """Main chat interface"""
        st.title("🌍 Air Quality Q&A Assistant")
        st.caption("Ask me anything about air quality in Indian cities!")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show chart if present
                if message.get("chart_data") is not None and message.get("has_chart"):
                    self.render_chart(
                        message["chart_data"],
                        message.get("chart_type", "trend")
                    )
                
                # Show metadata if enabled
                if message.get("metadata") and st.session_state.get("show_metadata", False):
                    with st.expander("Technical Details"):
                        st.json(message["metadata"])
        
        # Show disambiguation options if waiting
        if st.session_state.waiting_for_disambiguation:
            options = st.session_state.disambiguation_context.get("options", [])
            if options:
                self.render_disambiguation_options(options)
        
        # Chat input
        if prompt := st.chat_input("Ask about air quality...", 
                                   disabled=st.session_state.waiting_for_disambiguation):
            
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.query_count += 1
            
            # Process query
            with st.spinner("Analyzing your query..."):
                # Get response from agent system
                response = asyncio.run(self.process_query(prompt))
                
                # Check if disambiguation is needed
                if response.get("needs_disambiguation"):
                    st.session_state.waiting_for_disambiguation = True
                    st.session_state.disambiguation_context = {
                        "options": response["disambiguation_options"],
                        "original_query": prompt
                    }
                    
                    # Add assistant message asking for clarification
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "I need a bit more information to answer your query accurately.",
                        "metadata": {"disambiguation": True}
                    })
                else:
                    # Add response to messages
                    message = {
                        "role": "assistant",
                        "content": response["text_response"],
                        "metadata": response.get("metadata", {})
                    }
                    
                    # Add chart data if present
                    if response.get("has_chart"):
                        message["has_chart"] = True
                        message["chart_data"] = response["chart_data"]
                        message["chart_type"] = response.get("chart_type", "trend")
                    
                    st.session_state.messages.append(message)
            
            st.rerun()
    
    def run(self):
        """Main application loop"""
        self.render_sidebar()
        self.render_chat()

# Main execution
if __name__ == "__main__":
    app = ChatInterface()
    app.run()