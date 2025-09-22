# src/graphs/pm_query_workflow.py
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PMQueryState(TypedDict):
    # User input
    user_query: str
    
    # Location resolution
    location_search_term: str
    locations: List[Dict]
    needs_disambiguation: bool
    selected_location: Optional[Dict]
    
    # PM data
    pm_data: Optional[Dict]
    
    # Response
    response: str
    error: Optional[str]
    
    # Control flow
    waiting_for_user: bool

class PMQueryWorkflow:
    def __init__(self, location_agent, pm_agent):
        self.location_agent = location_agent
        self.pm_agent = pm_agent
        self.workflow = self._build_graph()
    
    def _build_graph(self):
        workflow = StateGraph(PMQueryState)
        
        # Add nodes
        workflow.add_node("parse_query", self.parse_query)
        workflow.add_node("search_location", self.search_location)
        workflow.add_node("handle_disambiguation", self.handle_disambiguation)
        workflow.add_node("fetch_pm_data", self.fetch_pm_data)
        workflow.add_node("format_response", self.format_response)
        
        # Define flow
        workflow.set_entry_point("parse_query")
        workflow.add_edge("parse_query", "search_location")
        workflow.add_edge("search_location", "handle_disambiguation")
        
        # Conditional routing after disambiguation check
        workflow.add_conditional_edges(
            "handle_disambiguation",
            lambda x: "wait" if x.get("waiting_for_user") else "continue",
            {
                "wait": END,  # Stop and wait for user
                "continue": "fetch_pm_data"
            }
        )
        
        workflow.add_edge("fetch_pm_data", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    async def parse_query(self, state: PMQueryState) -> PMQueryState:
        """Extract location from query"""
        query = state["user_query"].lower()
        
        # Simple extraction - enhance this with NLP later
        # For "What is PM level in Araria", extract "Araria"
        location_term = ""
        
        # Simple keyword extraction
        if " in " in query:
            location_term = query.split(" in ")[-1].strip()
        elif " at " in query:
            location_term = query.split(" at ")[-1].strip()
        elif " for " in query:
            location_term = query.split(" for ")[-1].strip()
        else:
            # Try to find a known location name in the query
            words = query.split()
            # You could maintain a list of known locations to check against
            location_term = words[-1] if words else ""
        
        return {
            **state,
            "location_search_term": location_term
        }
    
    async def search_location(self, state: PMQueryState) -> PMQueryState:
        """Search for location using location agent"""
        result = await self.location_agent.run({
            "location_query": state["location_search_term"]
        })
        
        return {
            **state,
            "locations": result.get("locations", []),
            "needs_disambiguation": result.get("needs_disambiguation", False)
        }
    
    async def handle_disambiguation(self, state: PMQueryState) -> PMQueryState:
        """Check if we need user input for disambiguation"""
        if state["needs_disambiguation"] and len(state["locations"]) > 1:
            return {
                **state,
                "waiting_for_user": True
            }
        elif state["locations"]:
            # Single location found, use it
            return {
                **state,
                "selected_location": state["locations"][0],
                "waiting_for_user": False
            }
        else:
            # No locations found
            return {
                **state,
                "error": "No location found",
                "waiting_for_user": False
            }
    
    async def fetch_pm_data(self, state: PMQueryState) -> PMQueryState:
        """Fetch PM2.5 data for selected location"""
        if not state.get("selected_location"):
            return {**state, "error": "No location selected"}
        
        location = state["selected_location"]
        
        result = await self.pm_agent.run({
            "location_code": location["code"],
            "location_level": location["level"],
            "location_name": location["name"]
        })
        
        return {
            **state,
            "pm_data": result if result.get("success") else None,
            "error": result.get("error") if not result.get("success") else None
        }
    
    async def format_response(self, state: PMQueryState) -> PMQueryState:
        """Format the final response"""
        if state.get("error"):
            response = f"❌ {state['error']}"
        elif state.get("pm_data"):
            data = state["pm_data"]
            location = state["selected_location"]
            
            # Get PM2.5 value and format it
            pm_value = data.get("pm25_value")
            
            # Determine air quality category
            category, emoji = self._get_air_quality_category(pm_value)
            
            response = f"{emoji} **PM2.5 level in {location['name']}**\n\n"
            response += f"📊 **Current Level:** {pm_value:.1f} µg/m³\n"
            response += f"📍 **Location Type:** {location['level'].replace('_', ' ').title()}\n"
            response += f"🏷️ **Category:** {category}\n"
            
            if data.get("timestamp"):
                response += f"🕐 **Last Updated:** {data['timestamp']}\n"
            
            if data.get("station_count"):
                response += f"📡 **Data from:** {data['station_count']} stations\n"
            
            # Add health advisory
            if category in ["Poor", "Very Poor", "Severe"]:
                response += f"\n⚠️ **Health Advisory:** {self._get_health_advisory(category)}"
        else:
            response = "Could not fetch PM2.5 data"
        
        return {
            **state,
            "response": response
        }
    
    def _get_air_quality_category(self, pm25_value: float) -> tuple:
        """Determine AQI category from PM2.5 value"""
        if pm25_value is None:
            return "Unknown", "❓"
        elif pm25_value <= 30:
            return "Good", "🟢"
        elif pm25_value <= 60:
            return "Satisfactory", "🟡" 
        elif pm25_value <= 90:
            return "Moderate", "🟠"
        elif pm25_value <= 120:
            return "Poor", "🔴"
        elif pm25_value <= 250:
            return "Very Poor", "🟣"
        else:
            return "Severe", "🟤"
    
    def _get_health_advisory(self, category: str) -> str:
        advisories = {
            "Poor": "Sensitive groups should reduce prolonged outdoor activities.",
            "Very Poor": "Avoid outdoor activities. Use masks if going outside.",
            "Severe": "Stay indoors. Avoid all outdoor activities."
        }
        return advisories.get(category, "")
    
    async def process_query(self, query: str) -> PMQueryState:
        """Process a new query"""
        initial_state = PMQueryState(
            user_query=query,
            waiting_for_user=False,
            locations=[],
            needs_disambiguation=False,
            selected_location=None,
            pm_data=None,
            response="",
            error=None,
            location_search_term=""
        )
        
        return await self.workflow.ainvoke(initial_state)
    
    async def continue_with_selection(self, state: PMQueryState, selected_idx: int) -> PMQueryState:
        """Continue workflow after user selects a location"""
        # Set selected location
        state["selected_location"] = state["locations"][selected_idx]
        state["waiting_for_user"] = False
        
        # Continue workflow from fetch_pm_data
        state = await self.fetch_pm_data(state)
        state = await self.format_response(state)
        
        return state