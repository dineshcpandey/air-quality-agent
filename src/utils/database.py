import asyncpg
from typing import List, Dict, Any

class DatabaseConnection:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(self.connection_string)
    
    async def execute_query(self, sql: str, params: List = None) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, *(params or []))
            return [dict(row) for row in rows]
    
    async def get_data_sources(self) -> List[Dict[str, Any]]:
        sql = """
        SELECT code, name, source_type, readings_table_name 
        FROM master.data_sources 
        WHERE is_active = true
        """
        return await self.execute_query(sql)

 