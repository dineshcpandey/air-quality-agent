"""
LocationResolverAgent
Resolves location references (city, landmark, alias) to standardized IDs, coordinates, and bounding boxes.
"""

from typing import Dict, Any, List, Optional
from .agent_base import AgentBase
import yaml
import os

class LocationResolverAgent(AgentBase):
    def __init__(self, db_connection=None, queries_path=None):
        super().__init__(name="LocationResolverAgent")
        self.db = db_connection
        # Load queries from config/queries.yaml
        if queries_path is None:
            queries_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "config", "queries.yaml")
        with open(queries_path, "r") as f:
            self.queries = yaml.safe_load(f)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        input_data: { "location_query": str }
        output: {
            "resolved_locations": List[str],
            "resolution_type": str,
            "confidence": float,
            "bbox": List[float]
        }
        """
        query_text = input_data.get("location_query", "").strip()
        self.log(f"Resolving location for query: '{query_text}'")

        sql = self.queries.get("location_search")
        if not sql:
            return {
                "success": False,
                "error": "Location search query not found in config",
                "resolved_locations": [],
                "resolution_type": None,
                "confidence": 0.0,
                "bbox": []
            }
        try:
            # Use the database connection to execute the query
            # Replace :location_text with parameterized value if needed
            # Assuming db_connection.execute_query is async
            result = await self.db.execute_query(
                sql.replace(":location_text", "$1"), [query_text]
            )
            if not result:
                self.log("No match found for location query.")
                return {
                    "success": False,
                    "error": "Location not recognized",
                    "resolved_locations": [],
                    "resolution_type": None,
                    "confidence": 0.0,
                    "bbox": []
                }
            # Assume result[0] contains the needed fields
            row = result[0]
            return {
                "success": True,
                "resolved_locations": row.get("resolved_locations", []),
                "resolution_type": row.get("resolution_type"),
                "confidence": row.get("confidence", 1.0),
                "bbox": row.get("bbox", [])
            }
        except Exception as e:
            return self.handle_error(e, {"location_query": query_text})
