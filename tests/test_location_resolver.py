"""
Unit tests for LocationResolverAgent
"""
import pytest
from src.agents.location_resolver import LocationResolverAgent

@pytest.fixture
def agent():
    return LocationResolverAgent()

def test_delhi_resolution(agent):
    result = agent.run({"location_query": "Delhi"})
    assert result["success"]
    assert "district_id_delhi_central" in result["resolved_locations"]
    assert result["resolution_type"] == "district"
    assert result["confidence"] > 0.9

def test_mumbai_resolution(agent):
    result = agent.run({"location_query": "Mumbai"})
    assert result["success"]
    assert "district_id_mumbai_city" in result["resolved_locations"]
    assert result["resolution_type"] == "district"
    assert result["confidence"] > 0.9

def test_ncr_resolution(agent):
    result = agent.run({"location_query": "NCR"})
    assert result["success"]
    assert set(result["resolved_locations"]) == set([
        "district_id_delhi_central", "district_id_gurgaon", "district_id_noida"
    ])
    assert result["resolution_type"] == "region"
    assert result["confidence"] > 0.9

def test_unknown_location(agent):
    result = agent.run({"location_query": "Atlantis"})
    assert not result["success"]
    assert result["error"] == "Location not recognized"
    assert result["confidence"] == 0.0
