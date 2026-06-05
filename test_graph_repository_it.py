import os
import pytest
from database.graph_repository import GraphRepository
from schemas.extraction import (
    SupplyChainExtractionPayload,
    ManufacturerExtraction,
    MedicalDeviceExtraction,
    SKUExtraction,
    UNSPSCCategoryExtraction
)

@pytest.fixture(scope="function")
def test_repo():
    """Setup a safe sandbox connection and wipe it before/after execution."""
    test_uri = os.environ.get("NEO4J_TEST_URI", "bolt://localhost:7688")
    repo = GraphRepository(uri=test_uri)
    with repo.driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    yield repo
    repo.close()

def test_hydrate_pipeline_creates_complete_graph_topology(test_repo):
    """
    Verify the GraphRepository accurately executes all MERGE queries and 
    draws the required edges between MedicalDevices, SKUs, and Manufacturers.
    """
    # 1. Arrange: Construct a miniature verified payload
    mock_payload = SupplyChainExtractionPayload(
        manufacturers=[ManufacturerExtraction(id="MFR-MEDTRONIC", name="Medtronic Inc.")],
        categories=[UNSPSCCategoryExtraction(code="42142611", name="Syringes")],
        devices=[
            MedicalDeviceExtraction(
                id="DEV-SYRINGE-3ML",
                name="3ml Safety Syringe",
                manufacturer_id="MFR-MEDTRONIC",
                category_code="42142611",
                skus=[SKUExtraction(id="GTIN-100234", price=14.50, lead_time_days=3)]
            )
        ]
    )

    # 2. Act: Execute the complete repository transaction
    test_repo.hydrate_supply_chain_pipeline(mock_payload)

    # 3. Assert: Query the real database to ensure the path exists
    with test_repo.driver.session() as session:
        # Check node existence
        mfr_count = session.run("MATCH (m:Manufacturer) RETURN count(m) as c").single()["c"]
        sku_count = session.run("MATCH (s:SKU) RETURN count(s) as c").single()["c"]
        assert mfr_count == 1
        assert sku_count == 1

        # Check edge traversal integrity: Can we walk from the SKU to the Manufacturer?
        path_query = """
        MATCH (s:SKU {id: 'GTIN-100234'})<-[:HAS_SKU]-(d:MedicalDevice)-[:MANUFACTURED_BY]->(m:Manufacturer)
        RETURN m.name as mfr_name, d.name as dev_name
        """
        record = session.run(path_query).single()
        
        assert record is not None, "Failed to locate the full Relationship path!"
        assert record["mfr_name"] == "Medtronic Inc."
        assert record["dev_name"] == "3ml Safety Syringe"