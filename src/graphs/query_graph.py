# src/graphs/query_graph.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class QueryState(TypedDict):
    user_query: str
    intent: str
    entities: dict
    sql: str
    results: List[dict]
    error: str
    formatted_response: str

class QueryGraph:
    def __init__(self, db_connection):
        self.db = db_connection
        self.workflow = self._build_graph()
    
    def _build_graph(self):
        workflow = StateGraph(QueryState)
        
        # Add nodes
        workflow.add_node("classify", self.classify_intent)
        workflow.add_node("extract", self.extract_entities)
        workflow.add_node("generate_sql", self.generate_sql)
        workflow.add_node("execute", self.execute_query)
        workflow.add_node("format", self.format_response)
        
        # Set flow
        workflow.set_entry_point("classify")
        workflow.add_edge("classify", "extract")
        workflow.add_edge("extract", "generate_sql")
        workflow.add_edge("generate_sql", "execute")
        workflow.add_edge("execute", "format")
        workflow.add_edge("format", END)
        
        return workflow.compile()
