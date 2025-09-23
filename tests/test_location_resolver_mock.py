import asyncio
import pytest
import sys
import os

# Ensure src is importable
ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.mock_db import MockDatabase
from agents.location_resolver import LocationResolverAgent


@pytest.mark.asyncio
async def test_location_resolver_araria():
    db = MockDatabase()
    await db.connect()

    resolver = LocationResolverAgent(db)

    result = await resolver.run({"location_query": "Araria"})

    # Basic assertions
    assert result.get("success") is True
    locations = result.get("locations", [])
    assert isinstance(locations, list)
    assert len(locations) >= 1

    # Check expected fields on first location
    loc = locations[0]
    assert "code" in loc
    assert "level" in loc
    assert "name" in loc

    await db.disconnect()
