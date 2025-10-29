from typing import Optional
from langchain_core.messages import HumanMessage

class RoutingAgent:
    def __init__(self, graph):
        self.graph = graph

    def handle_message(self, message: str, thread_id: str, pdf_path: Optional[str] = None):
        pdf_bytes = None
        if pdf_path:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

        config = {"configurable": {"thread_id": thread_id}}
        existing_state = self.graph.get_state(config)

        if existing_state and existing_state.values.get("messages"):
            existing_messages = existing_state.values["messages"]
            new_messages = existing_messages + [HumanMessage(content=message)]
        else:
            new_messages = [HumanMessage(content=message)]

        result = self.graph.invoke({
            "messages": new_messages,
            "pdf_bytes": pdf_bytes
        }, config)

        print("Current OverallState:", result)

        return result["messages"][-1].content
