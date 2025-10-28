import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def sentiment_analysis_tool(text: str) -> str:
    """Perform dummy sentiment analysis on the input text.

    Args:
        text: Input text string.

    Returns:
        A placeholder sentiment analysis result string.
    """
    return "Sentiment analysis result placeholder"

def design_doc_tool(pdf_content: str) -> str:
    """Process dummy design document content.

    Args:
        pdf_content: String representation of PDF content.

    Returns:
        A placeholder design doc processing response string.
    """
    return "Design doc processing placeholder"

def warranty_tool(question: str) -> str:
    """Provide dummy warranty information response.

    Args:
        question: Customer question about warranty.

    Returns:
        A placeholder warranty information string.
    """
    return "Warranty info placeholder"


tools = [sentiment_analysis_tool, design_doc_tool, warranty_tool]

# Initialize the LLM with API key and model name
llm = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY)
llm_with_tools = llm.bind_tools(tools)

# System prompt describing the agent's task
sys_msg = SystemMessage(content="You are a helpful assistant who selects and calls the appropriate tool based on the user's request.")

# Assistant function: calls the LLM with tools
def assistant(state: MessagesState):
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

# Build the LangGraph state graph
builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")


# switching between studio
use_custom_checkpoint = os.getenv("USE_CUSTOM_CHECKPOINT", "true").lower() == "true"

if use_custom_checkpoint:
    memory = MemorySaver()
    graph_with_memory = builder.compile(checkpointer=memory)
else:
    graph_no_memory = builder.compile()  # Let STUDIO platform handle checkpointing


# graph_with_memory = builder.compile(checkpointer=memory)

class RoutingAgent:
    def __init__(self):
        self.graph = graph_with_memory

    def handle_message(self, message: str, thread_id: str):
        messages = [HumanMessage(content=message)]
        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke({"messages": messages}, config)
        return result['messages'][-1].content
