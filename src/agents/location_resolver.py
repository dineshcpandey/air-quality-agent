# src/agents/location_resolver.py
import json
from typing import Dict, Any, List
from .agent_base import AgentBase

class LocationResolverAgent(AgentBase):
    def __init__(self, db_connection):
        super().__init__(name="LocationResolverAgent")
        self.db = db_connection
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls gis.search_location_json and returns all matches
        """
        query_text = input_data.get("location_query", "").strip()
        self.log(f"Searching for location: '{query_text}'")
        
        try:
            # Call your search function
            result = await self.db.execute_query(
                "SELECT gis.search_location_json($1) as locations", 
                [query_text]
            )
            
            if not result or not result[0]['locations']:
                return {
                    "success": False,
                    "locations": [],
                    "error": "No locations found"
                }
            
            # Parse JSON result
            locations = result[0]['locations']
            if isinstance(locations, str):
                locations = json.loads(locations)
            
            # Format for disambiguation
            formatted_locations = []
            for loc in locations:
                formatted_locations.append({
                    "code": loc.get("code"),
                    "level": loc.get("level"),
                    "name": loc.get("name"),
                    "display_name": self._format_display_name(loc),
                    "state": loc.get("state_name"),
                    "district": loc.get("district_name"),
                    "parent": loc.get("parent_name")
                })
            
            return {
                "success": True,
                "locations": formatted_locations,
                "count": len(formatted_locations),
                "needs_disambiguation": len(formatted_locations) > 1
            }
            
        except Exception as e:
            return self.handle_error(e, {"location_query": query_text})
    
    def _format_display_name(self, location: Dict) -> str:
        """Create user-friendly display name"""
        level = location.get('level', '')
        name = location.get('name', '')
        
        level_display = {
            'district': '📍 District',
            'district_hq': '🏛️ City (District HQ)',
            'sub_district': '📌 Sub-district',
            'ward': '🏘️ Ward'
        }.get(level, '📍 Location')
        
        parts = [f"{level_display}: {name}"]
        
        if location.get('district_name') and level != 'district':
            parts.append(f"District: {location['district_name']}")
        if location.get('state_name'):
            parts.append(f"State: {location['state_name']}")
            
        return " | ".join(parts)