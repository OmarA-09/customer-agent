from routing_agent import RoutingAgent

agent = RoutingAgent()
thread_id = "test_thread_1"

# messages = [
#     "This is a positive review of your product.",
#     "Here is a design document PDF I need analyzed.",
#     "What is the refund policy for product X?"
# ]

# for msg in messages:
#     response = agent.handle_message(msg, thread_id)
#     print(f"Input: {msg}\nResponse: {response}\n")

# print("---- Complaint ----")
# print(agent.handle_message("I'm unhappy with my chair quality", thread_id="1"))

# # ---- Test 2: Text-only warranty question ----
# print("---- Warranty ----")
# print(agent.handle_message("What is the warranty period for the sofa?", thread_id="2"))

'''

testing PDF upload to see if it correctly classifies

works even if the message is empty because pdf preview is passed to LLM

'''

# ---- Test 3: PDF design document ----
print("---- DESIGN PDF ----")
print(agent.handle_message(
    "Please analyze this drawing for cabinet dimensions",
    thread_id="3",
    pdf_path="./pdfs/Millwork_example.pdf"   # path to your test PDF
))

print("---- GOOD REVIEW PDF ----")
print(agent.handle_message(
    "",
    thread_id="4",
    pdf_path="./pdfs/review_.pdf"   # path to your test PDF
))

print("---- WARRANTEE PDF ----")
print(agent.handle_message(
    "",
    thread_id="4",
    pdf_path="./pdfs/warrantee_request.pdf"   # path to your test PDF
))

