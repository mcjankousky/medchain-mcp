import pytest
from unittest.mock import MagicMock, patch

# Import the tools directly from our server script
from server.mcp_server import (
    query_supply_chain_topology,
    get_product_alternatives,
    get_graph_status
)

# --- TOPOLOGY TOOL TESTS ---

@patch('server.mcp_server.repo')
def test_query_supply_chain_topology_success(mock_repo):
    """Test that the topology tool correctly formats a successful database return."""
    # 1. Setup the Mock Database Context Manager
    mock_session = MagicMock()
    mock_repo.driver.session.return_value.__enter__.return_value = mock_session
    
    # 2. Simulate what Neo4j would return for a valid query
    mock_session.run.return_value = [
        {
            "company_name": "Medtronic Inc.",
            "product_name": "Cardiac Pacemaker",
            "sku_id": "SKU-MED-001",
            "price": 4500.00,
            "classification": "Cardiac Implant Devices",
            "class_code": "4212"
        }
    ]
    
    # 3. Execute the Tool
    result = query_supply_chain_topology("Medtronic")
    
    # 4. Assert the tool parsed and formatted the data correctly
    assert "STRATEGIC TOPOLOGY REPORT FOR: Medtronic Inc." in result
    assert "Cardiac Implant Devices" in result
    assert "SKU-MED-001" in result
    assert "$4500.00" in result
    mock_session.run.assert_called_once() # Verify it actually queried the DB


@patch('server.mcp_server.repo')
def test_query_supply_chain_topology_empty(mock_repo):
    """Test that the topology tool handles missing companies gracefully."""
    mock_session = MagicMock()
    mock_repo.driver.session.return_value.__enter__.return_value = mock_session
    
    # Simulate an empty database return
    mock_session.run.return_value = []
    
    result = query_supply_chain_topology("GhostCompany")
    
    assert "No active product dependencies mapped" in result
    assert "GhostCompany" in result


# --- ALTERNATIVES TOOL TESTS ---

@patch('server.mcp_server.repo')
def test_get_product_alternatives_sku_match(mock_repo):
    """Test the primary logic branch: explicit SKU-level substitutes."""
    mock_session = MagicMock()
    mock_repo.driver.session.return_value.__enter__.return_value = mock_session
    
    # Simulate the FIRST query (SKU match) returning data
    def side_effect_run(query, **kwargs):
        if "confidence_score" in query: # This is our SKU-level query
            return [
                {
                    "alternative_sku": "SKU-ALT-999",
                    "device_name": "Replacement Device",
                    "manufacturer": "Alternative Corp",
                    "price": 100.0,
                    "lead_time": 2,
                    "confidence": 0.95,
                    "rationale": "Exact clinical match"
                }
            ]
        return [] # Fallback query returns nothing
        
    mock_session.run.side_effect = side_effect_run
    
    result = get_product_alternatives("SKU-TARGET")
    
    # Verify it hit the high-precision branch and formatted it
    assert "CRITICAL MATCH" in result
    assert "SKU-ALT-999" in result
    assert "[Confidence: 0.95]" in result
    assert "Fallback" not in result


@patch('server.mcp_server.repo')
def test_get_product_alternatives_fallback_match(mock_repo):
    """Test the secondary logic branch: UNSPSC category fallback."""
    mock_session = MagicMock()
    mock_repo.driver.session.return_value.__enter__.return_value = mock_session
    
    # Simulate the FIRST query failing, but the SECOND (fallback) succeeding
    def side_effect_run(query, **kwargs):
        if "confidence_score" in query:
            return [] # No explicit substitutes
        if "BELONGS_TO_CATEGORY" in query:
            return [
                {
                    "alternative_sku": "SKU-PEER-111",
                    "device_name": "Peer Category Device",
                    "manufacturer": "Peer Corp",
                    "price": 85.0,
                    "lead_time": 5
                }
            ]
            
    mock_session.run.side_effect = side_effect_run
    
    result = get_product_alternatives("SKU-TARGET")
    
    # Verify it hit the taxonomic fallback branch
    assert "Notice: No explicit SKU alternative edges defined" in result
    assert "category peer devices" in result
    assert "SKU-PEER-111" in result