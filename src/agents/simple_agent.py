import asyncio
import sys
import os

import sys
import os

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.database import DatabaseConnection
from src.utils.database import DatabaseConnection
async def main():
    db = DatabaseConnection()
    await db.connect()
    sources = await db.get_data_sources()
    if sources:
        print(f"First active data source: {sources[0]}")
    else:
        print("No active data sources found.")
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
