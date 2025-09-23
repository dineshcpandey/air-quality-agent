#!/usr/bin/env python3
"""Demo: run PMQueryWorkflow programmatically using app startup wiring.

This script imports the FastAPI app from src.api.main and triggers startup(),
then calls the workflow methods to simulate a user query and selection.
"""
import asyncio
import json
import os
import sys

import pathlib
ROOT = pathlib.Path.cwd()
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import src.api.main as api_main

async def main():
    # Run startup handler to initialize DB and agents
    await api_main.startup_event()
    try:
        workflow = api_main.app.state.workflow
        print('Running workflow.process_query("what is the current PM2.5 in Ambedkar Nagar")')
        state = await workflow.process_query('what is the current PM2.5 in Ambedkar Nagar')
        print(json.dumps(state, indent=2, default=str, ensure_ascii=False))

        if state.get('waiting_for_user'):
            print('\nSelecting the first option (index 0)')
            state2 = await workflow.continue_with_selection(state, 0)
            print(json.dumps(state2, indent=2, default=str, ensure_ascii=False))
    finally:
        if getattr(api_main.app.state, 'db', None):
            await api_main.app.state.db.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
