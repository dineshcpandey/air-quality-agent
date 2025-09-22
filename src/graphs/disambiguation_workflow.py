# src/graphs/disambiguation_workflow.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Dict

class QueryState(TypedDict):
    # Input
    user_query: str
    
    # Location resolution
    location_query: str
    location_results: List[Dict]
    needs_disambiguation: bool
    selected_location: Optional[Dict]
    
    # User interaction
    waiting_for_user: bool
    disambiguation_options: List[Dict]
    
    # Data fetching
    pm_data: Optional[Dict]
    
    # Final response
    final_response: str
    error: Optional[str]

class DisambiguationWorkflow:
    def __init__(self, location_agent, pm_agent):
        self.location_agent = location_agent
        self.pm_agent = pm_agent
        self.workflow = self._build_graph()
    
    def _build_graph(self):
        workflow = StateGraph(QueryState)
        
        # Add nodes
        workflow.add_node("extract_location", self.extract_location_from_query)
        workflow.add_node("resolve_location", self.resolve_location)
        workflow.add_node("check_disambiguation", self.check_disambiguation)
        workflow.add_node("wait_for_user", self.wait_for_user_input)
        workflow.add_node("fetch_pm_data", self.fetch_pm_data)
        workflow.add_node("format_response", self.format_response)
        
        # Define flow
        workflow.set_entry_point("extract_location")
        workflow.add_edge("extract_location", "resolve_location")
        workflow.add_edge("resolve_location", "check_disambiguation")
        
        # Conditional edge based on disambiguation
        workflow.add_conditional_edges(
            "check_disambiguation",
            self.route_after_disambiguation,
            {
                "need_user_input": "wait_for_user",
                "proceed": "fetch_pm_data"
            }
        )
        
        workflow.add_edge("wait_for_user", END)  # Pause for user
        workflow.add_edge("fetch_pm_data", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    async def extract_location_from_query(self, state: QueryState) -> QueryState:
        """Extract location name from user query"""
        query = state["user_query"]
        # Simple extraction - enhance with NLP if needed
        location_name = "araria"  # Extract this properly
        
        return {
            **state,
            "location_query": location_name
        }
    
    async def resolve_location(self, state: QueryState) -> QueryState:
        """Call location agent"""
        result = await self.location_agent.run({
            "location_query": state["location_query"]
        })
        
        return {
            **state,
            "location_results": result.get("locations", []),
            "needs_disambiguation": result.get("needs_disambiguation", False)
        }
    
    async def check_disambiguation(self, state: QueryState) -> QueryState:
        """Check if disambiguation is needed"""
        if state["needs_disambiguation"] and len(state["location_results"]) > 1:
            # Prepare options for user
            options = []
            for loc in state["location_results"]:
                options.append({
                    "id": f"{loc.get('code')}_{loc.get('level')}",
                    "display": f"{loc.get('name')} ({loc.get('level')}) - {loc.get('state_name')}",
                    "data": loc
                })
            
            return {
                **state,
                "waiting_for_user": True,
                "disambiguation_options": options
            }
        else:
            # Single result or no disambiguation needed
            return {
                **state,
                "selected_location": state["location_results"][0] if state["location_results"] else None
            }
    
    def route_after_disambiguation(self, state: QueryState) -> str:
        """Routing logic after checking disambiguation"""
        if state.get("waiting_for_user"):
            return "need_user_input"
        return "proceed"
    
    async def wait_for_user_input(self, state: QueryState) -> QueryState:
        """This node signals we need user input"""
        # The workflow will pause here
        # Streamlit will show options and resume with selected location
        return state
    
    async def fetch_pm_data(self, state: QueryState) -> QueryState:
        """Fetch PM data for selected location"""
        if not state.get("selected_location"):
            return {**state, "error": "No location selected"}
        
        result = await self.pm_agent.run({
            "location": state["selected_location"],
            "metric": "pm25"
        })
        
        return {
            **state,
            "pm_data": result.get("data")
        }
    
    async def format_response(self, state: QueryState) -> QueryState:
        """Format final response"""
        if state.get("error"):
            response = f"Error: {state['error']}"
        elif state.get("pm_data"):
            data = state["pm_data"]
            loc = state["selected_location"]
            response = f"PM2.5 level in {loc['name']} ({loc['level']}): {data.get('avg_value', 'N/A')} µg/m³"
        else:
            response = "Could not fetch PM data"
        
        return {
            **state,
            "final_response": response
        }
    
    async def run_until_disambiguation(self, query: str) -> QueryState:
        """Run workflow until user input needed"""
        initial_state = {
            "user_query": query,
            "waiting_for_user": False
        }
        
        result = await self.workflow.ainvoke(initial_state)
        return result
    
    async def resume_with_selection(self, state: QueryState, selected_option: Dict) -> QueryState:
        """Resume workflow after user selection"""
        # Update state with selection
        state["selected_location"] = selected_option["data"]
        state["waiting_for_user"] = False
        
        # Continue from fetch_pm_data
        result = await self.fetch_pm_data(state)
        result = await self.format_response(result)
        
        return result