#!/usr/bin/env python3
"""Test PMDataAgent against the real database.

Usage:
    python3 scripts/test_pm_data_agent.py

The script will call PMDataAgent.run with code=1116 and level=sub_district and
print the returned structure.
"""
import asyncio
import json
import os
import sys

# Make sure src is importable
ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.database import DatabaseConnection
from agents.pm_data_agent import PMDataAgent


async def main():
    db = DatabaseConnection()
    try:
        print("Connecting to database...")
        await db.connect()
    except Exception as e:
        print("Failed to connect to DB:")
        print(e)
        return

    agent = PMDataAgent(db)

    input_data = {
        "location_code": "1",
        "location_level": "ward",
        "location_name": "(code=1)"
    }

    print(f"Calling PMDataAgent with: code={input_data['location_code']}, level={input_data['location_level']}")

    try:
        result = await agent.run(input_data)
        print("\nResult:")
        # use default=str to safely serialize Decimal and other non-JSON types
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        print("Error calling PMDataAgent:")
        print(str(e))

    await db.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
