# test_workflow.py
import asyncio
from src.utils.database import DatabaseConnection
from src.agents.location_resolver import LocationResolverAgent
from src.agents.pm_data_agent import PMDataAgent
from src.graphs.pm_query_workflow import PMQueryWorkflow

async def test():
    # Initialize
    db = DatabaseConnection()
    await db.connect()
    
    location_agent = LocationResolverAgent(db)
    pm_agent = PMDataAgent(db)
    workflow = PMQueryWorkflow(location_agent, pm_agent)
    
    # Test query
    query = "What is PM level in Araria?"
    print(f"Query: {query}\n")
    
    # Process
    state = await workflow.process_query(query)
    
    if state.get("waiting_for_user"):
        print("Disambiguation needed!")
        print("Options:")
        for i, loc in enumerate(state["locations"]):
            print(f"{i}: {loc['display_name']}")
        
        # Simulate user selecting first option
        print("\nSelecting option 0...")
        state = await workflow.continue_with_selection(state, 0)
    
    print(f"\nFinal Response:\n{state['response']}")
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(test())