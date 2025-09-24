#!/usr/bin/env python3
"""
Test the disambiguation flow by calling the backend API directly

Usage:
    python scripts/test_disambiguation_flow.py "ambedkar nagar"
    
This will:
1. Send the query to the backend
2. Show the locations returned
3. Simulate selecting the first option
4. Show the final PM2.5 data
"""

import requests
import json
import sys
from typing import Dict, Any

BACKEND_URL = "http://localhost:8001"


def test_query(location_query: str) -> None:
    """Test the complete query flow"""
    print("=" * 60)
    print(f"🔍 Testing query: '{location_query}'")
    print("=" * 60)
    
    # Construct the full query
    full_query = f"What is the current PM2.5 in {location_query}"
    print(f"\n📝 Full query: '{full_query}'")
    
    # Step 1: Send initial query
    print("\n1️⃣ Sending query to backend...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/query",
            json={"query": full_query},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as e:
        print(f"❌ Error calling backend: {e}")
        print("\n💡 Make sure the backend is running:")
        print("   python -m uvicorn src.api.main:app --reload --port 8001")
        return
    
    # Display the response
    print("\n📥 Backend response:")
    print(json.dumps(result, indent=2))
    
    # Check if disambiguation is needed
    state = result.get('state', {})
    if state.get('waiting_for_user'):
        locations = state.get('locations', [])
        print(f"\n✅ Disambiguation needed! Found {len(locations)} locations:")
        
        for i, loc in enumerate(locations):
            print(f"\n  {i}: {loc.get('display_name', loc.get('name'))}")
            print(f"     Code: {loc.get('code')}")
            print(f"     Level: {loc.get('level')}")
            print(f"     State: {loc.get('state', 'N/A')}")
        
        # Step 2: Simulate selection (choose first option)
        if locations:
            selected_index = 0
            print(f"\n2️⃣ Selecting option {selected_index}: {locations[selected_index].get('display_name')}")
            
            try:
                selection_response = requests.post(
                    f"{BACKEND_URL}/query/select",
                    json={"state": state, "selected_index": selected_index},
                    timeout=10
                )
                selection_response.raise_for_status()
                selection_result = selection_response.json()
            except requests.RequestException as e:
                print(f"❌ Error during selection: {e}")
                return
            
            print("\n📥 Selection response:")
            print(json.dumps(selection_result, indent=2))
            
            # Extract and display the formatted response
            data = selection_result.get('data', {})
            if data.get('formatted_response'):
                print("\n✅ Final Response:")
                print("-" * 40)
                print(data['formatted_response'])
                print("-" * 40)
            
            # Show raw PM data if available
            if data.get('raw_data'):
                print("\n📊 Raw PM Data:")
                print(json.dumps(data['raw_data'], indent=2, default=str))
    else:
        # Direct response (no disambiguation needed)
        data = result.get('data', {})
        if data.get('formatted_response'):
            print("\n✅ Direct Response (no disambiguation needed):")
            print("-" * 40)
            print(data['formatted_response'])
            print("-" * 40)
        
        # Check for errors
        if state.get('error'):
            print(f"\n❌ Error: {state['error']}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)


def check_backend_health() -> bool:
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=2)
        response.raise_for_status()
        health = response.json()
        print(f"✅ Backend is healthy: {health}")
        return True
    except:
        print(f"❌ Backend is not running at {BACKEND_URL}")
        return False


def main():
    """Main test function"""
    # Check if location query provided
    if len(sys.argv) < 2:
        print("Usage: python test_disambiguation_flow.py <location>")
        print("Example: python test_disambiguation_flow.py 'ambedkar nagar'")
        sys.exit(1)
    
    location = " ".join(sys.argv[1:])
    
    # Check backend health
    print("🔍 Checking backend health...")
    if not check_backend_health():
        print("\n💡 Start the backend with:")
        print("   python -m uvicorn src.api.main:app --reload --port 8001")
        sys.exit(1)
    
    print()
    
    # Run the test
    test_query(location)


if __name__ == "__main__":
    main()
