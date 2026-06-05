import pytest
from pydantic import ValidationError
from schemas.extraction import SupplyChainExtractionPayload, SKUExtraction

def test_valid_payload_parsing():
    """Verify that a well-formed dictionary matches our schema schema perfectly."""
    valid_data = {
        "manufacturers": [{"id": "MFR-MEDTRONIC", "name": "Medtronic Inc."}],
        "categories": [{"code": "42142611", "name": "Syringes"}],
        "devices": [{
            "id": "DEV-SYRINGE-3ML",
            "name": "3ml Safety Syringe",
            "manufacturer_id": "MFR-MEDTRONIC",
            "category_code": "42142611",
            "skus": [{"id": "GTIN-100234", "price": 14.50, "lead_time_days": 3}]
        }],
        "substitutions": []
    }
    
    payload = SupplyChainExtractionPayload(**valid_data)
    assert len(payload.manufacturers) == 1
    assert payload.devices[0].skus[0].price == 14.50


def test_payload_validation_catches_type_mismatches():
    """Verify that Pydantic strictly blocks bad data types, like a string for price."""
    invalid_data = {
        "manufacturers": [],
        "categories": [],
        "devices": [{
            "id": "DEV-SYRINGE-3ML",
            "name": "3ml Safety Syringe",
            "manufacturer_id": "MFR-MEDTRONIC",
            "category_code": "42142611",
            "skus": [{"id": "GTIN-100234", "price": "not-a-price", "lead_time_days": 3}]
        }],
        "substitutions": []
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SupplyChainExtractionPayload(**invalid_data)
        
    assert "price" in str(exc_info.value)


def test_sku_default_lead_time():
    """Verify that if a document doesn't explicitly name a lead time, our safe default injects."""
    sku = SKUExtraction(id="SKU-TEST", price=10.0)
    assert sku.lead_time_days == 5 # Our specified fallback default value