# src/graphs/query_router.py
from typing import Dict, Any, Optional
import asyncio

class QueryRouter:
    """Routes queries through appropriate agents with disambiguation support"""
    
    def __init__(self, location_agent, disambiguation_agent, data_agents):
        self.location_agent = location_agent
        self.disambiguation_agent = disambiguation_agent
        self.data_agents = data_agents
    
    async def route_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Main routing logic"""
        
        # Step 1: Extract location if present
        location_results = await self.location_agent.extract_locations(query)
        
        # Step 2: Check if disambiguation needed
        disambiguation_check = await self.disambiguation_agent.check_disambiguation_needed(
            location_results
        )
        
        if disambiguation_check["needs_disambiguation"]:
            return {
                "needs_disambiguation": True,
                "disambiguation_options": disambiguation_check["options"],
                "original_query": query
            }
        
        # Step 3: Process query with selected/single location
        selected_location = disambiguation_check.get("selected")
        
        # Step 4: Determine query type and route to appropriate agent
        query_type = self._determine_query_type(query)
        
        # Step 5: Get data from appropriate agent
        data = await self.data_agents[query_type].process(
            query, 
            location=selected_location,
            context=context
        )
        
        # Step 6: Format response
        response = ResponseFormatter().format_response(
            query_type,
            data,
            metadata={
                "location": selected_location,
                "query_type": query_type,
                "confidence": disambiguation_check.get("confidence", 1.0)
            }
        )
        
        return response
    
    def _determine_query_type(self, query: str) -> str:
        """Determine the type of query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['current', 'now', 'latest', 'present']):
            return 'current_reading'
        elif any(word in query_lower for word in ['trend', 'history', 'past', 'last']):
            return 'time_series'
        elif any(word in query_lower for word in ['compare', 'versus', 'vs', 'between']):
            return 'comparison'
        elif any(word in query_lower for word in ['hotspot', 'worst', 'polluted']):
            return 'hotspot'
        elif any(word in query_lower for word in ['forecast', 'predict', 'tomorrow', 'will']):
            return 'forecast'
        
        return 'current_reading'  # default