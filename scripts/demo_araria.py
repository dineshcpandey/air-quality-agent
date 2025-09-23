#!/usr/bin/env python3
"""Demo: run PMQueryWorkflow for 'Araria' using a MockDatabase.

Usage:
    python3 scripts/demo_araria.py

This does not require a real Postgres server.
"""
import asyncio
import sys
import os

# Ensure src is importable
ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.mock_db import MockDatabase
from agents.location_resolver import LocationResolverAgent
from agents.pm_data_agent import PMDataAgent


async def main():
    db = MockDatabase()
    await db.connect()

    location_agent = LocationResolverAgent(db)
    pm_agent = PMDataAgent(db)

    query = "What is PM level in Araria?"
    print(f"Query: {query}\n")

    # Step 1: Resolve location
    loc_result = await location_agent.run({"location_query": "Araria"})
    locations = loc_result.get("locations", [])
    if not locations:
        print("No locations found for 'Araria'")
        await db.disconnect()
        return

    selected = locations[0]

    # Step 2: Fetch PM data
    pm_result = await pm_agent.run({
        "location_code": selected.get("code"),
        "location_level": selected.get("level"),
        "location_name": selected.get("name")
    })

    # Step 3: Format response (reuse simple category logic)
    def _get_air_quality_category(pm25_value: float):
        if pm25_value is None:
            return "Unknown", "❓"
        elif pm25_value <= 30:
            return "Good", "🟢"
        elif pm25_value <= 60:
            return "Satisfactory", "🟡"
        elif pm25_value <= 90:
            return "Moderate", "🟠"
        elif pm25_value <= 120:
            return "Poor", "🔴"
        elif pm25_value <= 250:
            return "Very Poor", "🟣"
        else:
            return "Severe", "🛑"

    if not pm_result.get("success"):
        print(f"Error fetching PM data: {pm_result.get('error')}")
    else:
        pm_value = pm_result.get("pm25_value")
        category, emoji = _get_air_quality_category(pm_value)
        response = f"{emoji} PM2.5 level in {selected.get('name')}\n\n"
        response += f"Current Level: {pm_value:.1f} \u00b5g/m\u00b3\n"
        response += f"Location Type: {selected.get('level')}\n"
        response += f"Category: {category}\n"
        if pm_result.get('timestamp'):
            response += f"Last Updated: {pm_result.get('timestamp')}\n"
        if pm_result.get('station_count'):
            response += f"Data from: {pm_result.get('station_count')} stations\n"

        print("Final Response:\n")
        print(response)

    await db.disconnect()


if __name__ == '__main__':
    asyncio.run(main())