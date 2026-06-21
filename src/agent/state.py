import operator
from typing import Annotated, Optional, TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

# --- Pydantic Models for Structured Output ---

class ResearchAvenues(BaseModel):
    """Used by the dispatcher to decide what to search for."""
    topics: list[str] = Field(
        description="A list of 3 specific research angles based on the user query"
    )

class CriticDecision(BaseModel):
    """Used by the Critic Agent to evaluate the gathered data."""
    is_sufficient: bool = Field(
        description="True if the data provides a solid, actionable foundation to draft the memo. Only set to False if CRITICAL, deal-breaking information is completely missing."
    )
    missing_information: Optional[str] = Field(
        description="If `is_sufficient` is False, explain exactly what critical data is missing. If True, leave it blank."
    )

# --- Graph States ---

class MasterState(TypedDict):
    ticker: str
    user_query: str
    aggregated_research: Annotated[list[str], operator.add]
    draft_memo: str
    feedback_loop_instruction: str
    research_topics: list[str]
    loop_count: Annotated[int, operator.add]
    human_approved: bool

class WorkerState(TypedDict):
    ticker: str
    user_query: str
    research_topic: str
    messages: Annotated[list[BaseMessage], add_messages]