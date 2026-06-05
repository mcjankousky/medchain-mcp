import pytest
from unittest.mock import MagicMock, patch
from pipeline.ingestion_runner import run_multimodal_ingestion_pipeline
from schemas.extraction import SupplyChainExtractionPayload

@patch("pipeline.ingestion_runner.run_genai_extraction")
def test_pipeline_runner_sequential_deduplication_integrity(mock_extraction_fn):
    """
    Verify that the multi-modal pipeline successfully converts independent document types
    and enforces strict ID deduplication across multi-source data overlaps.
    """
    # 1. Arrange: Setup duplicate mock returns mimicking various invoice/contract overlaps
    payload_a = SupplyChainExtractionPayload(
        manufacturers=[{"id": "MFR-MEDTRONIC", "name": "Medtronic Inc."}],
        categories=[], devices=[], substitutions=[]
    )
    payload_b = SupplyChainExtractionPayload(
        manufacturers=[{"id": "MFR-MEDTRONIC", "name": "Medtronic, LLC"}], # Duplicate overlapping node
        categories=[], devices=[], substitutions=[]
    )
    payload_c = SupplyChainExtractionPayload(
        manufacturers=[], categories=[], devices=[], substitutions=[]
    )
    
    # Assign the sequential loop return sequence values for each open file call block
    mock_extraction_fn.side_effect = [payload_a, payload_b, payload_c]

    # 2. Act: Trigger our pipeline framework orchestration execution script
    consolidated_data = run_multimodal_ingestion_pipeline()

    # 3. Assert: Confirm that exactly three open file extraction operations occurred
    assert mock_extraction_fn.call_count == 3
    
    # Confirm that our strict set matching successfully deduplicated the duplicate entries down to 1
    assert len(consolidated_data.manufacturers) == 1
    assert consolidated_data.manufacturers[0].id == "MFR-MEDTRONIC"