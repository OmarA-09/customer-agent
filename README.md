# customer-agent

## Setup

### Backend

`python -m venv venv`

`source venv/bin/activate`

`pip install -r requirements.txt`

`flask run`

### Frontend

`npm install`

`npm run dev`

### setup env vars

LANGSMITH_API_KEY
LANGSMITH_TRACING
LANGSMITH_PROJECT

OPENAI_API_KEY
<!-- Flase if using Langgraph Studio, false otherwise -->
USE_CUSTOM_CHECKPOINT
<!-- for sentiment analysis -->
GOOGLE_APPLICATION_CREDENTIALS=gcloudNLKey.json
<!-- API key for Gemini model access for design documents -->
GEMINI_API_KEY

## Overview / Task

This project implements a customer-facing interface where customers can submit a long-form ticket via a front end. The request is analysed by an AI routing agent backend which routes the request to one of three specialised AI models:

1. **Reviews/Complaints**: Sent to a Google Cloud Platform (GCP) sentiment analysis model. This model evaluates whether the user’s review or complaint is positive or negative.

2. **Design Documents**: PDF design documents are sent to a Gemini AI endpoint. Gemini analyses the schematics, returning detailed dimensions in a CSV-like format. Users can also query Gemini about previously submitted schematics, e.g., "are there more cabinets in this bathroom than in the previous schematic?" or "is this living room larger by floor area than the last one?"

3. **Warranty/Refund Questions**: Sent to a third AI model trained on company policy related to three sample products, covering warranty length and void conditions.


## Architecture & Components

- **Frontend**: React-based chat UI with file upload (PDF) capability and markdown support from AI responses.

- **Backend**: Python backend using LangGraph to build a `StateGraph` with nodes for classification, sentiment, design, and policy processing. Routes messages dynamically based on detected intent.

- **Custom State Management**: The project uses a custom `OverallState` typed dict combined with a `reducer` function to append messages to the conversation state automatically.

- **AI Models**:
  - OpenAI model 4o for routing 
  - VertexAI Model Garden Sentiment Analysis model for reviews (AutoML sentiment training deprecated, referenced for context).
  - Gemini for design document analysis & question answering.
  - OpenAI model 4o for warranty/refund questions.

- **Graph & Agent**: `RoutingAgent` uses LangGraph runtime with optional memory checkpointing. The custom overall state and reducer enable seamless state mutation and message handling.

## Environment Configuration

To run with custom checkpointing enabled (default), set in your `.env`:

`USE_CUSTOM_CHECKPOINT=true`

If you want to run the project in **LangSmith Studio**, you should disable the custom checkpoint to allow LangSmith to manage checkpointing:

`USE_CUSTOM_CHECKPOINT=false`

`langgraph dev`

## Notes and References

- Sentiment analysis values guide:  
  https://cloud.google.com/natural-language/docs/basics#interpreting_sentiment_analysis_values

- GCP Vertex AI Example Sentiment Model:  
  https://console.cloud.google.com/vertex-ai/publishers/google/model-garden/language-v1-analyze-sentiment?project=my-second-project-475209

## Git & Security

- The project should be managed under Git and pushed to GitHub.
- Use automated code scanning (e.g., Snyk) to monitor for security vulnerabilities.

## Challenges and Limitations

- GCP AutoML sentiment analysis API has been deprecated, preventing use of `sentiment_data.csv` or direct text sentiment models.
- Long-term memory persistence was not required; the system uses in-memory state and message history for context.
- Flexible routing required careful design of multi-turn flows, especially for document querying. 

## Improvements

- Avoid passing PDFBYTES into messages -> perhaps a custom reducer function
- Having a context window or "summarise all prev convo" selectively.
- structures responses with Langgraph - useful for JSON output
- Implement Human-in-the-loop/time travel for pdfs
- Deployment, handling double texting
- Make use of Tavily search