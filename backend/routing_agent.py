import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY)

# ------------------------------
# Specialized processing nodes
# ------------------------------

# Dummy implementations of specialized nodes
def sentiment_node(state: MessagesState):
    last_message = state["messages"][-1].content.lower()
    # In real code, call GCP sentiment model here
    sentiment = "positive" if "good" in last_message else "negative or neutral"
    return {"messages": [AIMessage(content=f"Sentiment analysis result: {sentiment}")]}

def design_node(state: MessagesState):
    # Stub: Call Gemini PDF endpoint and store/handle context here
    return {"messages": [AIMessage(content="Design doc processed with extracted dimensions (dummy).")]}

def policy_node(state: MessagesState):
    # Stub: Call warranty/refund LLM model here
    return {"messages": [AIMessage(content="Policy info: Warranty is 12 months standard (dummy).")]}

# ------------------------------
# Classifier node
# ------------------------------

# --- classifier node (normal node) ---
def classifier_node(state: MessagesState):
    user_msg = state["messages"][-1].content
    sys_msg = SystemMessage(content=(
        "You are an intelligent classifier. The user query will be one of: "
        "'sentiment' if it's a review or complaint, "
        "'design' if it's about design documents or schematics, "
        "or 'policy' if it's about refunds or warranty questions. "
        "Return one word: sentiment, design, or policy."
    ))
    reply = llm.invoke([sys_msg, HumanMessage(content=user_msg)])
    classified = reply.content.strip().lower()

    if classified not in ("sentiment", "design", "policy"):
        classified = "policy"

    return {"next": classified}

def route_from_classifier(state):
    return state["next"] 

# ------------------------------
# Build LangGraph
# ------------------------------


builder = StateGraph(MessagesState)
builder.add_node("classifier", classifier_node)
builder.add_node("sentiment", sentiment_node)
builder.add_node("design", design_node)
builder.add_node("policy", policy_node)

builder.add_edge(START, "classifier")
builder.add_conditional_edges("classifier", route_from_classifier, {
    "sentiment": "sentiment",
    "design": "design",
    "policy": "policy",
})
builder.add_edge("sentiment", END)
builder.add_edge("design", END)
builder.add_edge("policy", END)

# ------------------------------
# Compile with optional memory checkpoint
# ------------------------------

use_custom_checkpoint = os.getenv("USE_CUSTOM_CHECKPOINT", "true").lower() == "true"
if use_custom_checkpoint:
    memory = MemorySaver()
    graph_with_checkpoint = builder.compile(checkpointer=memory)
else:
    graph_studio = builder.compile()

class RoutingAgent:
    def __init__(self):
        self.graph = graph_with_checkpoint

    def handle_message(self, message: str, thread_id: str):
        messages = [HumanMessage(content=message)]
        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke({"messages": messages}, config)
        return result['messages'][-1].content

