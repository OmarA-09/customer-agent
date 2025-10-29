from typing import TypedDict, List, Optional, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

class OverallState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    pdf_bytes: Optional[bytes]
    next: Optional[str]
