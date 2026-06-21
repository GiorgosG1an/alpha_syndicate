from langgraph.types import Send
from src.agent.state import MasterState
from src.logger import get_logger

logger = get_logger(__name__)

def route_to_gatherers(state: MasterState) -> list[Send]:
    """Dynamically fans out to parallel worker nodes."""
    topics = state.get("research_topics", [])
    logger.info(f"Fanning out to {len(topics)} gather nodes...")
    
    return [
        Send(
            node="gather_node",
            arg={
                "ticker": state["ticker"],
                "user_query": state["user_query"],
                "research_topic": topic
            }
        ) for topic in topics
    ]

def route_after_critic(state: MasterState) -> str:
    """Routes to Analyst if sufficient, or back to Dispatcher if missing data."""
    current_loops = state.get("loop_count", 0)
    
    if current_loops >= 2:
        logger.warning(f"Max loops reached ({current_loops}). Forcing route to Analyst_node.")
        return "analyst_node"
    
    if state.get("feedback_loop_instruction") and state["feedback_loop_instruction"] != "None":
        logger.info("Missing data detected. Routing back to Dispatcher_node...")
        return "dispatcher_node"
    
    logger.info("Data sufficient. Routing to Analyst_node...")
    return "analyst_node"

def route_after_human(state: MasterState) -> str:
    """Routes based on the Portfolio Manager's decision."""
    if state.get("human_approved"):
         logger.info("Human approved draft. Routing to Publisher_node...")
         return "publisher_node"
    
    logger.info("Human rejected draft. Routing back to Dispatcher_node with new instructions...")
    return "dispatcher_node"