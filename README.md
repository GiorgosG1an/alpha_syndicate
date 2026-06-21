# Alpha Syndicate: Multi-Agent Financial Research System

A Python-based multi-agent architecture built with LangGraph to orchestrate asynchronous financial research, evaluation, and report generation. 

This project demonstrates advanced LLM orchestration patterns, including **Map-Reduce (Fan-out/Fan-in)**, **Human-In-The-Loop (HITL)** state management backed by a PostgreSQL database, and **Structured Data Extraction** using Pydantic.

## System Architecture

The system utilizes a Directed Acyclic Graph (DAG) to manage state across multiple specialized LLM agents. 

```mermaid
graph TD
    START((START)) --> Dispatcher[Dispatcher Node]
    
    Dispatcher -->|Generates N Topics| Gatherer1[Gatherer Node 1]
    Dispatcher --> Gatherer2[Gatherer Node 2]
    Dispatcher --> GathererN[Gatherer Node N]
    
    Gatherer1 --> Critic[Critic Node]
    Gatherer2 --> Critic
    GathererN --> Critic
    
    Critic -->|Missing Data?| Dispatcher
    Critic -->|Data Sufficient| Analyst[Analyst Node]
    
    Analyst --> Human[Human Review Checkpoint]
    
    Human -->|Rejected + Feedback| Dispatcher
    Human -->|Approved| Publisher[Publisher Node]
    
    Publisher --> END((END))
```

### Key Technical Patterns
* **Dynamic Fan-Out (Map-Reduce):** The Dispatcher analyzes the user query and generates distinct research avenues. The graph dynamically spawns parallel `gather_node` workers for each topic using LangGraph's `Send` API.
* **Persistent Fault-Tolerant State (PostgreSQL):** Graph execution is suspended at the `human_review_node`. Thread state is persisted asynchronously in a local Dockerized PostgreSQL database using `AsyncPostgresSaver`. This allows long-running executions to safely pause and resume without data loss, enabling a user to inject feedback or approve the draft days later.
* **Asynchronous Tool Calling:** I/O bound tasks (`yfinance` API calls and `DuckDuckGo` web searches) are executed asynchronously (`asyncio.to_thread`) to prevent blocking the event loop during parallel agent execution.
* **Structured Output Parsing:** Enforces strict JSON schemas via Pydantic (`CriticDecision`, `ResearchAvenues`) to ensure deterministic routing logic between graph edges.

## Project Structure

```text
alpha-syndicate/
├── docker-compose.yml       # PostgreSQL container for state persistence
├── src/
│   ├── main.py              # CLI entry point
│   ├── config.py            # Environment & LLM configuration
│   ├── logger.py            # Centralized Loguru configuration
│   ├── prompts.py           # Decoupled system prompts
│   ├── tools/
│   │   ├── finance.py       # yfinance integration
│   │   └── search.py        # DuckDuckGo search wrapper
│   └── agent/
│       ├── state.py         # TypedDict and Pydantic schemas
│       ├── nodes.py         # LLM agent definitions
│       ├── routing.py       # Conditional edge logic
│       └── graph.py         # StateGraph compilation
├── tests/                   # Pytest suite
├── pyproject.toml           # Dependency management
└── README.md
```

## Installation & Setup

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/alpha-syndicate.git
cd alpha-syndicate
```

**2. Install dependencies**
Ensure you have Python >= 3.10 installed.
```bash
pip install -e .
# OR if using Poetry:
poetry install
```

**3. Environment Variables**
Create a `.env` file in the root directory. The system requires an LLM API key and Database credentials.
```env
# LLM Configuration
DASHSCOPE_API_KEY=your_api_key_here

# Database Credentials
POSTGRES_USER=alpha_user
POSTGRES_PASSWORD=SuperSecretPassword123
POSTGRES_DB=alpha_syndicate
DATABASE_URL=postgresql://alpha_user:SuperSecretPassword123@localhost:5433/alpha_syndicate
```

**4. Start the Database**
Spin up the PostgreSQL instance via Docker. LangGraph handles the necessary schema migrations automatically on the first run.
```bash
docker-compose up -d
```

## Usage

The application is executed via a Command Line Interface (CLI). 

```bash
python -m src.main --ticker AAPL --query "Analyze Apple's upcoming AI hardware investments and supply chain risks."
```

### CLI Arguments
| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--ticker` | `str` | `AAPL` | The target stock ticker symbol. |
| `--query` | `str` | *(Pre-set)* | The specific strategic query for the research agents to focus on. |

### Interactive Execution Flow
1. **Research Phase:** Standard `INFO` logs are printed as the Dispatcher creates topics and parallel Gatherers fetch live data.
2. **Review Pause:** The graph suspends execution, saves the state to Postgres, and outputs a Markdown Draft Memo.
3. **Manager Feedback:** You will be prompted in the terminal.
   - Type `approve` to finalize and stream the formatted output.
   - Type specific feedback (e.g., *"You missed their Q3 earnings, focus on that"*) to wipe the current research, route back to the Dispatcher, and restart the Map-Reduce loop with the new instructions.

## Future Enhancements
- **FastAPI Migration:** Wrap the graph execution in a REST API, utilizing Server-Sent Events (SSE) to stream tokens and state updates to a frontend interface.
- **Observability:** Integrate LangSmith or OpenTelemetry to track token usage, tool failure rates, and latency across nodes.
- **CI/CD Pipeline:** Implement GitHub Actions for automated testing and linting.
