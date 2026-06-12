## MedChain-MCP: Agentic Knowledge Graph & MCP Server for Healthcare Supply Chain Ontologies

This production-grade repository implements a local, containerized pipeline that ingests chaotic, multi-modal healthcare supply chain data, uses a Large Language Model (LLM) to extract and validate data against a strict ontology, structures it into a Neo4j graph database, and exposes that graph dynamically to an autonomous AI agent via a Model Context Protocol (MCP) server.

---

### ## Project Architecture & Data Flow

The diagram below details the end-to-end data lifecycle of the application—from multi-format raw data ingestion through deterministic validation layers to real-time agentic query tool execution.

```
[ Raw Multi-Modal Data ]
   │  - Vendor Contract (.txt)
   │  - Tabular Invoice (.csv)
   │  - Manufacturer Catalog (.json)
   ▼
[ Sequential Hybrid Preprocessing Layer ]
   │  - Regex Suffix & Punctuation Stripper (Python)
   │  - RapidFuzz / Levenshtein Distance Matrix vs. Master List
   ▼
[ Google Gemini 2.5 Flash Extraction Engine ]
   │  - Prompt-Injected Pydantic Schema Validation (Bypassing SDK $defs bug)
   │  - Strict type-enforced parsing into uniform JSON payloads
   ▼
[ Graph Hydration Layer (GraphRepository) ]
   │  - Idempotent, parameterized Cypher MERGE operations
   ▼
┌─────────────────── /app Docker Container Network Workspace ───────────────────┐
│                                                                               │
│   [ Neo4j Community Instance ] ◄───► [ Standalone FastMCP Server Engine ]     │
│    (Persistent Data Volumes)         (Global Bolt Connection Pooling)         │
│                                                     ▲                         │
└─────────────────────────────────────────────────────┼─────────────────────────┘
                                                      │  Model Context Protocol
                                                      │  (STDIO Transport Layer)
                                                      ▼
                                            [ Autonomous AI Agent ]
                                               - State-Managed Chat Loop
                                               - Real-Time Tool Execution
                                               - Strategic Procurement Reports

```

---

### ## Core System Technical Capabilities

* **Multi-Modal Ingestion Pipeline:** Consolidates raw narrative text , flat spreadsheet logs , and deep JSON properties into a unified intake flow.


* **Sequential Hybrid Entity Resolution:** Minimizes non-deterministic LLM hallucinations and graph database fragmentation by routing messy corporate titles through a fast custom Python Regex cleaner combined with a rapid C++ optimized Levenshtein distance string matching algorithm (`RapidFuzz`).


* **Idempotent Schema Protection:** Implements strict Neo4j 5 unique constraints tied directly to parameterized, fallback-resilient Cypher operations (`ON CREATE SET` / `ON MATCH SET`). This ensures that multiple pipeline runs sync variables smoothly without fabricating duplicating sub-islands or causing database write deadlocks.


* **Fuzzy Agent-Friendly Tooling:** Exposes analytical tools via the `FastMCP` schema standard that leverage `toLower()` and `CONTAINS` query logic , allowing autonomous models to interact with complex topologies without guessing explicit primary database keys.


* **Advanced Procurement Resilience Logic:** Implements an automated clinical fallback matrix. If a critical asset experiences a vendor shortage, tools query specific physical packaging substitutes via `POTENTIAL_SUBSTITUTE_FOR` ; if missing, they gracefully fall back using `OPTIONAL_MATCH` queries to scan hierarchical industry-standard classifications via the `UNSPSC_Category` tier.


* **Multi-Tier Continuous Integration Testing:** Features a robust automated test ecosystem split between instant, isolated unit testing (mocking database drivers via `unittest.mock`) and true container-networked database integration suites (`test_graph_repository_it.py`) , paired with an explicit, parameter-driven **EvalOps pipeline** (`test_evalops.py`) that utilizes an LLM-as-a-Judge script to grade agent trajectories and facts against a strict metric rubric.



---

### ## Project Execution File Tree

```text
medchain-mcp/
├── .env                         # Local encrypted environment properties (Untracked)
├── .gitignore                   # Safe configuration exclude rules
├── docker-compose.yml           # Multi-container network and persistent storage volumes
├── Dockerfile                   # Isolated Python 3.12, virtualenv, Node.js, & MCP configuration
├── requirements.txt             # Pinned top-level system tech dependencies
├── requirements-test.txt        # Isolated testing framework pins
├── main.py                      # Master pipeline ingestion execution coordinator
├── client.py                    # Autonomous stateful AI Agent orchestrator
├── setup_schema.py              # Unique data constraints database builder
├── test_setup_schema.py         # Mock database constraint configuration tests
├── test_preprocessing.py        # Exhaustive validation mapping tests for hybrid strings
├── test_ingestion.py            # Stable file structure check validation tests
├── test_extraction_engine.py    # Offline Mock Gemini client schema tests
├── test_ingestion_runner.py     # End-to-end file loop aggregation tests
├── test_graph_repository_it.py  # Live containerized database write integration tests
├── test_mcp_server.py           # Multi-branch logic analytical tool unit tests
├── test_integration.py          # Live production-ready database volume checks
├── test_evalops.py              # Three-Pillar golden dataset & LLM-Judge evaluation suite
├── data/
│   ├── vendor_contract.txt      # Raw narrative provider document snippet
│   ├── invoice_raw.csv          # Messy flat supplier accounting record
│   └── manufacturer_catalog.json# Nested corporate catalog data
├── database/
│   └── graph_repository.py      # Parametrical data access layer abstraction module
├── pipeline/
│   ├── preprocessing.py         # Advanced entity resolution cleaning modules
│   ├── ingestion.py             # Basic directory asset content validators
│   ├── extraction_engine.py     # Custom schema string-prompt engine mechanics
│   └── ingestion_runner.py      # Local file coordinator and parsing engine
├── schemas/
│   └── extraction.py            # Type-safe object graph schemas (Pydantic v2)
└── server/
    └── mcp_server.py            # High-level FastMCP engine analytics routing setup

```

---

### ## Quickstart Deployment Guide

#### 1. Environment Setup

Clone the codebase and navigate to the project directory:

```bash
git clone https://github.com/mcjankousky/medchain-mcp.git
cd medchain-mcp

```

Create a local, untracked `.env` file in the root folder to house database and cloud resource keys safely:

```env
NEO4J_PASSWORD=ReplaceThisWithYourSecurePassword_123
GOOGLE_API_KEY=AIzaSyYourSecretGeminiTokenHere

```

#### 2. Build the System Infrastructure

Compile the completely isolated multi-container runtime environment, including specialized global dependencies like the Anthropic MCP Inspector and Node.js:

```bash
docker-compose build --no-cache

```

#### 3. Initialize the Graph Database & Load Data

Spin up the background database clusters, automatically implement uniqueness data constraints , and execute the full structured extraction extraction pipeline to ingest all raw text, tables, and nested catalog assets:

```bash
# Start background services
docker-compose up -d

# Run the master data ingestion and graph hydration pipeline
docker-compose run --rm app python main.py

```

#### 4. Run the Continuous Integration & EvalOps Test Suites

Verify all layers of code syntax logic, string fuzzy match normalization mappings, live container connection states, database persistence capabilities, and agent trajectory evaluations:

```bash
# Execute the entire comprehensive automated testing ecosystem
docker-compose run --rm app pytest -v -s

```

#### 5. Launch the Local Interactive MCP Inspector Debugger

Fire up the local dark-mode development UI server panel on port `6274` to visually run queries against your exposed analytical graph tools:

```bash
docker-compose run --rm -e HOST=0.0.0.0 -p 6274:6274 -p 6277:6277 app fastmcp dev inspector server/mcp_server.py

```

*Windows Quirks Note:* Open your browser and navigate to the localhost equivalent token link printed in your console terminal:
`http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=your_unique_session_token` 

#### 6. Execute the Autonomous AI Agent Client

Launch the state-managed loop client execution script. This instructs the agent to autonomously detect available graph tools, query localized supply networks, inspect packaging replacements during simulated supplier shortfalls, and generate professional strategic procurement reports:

```bash
docker-compose run --rm app python client.py

```
