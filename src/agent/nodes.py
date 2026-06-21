from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition

from src.config import get_llm
from src.logger import get_logger
from src.prompts import (
    WORKER_SYSTEM_PROMPT, DISPATCHER_SYSTEM_PROMPT, DISPATCHER_FEEDBACK_PROMPT,
    CRITIC_SYSTEM_PROMPT, ANALYST_SYSTEM_PROMPT, PUBLISHER_SYSTEM_PROMPT
)
from src.agent.state import MasterState, WorkerState, ResearchAvenues, CriticDecision
from src.tools import ALL_TOOLS

logger = get_logger(__name__)
llm = get_llm()

# --- Subgraph Setup for the Worker ---

llm_with_tools = llm.bind_tools(tools=ALL_TOOLS, tool_choice="auto")

async def worker_llm_node(state: WorkerState) -> dict:
    response = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": [response]}

def build_worker_subgraph():
    builder = StateGraph(WorkerState)
    builder.add_node("llm", worker_llm_node)
    builder.add_node("tools", ToolNode(ALL_TOOLS))
    builder.add_edge(START, "llm")
    builder.add_conditional_edges("llm", tools_condition)
    builder.add_edge("tools", "llm")
    return builder.compile()

worker_graph = build_worker_subgraph()

# --- Master Graph Nodes ---

async def dispatcher_node(state: MasterState) -> dict:
    logger.info("--- Dispatcher: Planning Research ---")
    planner_llm = llm.with_structured_output(ResearchAvenues)

    sys_msg = DISPATCHER_SYSTEM_PROMPT.format(ticker=state["ticker"])
    
    if state.get("feedback_loop_instruction") and state["feedback_loop_instruction"] != "None":
        sys_msg += "\n" + DISPATCHER_FEEDBACK_PROMPT.format(feedback=state['feedback_loop_instruction'])

    prompt = ChatPromptTemplate.from_messages([("system", sys_msg), ("human", "{user_query}")])

    plan: ResearchAvenues = await planner_llm.ainvoke(prompt.invoke({
        "user_query": state["user_query"]
    }))

    logger.debug(f"Generated Avenues: {plan.topics}")
    return {
        "research_topics": plan.topics,
        "loop_count": 1
    }

async def gather_node(state: WorkerState) -> dict:
    logger.info(f"--- Gatherer: Investigating '{state['research_topic']}' ---")
    
    sys_msg = SystemMessage(
        content=WORKER_SYSTEM_PROMPT.format(
            topic=state["research_topic"], 
            ticker=state["ticker"]
        )
    )

    result: WorkerState = await worker_graph.ainvoke({
        "ticker": state["ticker"],
        "user_query": state["user_query"],
        "research_topic": state["research_topic"],
        "messages": [sys_msg]
    })

    final_msg = result["messages"][-1].content
    formatted_finding = f"### {state['research_topic']} ###\n{final_msg}\n"
    
    return {"aggregated_research": [formatted_finding]}

async def critic_node(state: MasterState) -> dict:
    logger.info("--- Critic: Evaluating Research ---")
    critic_llm = llm.with_structured_output(CriticDecision)
    all_search = "\n\n".join(state.get("aggregated_research", []))

    prompt = ChatPromptTemplate.from_messages([
        ("system", CRITIC_SYSTEM_PROMPT),
        ("human", "User Request: {user_query}\n\nAggregated Research:\n{research}")
    ])

    evaluation: CriticDecision = await critic_llm.ainvoke(
        prompt.invoke({"user_query": state["user_query"], "research": all_search})
    )

    logger.debug(f"Critic Decision - Sufficient: {evaluation.is_sufficient}")
    if not evaluation.is_sufficient:
        logger.warning(f"Critic Feedback: {evaluation.missing_information}")
    
    return {
        "feedback_loop_instruction": evaluation.missing_information if not evaluation.is_sufficient else "None"
    }

async def analyst_node(state: MasterState) -> dict:
    logger.info("--- Analyst: Drafting Investment Memo ---")
    all_research = "\n\n".join(state.get("aggregated_research", []))

    prompt = ChatPromptTemplate.from_messages([
        ("system", ANALYST_SYSTEM_PROMPT),
        ("human", "Target Asset: {ticker}\nUser's Strategic Focus: {user_query}\n\nVerified Research Data:\n{research}")
    ])

    response = await llm.ainvoke(prompt.format_messages(
        ticker=state["ticker"],
        user_query=state["user_query"],
        research=all_research
    ))

    return {"draft_memo": response.content}

async def human_review_node(state: MasterState):
    """Dummy node. Interruption happens BEFORE this node executes."""
    logger.info("--- HUMAN REVIEW CHECKPOINT ---")
    pass

async def publisher_node(state: MasterState) -> dict:
    logger.info("--- PUBLISHER: Formatting Final Output ---")
    prompt = ChatPromptTemplate.from_messages([
        ("system", PUBLISHER_SYSTEM_PROMPT),
        ("human", "{draft}")
    ])
    
    chain = prompt | llm 
    response = await chain.ainvoke({"draft": state["draft_memo"]})
    return {"draft_memo": response.content}