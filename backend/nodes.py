import io
from typing import Optional
from PyPDF2 import PdfReader
import pdf2image
import pytesseract
from PIL import Image
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from custom_state import OverallState
from langchain_openai import ChatOpenAI

from google.cloud import language_v1
import six

def sentiment_node(state: OverallState):
    # Extract the last human message text
    content = next((m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), "")

    client = language_v1.LanguageServiceClient()

    if isinstance(content, six.binary_type):
        content = content.decode("utf-8")

    document = {"type_": language_v1.Document.Type.PLAIN_TEXT, "content": content}

    response = client.analyze_sentiment(request={"document": document})
    sentiment = response.document_sentiment

    score = sentiment.score
    magnitude = sentiment.magnitude

    # Simple classification based on score, customize thresholds as needed
    if score >= 0.25:
        label = "Positive"
    elif score <= -0.25:
        label = "Negative"
    else:
        label = "Neutral"

    result_text = f"Sentiment analysis result: Score={score:.2f}, Magnitude={magnitude:.2f}, Classified as {label}"

    return {"messages": [AIMessage(content=result_text)]}

# Design document processing node (dummy)
def design_node(state):
    return {"messages": [AIMessage(content="Design doc processed with extracted dimensions (dummy).")]}


# Policy node using specialized LLM call
def policy_node(state):
    llm = ChatOpenAI(model="gpt-4o")  # Adjust or pass as argument if needed

    policy_context = """You are a customer service agent for a major online retailer (similar to Amazon/Argos).
    ... (include full policy text as in original) ...
    """

    user_message = next((m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), "")

    policy_messages = [
        SystemMessage(content=policy_context),
        HumanMessage(content=user_message)
    ]

    policy_response = llm.invoke(policy_messages)

    return {"messages": [policy_response]}


# Extract text from PDF using PyPDF2 first, then OCR fallback
def extract_text_from_pdf(pdf_bytes: bytes, max_chars: int = 800) -> str:
    text = ""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text
            if len(text) >= max_chars:
                break

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


# Classifier node for routing
def classifier_node(state):
    llm = ChatOpenAI(model="gpt-4o")  # Adjust or pass as argument if needed

    all_msgs = "\n".join([m.content for m in state["messages"] if hasattr(m, "content")])
    pdf_bytes = state.get("pdf_bytes")

    pdf_text_preview = extract_text_from_pdf(pdf_bytes) if pdf_bytes else ""

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

    result = {"next": classified}

    if classified != "design":
        result["pdf_bytes"] = None

    return result
