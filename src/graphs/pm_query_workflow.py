# Minimal PM Query workflow - single clean implementation
from typing import Dict, Any, Optional, TypedDict, List, Tuple


class PMQueryState(TypedDict):
    user_query: str
    location_search_term: str
    locations: List[Dict[str, Any]]
    needs_disambiguation: bool
    selected_location: Optional[Dict[str, Any]]
    pm_data: Optional[Dict[str, Any]]
    response: str
    error: Optional[str]
    waiting_for_user: bool


class PMQueryWorkflowProcedural:
    """Small procedural workflow to resolve a location and fetch PM2.5 values."""

    def __init__(self, location_agent, pm_agent):
        self.location_agent = location_agent
        self.pm_agent = pm_agent

    def _get_air_quality_category(self, pm25_value: Optional[float]) -> Tuple[str, str]:
        if pm25_value is None:
            return "Unknown", "❓"
        if pm25_value <= 30:
            return "Good", "🟢"
        if pm25_value <= 60:
            return "Satisfactory", "🟡"
        if pm25_value <= 90:
            return "Moderate", "🟠"
        if pm25_value <= 120:
            return "Poor", "🔴"
        if pm25_value <= 250:
            return "Very Poor", "🟣"
        return "Severe", "🟤"

    async def process_query(self, query: str) -> PMQueryState:
        state: PMQueryState = {
            "user_query": query,
            "location_search_term": "",
            "locations": [],
            "needs_disambiguation": False,
            "selected_location": None,
            "pm_data": None,
            "response": "",
            "error": None,
            "waiting_for_user": False,
        }

        q = state["user_query"].lower()
        term = ""
        for sep in (" in ", " at ", " for "):
            if sep in q:
                term = q.split(sep)[-1].strip()
                break
        if not term:
            parts = q.split()
            term = parts[-1] if parts else ""
        state["location_search_term"] = term

        res = await self.location_agent.run({"location_query": term})
        state["locations"] = res.get("locations", [])
        state["needs_disambiguation"] = res.get("needs_disambiguation", False)

        if state["needs_disambiguation"] and len(state["locations"]) > 1:
            state["waiting_for_user"] = True
            return state

        if state["locations"]:
            state["selected_location"] = state["locations"][0]

        if not state.get("selected_location"):
            state["error"] = "No location found"
            return state

        loc = state["selected_location"]
        pm_res = await self.pm_agent.run({
            "location_code": loc.get("code"),
            "location_level": loc.get("level"),
            "location_name": loc.get("name"),
        })
        if not pm_res.get("success"):
            state["error"] = pm_res.get("error") or "Failed to fetch PM data"
            return state
        state["pm_data"] = pm_res

        pm = state["pm_data"].get("pm25_value") if state.get("pm_data") else None
        _, emoji = self._get_air_quality_category(pm)
        loc_name = loc.get("name", "unknown")
        if pm is None:
            pm_text = "N/A"
        else:
            try:
                pm_text = f"{pm:.2f}"
            except Exception:
                pm_text = str(pm)

        state["response"] = f"{emoji} PM2.5 in {loc_name}: {pm_text} µg/m³"
        return state

    async def continue_with_selection(self, state: PMQueryState, selected_idx: int) -> PMQueryState:
        if not state.get("locations"):
            return {**state, "error": "No locations to select from"}
        if selected_idx < 0 or selected_idx >= len(state["locations"]):
            return {**state, "error": "Selected index out of range"}

        state["selected_location"] = state["locations"][selected_idx]
        state["waiting_for_user"] = False

        loc = state["selected_location"]
        pm_res = await self.pm_agent.run({
            "location_code": loc.get("code"),
            "location_level": loc.get("level"),
            "location_name": loc.get("name"),
        })
        if not pm_res.get("success"):
            return {**state, "error": pm_res.get("error") or "Failed to fetch PM data"}
        state["pm_data"] = pm_res

        pm = pm_res.get("pm25_value")
        _, emoji = self._get_air_quality_category(pm)
        if pm is None:
            pm_text = "N/A"
        else:
            try:
                pm_text = f"{pm:.2f}"
            except Exception:
                pm_text = str(pm)

        state["response"] = f"{emoji} PM2.5 in {loc.get('name','unknown')}: {pm_text} µg/m³"
        return state


# --- Graph adapter (optional) -------------------------------------------------
USE_LANGGRAPH = True
try:
    import importlib
    langgraph = importlib.import_module('langgraph')  # type: ignore - optional
    # try to load the graph submodule if present
    try:
        lg_graph = importlib.import_module('langgraph.graph')
        StateGraph = getattr(lg_graph, 'StateGraph')
        END = getattr(lg_graph, 'END')
    except Exception:
        StateGraph = None
        END = None
except Exception:
    USE_LANGGRAPH = False


if USE_LANGGRAPH:
    class GraphPMQueryWorkflow:
        """Adapter that builds a small langgraph graph but delegates work to the
        existing agents. This keeps behavior parity while letting the graph
        runtime orchestrate node ordering if present.
        """

        def __init__(self, location_agent, pm_agent):
            self.location_agent = location_agent
            self.pm_agent = pm_agent
            # We don't create a complex graph here; graph creation would go
            # here if you want to visualize or instrument nodes. For now we
            # simply delegate to existing methods to preserve behavior.

        async def process_query(self, query: str) -> PMQueryState:
            # Delegate to the procedural implementation for now so behavior
            # remains identical; a more featureful graph can be constructed
            # later that maps nodes to these logical steps.
            proc = globals().get('PMQueryWorkflowProcedural')
            if proc is None:
                raise RuntimeError('Procedural workflow missing')
            w = proc(self.location_agent, self.pm_agent)
            return await w.process_query(query)

        async def continue_with_selection(self, state: PMQueryState, selected_idx: int) -> PMQueryState:
            proc = globals().get('PMQueryWorkflowProcedural')
            if proc is None:
                raise RuntimeError('Procedural workflow missing')
            w = proc(self.location_agent, self.pm_agent)
            return await w.continue_with_selection(state, selected_idx)


    # Export name that users expect
    PMQueryWorkflow = GraphPMQueryWorkflow  # type: ignore
# Export PMQueryWorkflow symbol: prefer graph-backed adapter when available
if USE_LANGGRAPH:
    PMQueryWorkflow = GraphPMQueryWorkflow  # type: ignore
else:
    PMQueryWorkflow = PMQueryWorkflowProcedural  # type: ignore