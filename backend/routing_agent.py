import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END, add_messages
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, List, Optional, Dict, Annotated

class OverallState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]  # Auto-append with reducer
    pdf_bytes: Optional[bytes]
    next: Optional[str]

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY)

# ------------------------------
# Specialized processing nodes
# ------------------------------

# Dummy implementations of specialized nodes
def sentiment_node(state: OverallState):
    last_message = state["messages"][-1].content.lower()
    sentiment = "positive" if "good" in last_message else "negative or neutral"
    # Append AIMessage to existing history
    return {
        "messages": [AIMessage(content=f"Sentiment analysis result: {sentiment}")]
    }

def design_node(state: OverallState):
    return {
        "messages": [AIMessage(content="Design doc processed with extracted dimensions (dummy).")]
    }

def policy_node(state: OverallState):
    """Handles warranty and refund policy questions using a specialized LLM
    with general retail policy context based on item price tiers."""
    
    # General retail policy knowledge base
    policy_context = """You are a customer service agent for a major online retailer (similar to Amazon/Argos).
      We sell thousands of products across all categories. Use these general policies:
      
      REFUND POLICY (Based on Item Price):
      
      Under £50:
      - 30-day return window from delivery date
      - Full refund if unopened/unused with original packaging
      - 80% refund if opened but in resaleable condition
      - Free return shipping
      
      £50 - £200:
      - 30-day return window from delivery date
      - Full refund if unopened/unused with original packaging
      - 70% refund if opened but in resaleable condition
      - Customer pays return shipping (unless faulty)
      
      Over £200:
      - 60-day return window from delivery date
      - Full refund if unopened/unused with original packaging
      - 60% refund if opened but in resaleable condition
      - Free return shipping for items over £500
      - Customer pays return shipping for £200-£500 (unless faulty)
      
      NO REFUNDS for:
      - Personalized/custom items
      - Hygiene products once opened (underwear, earbuds, cosmetics)
      - Digital downloads or software after activation
      - Items damaged by customer misuse
      - Items without proof of purchase
      
      WARRANTY COVERAGE (Based on Item Price):
      
      Under £50:
      - 12-month manufacturer warranty
      - Covers manufacturing defects only
      - No accidental damage coverage
      
      £50 - £200:
      - 12-month manufacturer warranty
      - Optional extended warranty available (£10-30 depending on item)
      - Covers manufacturing defects and hardware failures
      
      Over £200:
      - 24-month manufacturer warranty (EU law compliance)
      - Optional extended warranty available (£30-100)
      - Covers manufacturing defects, hardware failures, and some wear-and-tear
      
      WARRANTY VOID IF:
      - Physical damage (drops, liquid damage, impact)
      - Unauthorized repairs or modifications
      - Normal wear and tear (for items under £200)
      - Used for commercial purposes (if sold for personal use)
      - Proof of purchase cannot be provided
      
      FAULTY ITEMS:
      - Full refund or replacement within 30 days of receipt
      - After 30 days: repair or replacement (no refund)
      - We cover ALL return shipping for faulty items
      - Faults must be reported within warranty period
      
      PROCESS:
      - Refunds processed within 3-5 business days after receiving return
      - Returns initiated online via account or customer service
      - Order number or receipt required for all returns/warranty claims
      
      IMPORTANT RULES:
      - Always ask for: item category, price, purchase date, and condition
      - Be helpful but firm about policy limits
      - If customer mentions damage, determine if it's manufacturing defect or user damage
      - Escalate to supervisor if customer spent over £1000 or has special circumstances
    """
    
    # Get the user's question from the most recent HumanMessage
    user_message = next((m.content for m in reversed(state["messages"]) 
                        if isinstance(m, HumanMessage)), "")
    
    # Create policy-specialized LLM call
    policy_messages = [
        SystemMessage(content=policy_context),
        HumanMessage(content=user_message)
    ]
    
    policy_response = llm.invoke(policy_messages)
    
    # Only return new message - pdf_bytes persists automatically
    return {"messages": [policy_response]}

# ------------------------------
# Classifier node
# ------------------------------

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
    all_msgs = "\n".join([m.content for m in state["messages"] if hasattr(m, "content")])
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

      Here is the full chat so far:
      {all_msgs}
      
      PDF text preview:
      \"\"\"{pdf_text_preview}\"\"\"

    """

    response = llm.invoke([HumanMessage(content=classifier_prompt)])
    classified = response.content.strip().lower()

    if classified not in ("sentiment", "design", "policy"):
        classified = "policy"

    # Build return dict - only keep PDF for design tasks
    result = {"next": classified}
    
    if classified != "design":
        result["pdf_bytes"] = None  # Explicitly clear it for non-design routes
    
    return result


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

        config = {"configurable": {"thread_id": thread_id}}

        # Get existing state from checkpoint
        existing_state = self.graph.get_state(config)
        
        # If there's existing state, append to existing messages
        if existing_state and existing_state.values.get("messages"):
            existing_messages = existing_state.values["messages"]
            new_messages = existing_messages + [HumanMessage(content=message)]
        else:
            # First message in thread
            new_messages = [HumanMessage(content=message)]

        # Invoke with accumulated messages
        result = self.graph.invoke({
            "messages": new_messages, 
            "pdf_bytes": pdf_bytes
        }, config)

        print("Current OverallState:", result)

        return result["messages"][-1].content