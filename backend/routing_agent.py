import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, List, Optional, Dict

# Define a composite state TypedDict with messages and optional pdf_bytes
class MessageDict(TypedDict):
    content: str
    metadata: Optional[Dict]

class OverallState(TypedDict):
    messages: List[MessageDict]
    pdf_bytes: Optional[bytes]

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY)

# ------------------------------
# Specialized processing nodes
# ------------------------------

# Dummy implementations of specialized nodes
def sentiment_node(state: OverallState):
    last_message = state["messages"][-1].content.lower()
    # In real code, call GCP sentiment model here
    sentiment = "positive" if "good" in last_message else "negative or neutral"
    return {"messages": [AIMessage(content=f"Sentiment analysis result: {sentiment}")]}

def design_node(state: OverallState):
    # Stub: Call Gemini PDF endpoint and store/handle context here
    return {"messages": [AIMessage(content="Design doc processed with extracted dimensions (dummy).")]}

def policy_node(state: OverallState):
    # Stub: Call warranty/refund LLM model here
    return {"messages": [AIMessage(content="Policy info: Warranty is 12 months standard (dummy).")]}

# ------------------------------
# Classifier node
# ------------------------------

# --- classifier node (normal node) ---
import io
from PyPDF2 import PdfReader
import pdf2image
import pytesseract
from PIL import Image

def extract_text_from_pdf(pdf_bytes: bytes, max_chars: int = 800) -> str:
    text = ""
    try:
        # Try PyPDF2 first for text-based PDFs
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text
            if len(text) >= max_chars:
                break

        # If no text found, try OCR (for scanned/image PDFs)
        if text.strip() == "":
            images = pdf2image.convert_from_bytes(pdf_bytes)
            for img in images:
                ocr_text = pytesseract.image_to_string(img)
                text += ocr_text
                if len(text) >= max_chars:
                    break

    except Exception as e:
        print("Error extracting text from PDF:", e)

    return text[:max_chars]
    

def classifier_node(state: OverallState):
    user_msg = state["messages"][-1].content
    pdf_bytes = state.get("pdf_bytes")

    # Extract PDF text if available
    pdf_text_preview = extract_text_from_pdf(pdf_bytes) if pdf_bytes else ""

    # For debugging
    # print(pdf_text_preview)

    classifier_prompt = f"""
You are a routing classifier for customer tickets.
Each ticket includes:
- A user message (text input, can be empty)
- An optional PDF document (text extracted from PDF)

Classify the request into one of three categories:
- 'sentiment' → if the user is giving a review, complaint, or feedback (including if a review is written in a PDF)
- 'design' → if the content involves technical drawings, architectural schematics, or CAD-like documents
- 'policy' → if the content involves warranty, refunds, or product policy


Rules:
- Do NOT assume that every PDF is a design document.
- If the user message is empty, classify based on PDF content.
- If the PDF text or user message looks like feedback or a review, classify as 'sentiment'.
- If the PDF looks like warranty or refund documentation, classify as 'policy'.
- Otherwise, classify as 'design'.
- Respond with exactly one word: sentiment, design, or policy.

User message:
\"\"\"{user_msg}\"\"\"

PDF text preview:
\"\"\"{pdf_text_preview}\"\"\"

    """

    reply = llm.invoke([HumanMessage(content=classifier_prompt)])
    classified = reply.content.strip().lower()

    if classified not in ("sentiment", "design", "policy"):
        classified = "policy"

    return {"next": classified}



def route_from_classifier(state):
    return state["next"] 

# ------------------------------
# Build LangGraph
# ------------------------------


builder = StateGraph(OverallState)
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

    def handle_message(self, message: str, thread_id: str, pdf_path: Optional[str] = None):
        pdf_bytes = None
        if pdf_path:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

        messages = [HumanMessage(content=message)]
        config = {"configurable": {"thread_id": thread_id}}

        result = self.graph.invoke({"messages": messages, "pdf_bytes": pdf_bytes}, config)
        return result["messages"][-1].content
