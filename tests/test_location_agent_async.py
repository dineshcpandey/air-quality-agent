"""
Async test script for LocationResolverAgent with database connection
"""

import asyncio
from src.agents.location_resolver import LocationResolverAgent
from src.utils.database import DatabaseConnection
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING")

async def main():
    # Initialize DB connection
    db = DatabaseConnection(DB_CONNECTION_STRING)
    await db.connect()

    # Initialize LocationResolverAgent with DB connection
    agent = LocationResolverAgent(db_connection=db)

    # Test queries
    test_queries = [
        "Delhi",
        "Mumbai",
        "NCR",
        "Atlantis"
    ]

    for query in test_queries:
        result = await agent.run({"location_query": query})
        print(f"Query: {query}\nResult: {result}\n{'-'*40}")

if __name__ == "__main__":
    asyncio.run(main())
