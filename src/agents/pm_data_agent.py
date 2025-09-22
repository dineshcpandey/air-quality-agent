# src/agents/pm_data_agent.py
from typing import Dict, Any
from .agent_base import AgentBase

class PMDataAgent(AgentBase):
    def __init__(self, db_connection):
        super().__init__(name="PMDataAgent")
        self.db = db_connection
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch PM2.5 data using gis.get_current_pm25(code, level)
        """
        location_code = input_data.get("location_code")
        location_level = input_data.get("location_level")
        location_name = input_data.get("location_name", "Unknown")
        
        self.log(f"Fetching PM2.5 for {location_name} (code: {location_code}, level: {location_level})")
        
        try:
            # Call your PM2.5 function
            result = await self.db.execute_query(
                "SELECT * FROM gis.get_current_pm25($1, $2)",
                [location_code, location_level]
            )
            
            if not result:
                return {
                    "success": False,
                    "error": "No PM2.5 data available for this location"
                }
            
            data = result[0]
            
            # Format response based on what your function returns
            # Adjust these field names based on your actual function output
            return {
                "success": True,
                "pm25_value": data.get("pm25_value"),
                "timestamp": data.get("timestamp"),
                "station_count": data.get("station_count"),
                "measurement_type": data.get("measurement_type"),  # avg, latest, etc.
                "location": {
                    "name": location_name,
                    "code": location_code,
                    "level": location_level
                },
                "raw_data": data  # Keep all data for debugging
            }
            
        except Exception as e:
            return self.handle_error(e, {
                "location_code": location_code,
                "location_level": location_level
            })