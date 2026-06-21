import asyncio
import uuid
import argparse
import sys

from src.agent.graph import master_graph
from src.logger import get_logger

logger = get_logger(__name__)

async def run_syndicate(ticker: str, query: str):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_input = {
        "ticker": ticker,
        "user_query": query,
        "aggregated_research": [] 
    }

    print("\n" + "="*60)
    print(f"LAUNCHING ALPHA SYNDICATE FOR: {ticker}")
    print("="*60 + "\n")

    try:
        async for event in master_graph.astream(initial_input, config=config, stream_mode="values"):
            # We don't need to print the raw state
            pass
    except Exception as e:
        logger.error(f"Critical error during execution: {e}")
        sys.exit(1)

    current_state = master_graph.get_state(config)
    draft = current_state.values.get("draft_memo", "Error: No draft found.")

    print("\n" + "="*60)
    print("DRAFT MEMO READY FOR PORTFOLIO MANAGER REVIEW")
    print("="*60)
    print(draft)
    print("="*60 + "\n")

    print("Manager Action Required:")
    print(" - Type 'approve' to finalize the memo.")
    print(" - Type instructions (e.g., 'Add focus on Apple Car') for a rewrite.")
    
    user_input = input("\nManager Feedback: ").strip()

    if user_input.lower() == 'approve':
        logger.info("Draft approved by manager.")
        await master_graph.aupdate_state(
            config,
            {"human_approved": True, "feedback_loop_instruction": "None"},
            as_node="human_review_node" 
        )
    else:
        logger.info(f"Draft rejected. Feedback provided: {user_input}")
        await master_graph.aupdate_state(
            config,
            {
                "human_approved": False, 
                "feedback_loop_instruction": user_input,
                "aggregated_research": []
            },
            as_node="human_review_node"
        )
    
    print("\nRESUMING GRAPH & PUBLISHING FINAL MEMO...\n")
    
    async for event in master_graph.astream_events(None, config=config, version="v2"):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if chunk.content:
                print(chunk.content, end="", flush=True)
                
    print("\n\nMission Accomplished. Syndicate Offline.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Alpha Syndicate: Hedge Fund AI Agent")
    parser.add_argument(
        "--ticker", 
        type=str, 
        default="AAPL", 
        help="The stock ticker to research (e.g., AAPL, NVDA, TSLA)."
    )
    parser.add_argument(
        "--query", 
        type=str, 
        default="Analyze Apple (AAPL). Focus specifically on their upcoming AI hardware investments and whether it poses a threat to Nvidia.", 
        help="The specific strategic query for the AI to focus on."
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_syndicate(ticker=args.ticker, query=args.query))
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user. Exiting...")
        sys.exit(0)