# customer-agent

## Setup

### Backend

`pip install -r requirements.txt`

## Overview / Task

This project implements a customer-facing interface where customers can submit a long-form ticket via a front end. The request is analyzed by an AI routing agent backend which routes the request to one of three specialized AI models:

1. **Reviews/Complaints**: Sent to a Google Cloud Platform (GCP) sentiment analysis model. This model evaluates whether the user’s review or complaint is positive or negative.

2. **Design Documents**: PDF design documents are sent to a Gemini AI endpoint. Gemini analyzes the schematics, returning detailed dimensions in a CSV-like format. Users can also query Gemini about previously submitted schematics, e.g., "are there more cabinets in this bathroom than in the previous schematic?" or "is this living room larger by floor area than the last one?"

3. **Warranty/Refund Questions**: Sent to a third AI model trained on company policy related to three sample products, covering warranty length and void conditions.

---

## Architecture & Components

- **Frontend**: React-based chat UI with file upload (PDF) capability and markdown support from AI responses.

- **Backend**: Python backend using LangGraph to build a StateGraph with nodes for classification, sentiment, design, and policy processing. Routes messages dynamically based on detected intent.

- **AI Models**:
  - GCP AutoML Sentiment Analysis for reviews (though deprecated, referenced for context).
  - Gemini for design document analysis & question answering.
  - Custom policy model for warranty/refund questions.

- **Graph & Agent**: RoutingAgent uses LangGraph runtime with optional memory checkpointing.

---

## Environment Configuration

To run with custom checkpointing enabled (default), set in your `.env`:

`USE_CUSTOM_CHECKPOINT=true`

If you want to run the project in **LangSmith Studio**, you should disable the custom checkpoint to allow LangSmith to manage checkpointing:

`USE_CUSTOM_CHECKPOINT=false`


---

## Notes and References

- Sentiment analysis values guide:  
  https://cloud.google.com/natural-language/docs/basics#interpreting_sentiment_analysis_values

- GCP Vertex AI Example Sentiment Model:  
  https://console.cloud.google.com/vertex-ai/publishers/google/model-garden/language-v1-analyze-sentiment?project=my-second-project-475209

---

## Challenges and Limitations

- GCP AutoML sentiment analysis API has been deprecated, preventing use of `sentiment_data.csv` or direct text sentiment models.
- Long-term memory persistence was not required; the system uses in-memory state and message history for context.
- Flexible routing required careful design of multi-turn flows, especially for document querying.

---

## Git & Security

- The project should be managed under Git and pushed to GitHub.
- Use automated code scanning (e.g., Snyk) to monitor for security vulnerabilities.