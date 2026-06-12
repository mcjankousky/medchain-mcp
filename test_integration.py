import pytest

# Import the health-check tool we built
from server.mcp_server import get_graph_status

def test_database_is_hydrated():
    """
    INTEGRATION TEST: Verifies that the live Neo4j database is accessible 
    and has been successfully hydrated with Phase 2 supply chain data.
    """
    # 1. Execute the actual tool against the live database
    result = get_graph_status()
    
    # 2. Verify we didn't get a connection error
    assert "Database read error" not in result, f"Failed to connect to Neo4j: {result}"
    assert "MedChain Graph is fully operational" in result
    
    # 3. Extract the node count from the string
    # Expected string format: "... Total nodes currently in ontology: 150"
    try:
        count_str = result.split(":")[-1].strip()
        node_count = int(count_str)
    except ValueError:
        pytest.fail(f"Could not parse node count from result string: {result}")
        
    # 4. The ultimate test: Are there nodes?
    assert node_count > 0, "Graph is connected but EMPTY! Run main.py to hydrate."
    
    print(f"\n✅ Hydration Verified: Found {node_count} nodes in the live graph.")