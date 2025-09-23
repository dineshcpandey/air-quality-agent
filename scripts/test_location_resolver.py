#!/usr/bin/env python3
"""Test the LocationResolverAgent against a real database.

Usage:
    python3 scripts/test_location_resolver.py "Araria"

This script will:
  - Load DB settings via the existing `src/utils/database.py` (which uses .env)
  - Connect to the database
  - Call `gis.search_location_json` through `LocationResolverAgent`
  - Print the structured results (one or more locations)

If the DB connection fails, the error will be printed with hints.
"""
import asyncio
import json
import os
import sys
from typing import Any

# Make sure src is importable
ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.database import DatabaseConnection
from agents.location_resolver import LocationResolverAgent
from agents.pm_data_agent import PMDataAgent
import argparse


async def main(location_query: str) -> None:
    db = DatabaseConnection()
    try:
        print("Connecting to database...")
        await db.connect()
    except Exception as e:
        print("Failed to connect to database:")
        print(str(e))
        print("\nTroubleshooting tips:")
        print(" - Ensure your .env contains DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        print(" - Make sure the DB is reachable from this machine (telnet/psql)")
        print(" - Run scripts/test_db_connection.py to verify basic connectivity")
        return

    try:
        resolver = LocationResolverAgent(db)
        print(f"Searching for: '{location_query}'")
        result = await resolver.run({"location_query": location_query})

        print("\nResult:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get('locations'):
            print(f"\nFound {len(result['locations'])} location(s):")
            for i, loc in enumerate(result['locations']):
                print(f"{i+1}. code={loc.get('code')}, level={loc.get('level')}, name={loc.get('name')}")
        else:
            print("No locations returned by the database query.")

    except Exception as e:
        print("Error while resolving location:")
        print(str(e))

    finally:
        await db.disconnect()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Test location resolver and optionally fetch PM data for a selected result")
    parser.add_argument('query', type=str, help='Location search term')
    parser.add_argument('--select', type=int, help='1-based index of the location to fetch PM data for')
    args = parser.parse_args()

    selection = args.select
    if selection:
        # run and fetch selection
        async def run_and_select():
            db = DatabaseConnection()
            try:
                await db.connect()
            except Exception as e:
                print(f"Failed to connect to database: {e}")
                return

            resolver = LocationResolverAgent(db)
            result = await resolver.run({"location_query": args.query})
            locations = result.get('locations', [])
            if not locations:
                print("No locations found to select from.")
                await db.disconnect()
                return

            idx = selection - 1
            if idx < 0 or idx >= len(locations):
                print(f"Selection {selection} out of range (1..{len(locations)})")
                await db.disconnect()
                return

            chosen = locations[idx]
            print(f"Selected: {chosen['display_name']} (code={chosen['code']}, level={chosen['level']})")

            pm_agent = PMDataAgent(db)
            pm_result = await pm_agent.run({
                'location': chosen
            })

            print('\nPM agent normalized result:')
            # Some DB drivers return Decimal objects; use default=str to serialize them
            print(json.dumps(pm_result, indent=2, ensure_ascii=False, default=str))

            await db.disconnect()

        asyncio.run(run_and_select())
    else:
        asyncio.run(main(args.query))
