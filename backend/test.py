from routing_agent import RoutingAgent

agent = RoutingAgent()
thread_id = "test_thread_1"

messages = [
    "This is a positive review of your product.",
    "Here is a design document PDF I need analyzed.",
    "What is the refund policy for product X?"
]

for msg in messages:
    response = agent.handle_message(msg, thread_id)
    print(f"Input: {msg}\nResponse: {response}\n")
