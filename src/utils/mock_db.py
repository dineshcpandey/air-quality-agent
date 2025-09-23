import asyncio
import json
from typing import List, Dict, Any, Optional


class MockDatabase:
    """A tiny in-memory mock of DatabaseConnection for local demos and tests.

    It implements the async methods used by the agents:
      - connect()
      - disconnect()
      - execute_query(sql, params)
      - test_connection()
      - get_data_sources()
    """

    def __init__(self):
        self.connected = False

    async def connect(self):
        await asyncio.sleep(0)  # yield
        self.connected = True

    async def disconnect(self):
        await asyncio.sleep(0)
        self.connected = False

    async def test_connection(self) -> bool:
        await asyncio.sleep(0)
        return True

    async def get_data_sources(self) -> List[Dict[str, Any]]:
        await asyncio.sleep(0)
        return [
            {"code": "ARARIA_STN", "name": "Araria Monitoring Network", "source_type": "station", "readings_table_name": "readings_station"}
        ]

    async def execute_query(self, sql: str, params: List = None) -> List[Dict[str, Any]]:
        """Return deterministic mock results depending on the SQL called.

        Location resolver expects: SELECT gis.search_location_json($1) as locations
        PMDataAgent expects: SELECT * FROM gis.get_current_pm25($1, $2)
        """
        sql_lower = (sql or "").lower()
        params = params or []

        # Mock search_location_json
        if 'search_location_json' in sql_lower:
            query_text = params[0] if params else ''
            # If query contains araria, return a list with one or more matches
            if 'araria' in query_text.lower():
                locations = [
                    {
                        "code": "ARARIA_D", 
                        "level": "district",
                        "name": "Araria",
                        "state_name": "Bihar",
                        "district_name": "Araria",
                        "parent_name": "ARARIA"
                    }
                ]
            else:
                locations = []

            # Return as the DB driver would: a row with 'locations'
            return [{"locations": locations}]

        # Mock get_current_pm25
        if 'get_current_pm25' in sql_lower:
            code = params[0] if params else None
            level = params[1] if len(params) > 1 else None

            # Provide a deterministic value for Araria
            if code and 'araria' in str(code).lower() or code == 'ARARIA_D':
                return [{
                    "pm25_value": 145.2,
                    "timestamp": "2025-09-22T10:00:00Z",
                    "station_count": 3,
                    "measurement_type": "avg"
                }]

            # Default empty
            return []

        # Generic fallback
        return []
