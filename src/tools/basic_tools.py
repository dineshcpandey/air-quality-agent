from langchain.tools import Tool
from typing import Optional

class CurrentReadingsTool(Tool):
    name = "get_current_readings"
    description = "Fetch latest sensor readings for specified locations and metrics"
    
    def _run(self, source: str, location: Optional[str] = None, metric: Optional[str] = None):
        sql = f"""
        SELECT *
        FROM aq.current_readings_{source}
        WHERE 1=1
        """
        if location:
            sql += f" AND (district = '{location}' OR location_name LIKE '%{location}%')"
        if metric:
            sql = sql.replace("*", metric)
        sql += " ORDER BY timestamp DESC LIMIT 10"
        
        return self.db.execute_query(sql)
