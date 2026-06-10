import os
import sys
from pipeline.ingestion_runner import run_multimodal_ingestion_pipeline
from database.graph_repository import GraphRepository

def main():
    """
    Main orchestration entrypoint for Phase 2:
    1. Extracts and normalizes data from raw documents using the GenAI pipeline.
    2. Opens a safe connection to the Neo4j database.
    3. Hydrates the graph topology transactionally.
    """
    print("========================================================================")
    print("INITIALIZING MEDCHAIN KNOWLEDGE GRAPH PIPELINE")
    print("========================================================================\n")

    # 1. Environment Gatekeeper
    # Ensure critical API keys and database connections are present before firing
    required_envs = ["GEMINI_API_KEY", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]
    missing = [var for var in required_envs if var not in os.environ]
    
    if missing:
        print(f"CRITICAL ERROR: Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        print("Please check your .env file and docker-compose.yml configuration.", file=sys.stderr)
        sys.exit(1)

    # 2. Execute Extraction & Normalization
    try:
        # This returns the fully deduplicated, Pydantic-validated payload
        master_payload = run_multimodal_ingestion_pipeline()
    except Exception as e:
        print(f"\n[ERROR] Pipeline extraction failed: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Execute Database Hydration
    print("\n[PROCESSING] Connecting to Neo4j to hydrate the graph database...")
    repo = None
    try:
        # Instantiate the database repository using the default dev database URI
        repo = GraphRepository()
        
        # Hydrate the graph using the transactional upsert methods
        repo.hydrate_supply_chain_pipeline(master_payload)
        
        print("\n========================================================================")
        print("GRAPH HYDRATION COMPLETE!")
        print("========================================================================")
        
    except Exception as e:
        print(f"\n[ERROR] Graph database hydration failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Always ensure the database driver pool is closed safely
        if repo:
            repo.close()

if __name__ == "__main__":
    main()