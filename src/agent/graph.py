from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from src.agent.state import MasterState
from src.agent.nodes import (
    dispatcher_node, gather_node, critic_node, 
    analyst_node, human_review_node, publisher_node
)
from src.agent.routing import (
    route_to_gatherers, route_after_critic, route_after_human
)
from src.logger import get_logger

logger = get_logger(__name__)

def build_master_graph():
    logger.info("Building the Alpha Syndicate Master Graph...")
    builder = StateGraph(MasterState)

    builder.add_node("dispatcher_node", dispatcher_node)
    builder.add_node("gather_node", gather_node)
    builder.add_node("critic_node", critic_node)
    builder.add_node("analyst_node", analyst_node)
    builder.add_node("human_review_node", human_review_node)
    builder.add_node("publisher_node", publisher_node)

    builder.add_edge(START, "dispatcher_node")
    
    builder.add_conditional_edges("dispatcher_node", route_to_gatherers)
    
    builder.add_edge("gather_node", "critic_node")
    
    builder.add_conditional_edges("critic_node", route_after_critic)
    
    builder.add_edge("analyst_node", "human_review_node")
    builder.add_conditional_edges("human_review_node", route_after_human)
    builder.add_edge("publisher_node", END)
    
    memory = InMemorySaver()

    return builder.compile(
        checkpointer=memory,
        interrupt_before=["human_review_node"]
    )

master_graph = build_master_graph()