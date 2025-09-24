#!/usr/bin/env python3
"""
Simple test to verify the backend selection endpoint is working

This bypasses Streamlit entirely and tests the backend directly.
"""

import requests
import json
import sys

def test_backend_selection():
    """Test the backend selection endpoint directly"""
    
    print("=" * 60)
    print("Testing Backend Selection Endpoint")
    print("=" * 60)
    
    # Step 1: First get some disambiguation state
    print("\n1. Getting disambiguation state...")
    
    backend_url = "http://localhost:8001"
    
    # Check health
    try:
        health = requests.get(f"{backend_url}/health", timeout=2)
        print(f"✅ Backend is running: {health.json()}")
    except:
        print("❌ Backend is not running!")
        print("Start it with: python -m uvicorn src.api.main:app --reload --port 8001")
        return
    
    # Send a query that should trigger disambiguation
    query = "What is PM2.5 in Ambedkar Nagar"
    print(f"\n2. Sending query: '{query}'")
    
    response = requests.post(
        f"{backend_url}/query",
        json={"query": query},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Query failed: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    state = result.get('state', {})
    
    if not state.get('waiting_for_user'):
        print("❌ No disambiguation triggered")
        print(json.dumps(state, indent=2))
        return
    
    locations = state.get('locations', [])
    print(f"✅ Got {len(locations)} locations:")
    for i, loc in enumerate(locations):
        print(f"   {i}: {loc.get('display_name', loc.get('name'))}")
    
    if not locations:
        print("❌ No locations to select")
        return
    
    # Step 2: Test selection
    print(f"\n3. Testing selection of index 0...")
    
    selection_url = f"{backend_url}/query/select"
    print(f"   URL: {selection_url}")
    print(f"   Payload: state with {len(locations)} locations, selected_index: 0")
    
    selection_response = requests.post(
        selection_url,
        json={
            "state": state,
            "selected_index": 0
        },
        timeout=10
    )
    
    print(f"   Response status: {selection_response.status_code}")
    
    if selection_response.status_code == 200:
        selection_result = selection_response.json()
        data = selection_result.get('data', {})
        
        print("\n✅ Selection successful!")
        if data.get('formatted_response'):
            print("\nFormatted Response:")
            print("-" * 40)
            print(data['formatted_response'])
            print("-" * 40)
        
        if data.get('raw_data'):
            print("\nRaw PM Data:")
            print(json.dumps(data['raw_data'], indent=2, default=str))
    else:
        print(f"❌ Selection failed: {selection_response.status_code}")
        print(selection_response.text)
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_backend_selection()
