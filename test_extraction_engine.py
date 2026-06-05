import pytest
from unittest.mock import MagicMock, patch
from pipeline.extraction_engine import run_genai_extraction
from schemas.extraction import SupplyChainExtractionPayload

@patch("pipeline.extraction_engine.genai.Client")
def test_extraction_engine_correctly_intercepts_and_resolves_ids_with_gemini(mock_client_cls):
    """
    Ensure the extraction engine triggers the Gemini content engine and successfully
    forces stochastic model variations back to our master manufacturer IDs.
    """
    # 1. Arrange: Mock the Google SDK model response tree
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    
    mock_payload = SupplyChainExtractionPayload(
        manufacturers=[{"id": "PENDING", "name": "Medtronic, LLC"}],
        categories=[],
        devices=[],
        substitutions=[]
    )
    
    mock_response = MagicMock()
    mock_response.parsed = mock_payload
    mock_client.models.generate_content.return_value = mock_response

    # 2. Act: Trigger our local engine function
    processed_payload = run_genai_extraction("Messy raw string text input documentation.")

    # 3. Assert: Verify the underlying google generate_content endpoint parameters were engaged
    mock_client.models.generate_content.assert_called_once()
    
    # Confirm that our preprocessing passthrough successfully forced the ID to update
    assert processed_payload.manufacturers[0].id == "MFR-MEDTRONIC"