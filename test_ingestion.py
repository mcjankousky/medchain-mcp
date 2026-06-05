import os
import pytest

def test_ingestion_layer_files_exist_and_are_non_empty():
    """Assert that all mock logistics data stores exist and contain data boundaries."""
    base_dir = os.path.join(os.path.dirname(__file__), "data")
    
    files_to_check = [
        "vendor_contract.txt",
        "invoice_raw.csv",
        "manufacturer_catalog.json"
    ]
    
    for filename in files_to_check:
        full_path = os.path.join(base_dir, filename)
        
        # Assert files physically exist in the workspace volume
        assert os.path.exists(full_path) == True, f"Missing mock data file: {filename}"
        
        # Assert file has content to prevent zero-token empty reads by the LLM
        assert os.path.getsize(full_path) > 0, f"Data file {filename} is empty"