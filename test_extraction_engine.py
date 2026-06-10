import pytest
from unittest.mock import MagicMock, patch
from pipeline.extraction_engine import run_genai_extraction
from schemas.extraction import SupplyChainExtractionPayload

@patch("pipeline.extraction_engine.genai.Client")
def test_extraction_engine_correctly_intercepts_and_resolves_ids_with_gemini(mock_client_cls):
    """Ensure the extraction engine successfully forces stochastic model variations back to master IDs."""
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    
    # We now mock the raw JSON text response that Gemini will return
    mock_response = MagicMock()
    mock_response.text = '{"manufacturers": [{"id": "PENDING", "name": "Medtronic, LLC"}], "categories": [], "devices": [], "substitutions": []}'
    mock_client.models.generate_content.return_value = mock_response

    # Act
    processed_payload = run_genai_extraction("Messy raw string text input documentation.")

    # Assert
    mock_client.models.generate_content.assert_called_once()
    assert processed_payload.manufacturers[0].id == "MFR-MEDTRONIC"