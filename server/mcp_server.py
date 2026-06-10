import os
import sys
from fastmcp import FastMCP
from database.graph_repository import GraphRepository

# 1. Initialize the FastMCP server instance
mcp = FastMCP("MedChain Knowledge Graph")

# 2. Establish a global connection pool to the Neo4j database
try:
    # This automatically picks up the NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD from the environment
    repo = GraphRepository()
except Exception as e:
    print(f"CRITICAL ERROR: Failed to connect to Neo4j graph database: {e}", file=sys.stderr)
    sys.exit(1)

# 3. Define our first simple MCP Tool using a decorator
@mcp.tool()
def get_graph_status() -> str:
    """
    A foundational health-check tool. Use this to verify the MCP server 
    can successfully read from the underlying Neo4j supply chain database.
    """
    try:
        with repo.driver.session() as session:
            # Execute a safe, read-only Cypher query to count the total nodes
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            count = result.single()["node_count"]
            return f"MedChain Graph is fully operational. Total nodes currently in ontology: {count}"
    except Exception as e:
        return f"Database read error: {str(e)}"

if __name__ == "__main__":
    # 4. Start the MCP server using Standard Input/Output (stdio) transport
    print("Initializing MedChain MCP Server via stdio...", file=sys.stderr)
    try:
        mcp.run()
    finally:
        # Ensure the database connections are closed gracefully if the server shuts down
        repo.close()