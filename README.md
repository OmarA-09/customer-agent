# customer-agent

## Setup 

pip install -r requirements.txt


##















# Task

A customer-facing, front end interface where customers can submit a ticket in long-form text; The request should go through to an AI agent that determines which other AI agent to pipe the request through to (using the API). We expect requests generally to be one of 3 things; a review/complaint, a design document in pdf format, or a question about refunds/warranty for a product.

Reviews/complaints should go to a GCP model for sentiment analysis to determine whether it is a positive or negative review.

Design documents should go through to a Gemini endpoint. Gemini should return the dimensions of all fittings in a CSV-like format. It should be possible to ask Gemini questions about the schematics it has received already, e.g. "are there more cabinets in this bathroom than in the previous schematic?", "is this living room larger by floor area than the last one?"

And questions about refunds/warranty should go through to a third model prepped with company policy - you can come up with just a few points relating to let's say 3 products. Things like the length of the warranty and what sort of things might void it.

It's important that you track your projects with Git and upload to Github - since that's how we'll analyse them using Snyk to identify any security vulnerabilities.

send to maybe

- automl senimentanaysis
- deisgn document - pdf analysis

can have 3 products, feed the model it before it takes enquries 

long form memory in DB not needed.


https://cloud.google.com/natural-language/docs/basics#interpreting_sentiment_analysis_values

https://console.cloud.google.com/vertex-ai/publishers/google/model-garden/language-v1-analyze-sentiment?project=my-second-project-475209


# challenges, feedback, limitations

- sentiment_data.csv could have been used, had text sentiment analysis not been deprecated
  on GCP AutoML!

