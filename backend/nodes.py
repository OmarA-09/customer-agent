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
    # print("") # for logging
    # print(response)
    # print("")
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

import logging
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def design_node(state: OverallState):
    logger.info("design_node invoked")

    pdf_bytes = state.get("pdf_bytes")
    if not pdf_bytes:
        logger.warning("No PDF document found in the state.")
        return {"messages": [AIMessage(content="No PDF document found in the state to extract from.")]}

    logger.info(f"PDF bytes size: {len(pdf_bytes)} bytes")

    prompt = (
        "You are an expert document extraction assistant.\n"
        "Extract structured data such as the table of contents, border details, "
        "and bill of materials from the PDF document provided. Return ONLY valid JSON."
    )
    logger.info(f"Prompt for Gemini: {prompt}")

    try:
        client = genai.Client()
        logger.info("GenAI client initialized")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                types.Part.from_text(text=prompt),
            ],
        )

        logger.info("Received response from Gemini model")
        logger.debug(f"Response text: {response.text}")

        # Try printing .text property explicitly
        extracted_text = getattr(response, "text", None)
        if extracted_text:
            logger.info(f"Extracted text length: {len(extracted_text)}")
            print(extracted_text)
        else:
            logger.warning("Response.text attribute is empty or missing.")
            # You can try to iterate parts if available
            try:
                parts = response.candidates[0].content.parts
                for part in parts:
                    print(part.text or repr(part.inline_data))
            except Exception as e:
                logger.error(f"Failed to read parts from response: {e}")

        return {"messages": [AIMessage(content=f"Extracted Data:\n{response.text}")]}

    except Exception as e:
        logger.error(f"Exception during Gemini call: {e}", exc_info=True)
        return {"messages": [AIMessage(content=f"Failed to extract data: {str(e)}")]}



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
