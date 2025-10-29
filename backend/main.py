import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from custom_state import OverallState
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, List, Optional, Annotated
from nodes import sentiment_node, design_node, policy_node, classifier_node
from graph import build_graph
from agent import RoutingAgent

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY)

# class OverallState(TypedDict):
#     messages: Annotated[List[BaseMessage], add_messages]  # Auto-append with reducer
#     pdf_bytes: Optional[bytes]
#     next: Optional[str]

# Build the LangGraph graph with nodes and edges
builder = build_graph(OverallState, sentiment_node, design_node, policy_node, classifier_node)
# if using langsmith studio can set checkpoint to false so it can handle it under the hood
use_custom_checkpoint = os.getenv("USE_CUSTOM_CHECKPOINT", "true").lower() == "true"

if use_custom_checkpoint:
    memory = MemorySaver()
    graph_with_checkpoint = builder.compile(checkpointer=memory)
else:
    graph_no_checkpoint = builder.compile()

# Initialize the routing agent with the compiled graph
agent = RoutingAgent(graph=graph_with_checkpoint)

# Example usage (uncomment to use):
# response = agent.handle_message("Hello, I want to ask about warranty.", thread_id="thread-1")
# print(response)
