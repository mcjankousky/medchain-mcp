import pytest
import sys
from unittest.mock import MagicMock, patch
from setup_schema import initialize_database, CONSTRAINTS

@patch("setup_schema.GraphDatabase.driver")
def test_initialize_database_applies_all_constraints(mock_driver_cls):
    """
    Test that the script connects to the database, executes every 
    defined ontology constraint exactly once, and reads them back.
    """
    # 1. Arrange: Setup the nested mock structure for Neo4j driver lifecycle
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver_cls.return_value = mock_driver
    mock_driver.session.return_value.__enter__.return_value = mock_session
    
    # Simulate the database returning rows when 'SHOW CONSTRAINTS' runs
    mock_session.run.return_value = [
        {"type": "UNIQUENESS", "name": "manufacturer_id", "properties": ["id"]},
        {"type": "UNIQUENESS", "name": "device_id", "properties": ["id"]}
    ]

    # 2. Act: Execute the schema initialization code
    initialize_database()

    # 3. Assert: Verify the driver was constructed and closed properly
    mock_driver_cls.assert_called_once()
    mock_driver.close.assert_called_once()

    # Verify that every single constraint query in our list was executed
    executed_queries = [call[0][0] for call in mock_session.run.call_args_list]
    for constraint in CONSTRAINTS:
        assert constraint in executed_queries
    
    # Verify that the verification check was also executed
    assert "SHOW CONSTRAINTS" in executed_queries


@patch("setup_schema.GraphDatabase.driver")
def test_initialize_database_handles_connection_failure(mock_driver_cls):
    """
    Test that if Neo4j is unreachable, the initialization script handles 
    the exception cleanly and exits with a non-zero system failure status.
    """
    # 1. Arrange: Force the driver connection to raise a network exception
    mock_driver_cls.side_effect = Exception("Connection refused by database host")

    # 2. Act & Assert: Verify that the script terminates using sys.exit(1)
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        initialize_database()
    
    # Assert that it forced a container failure exit code
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1