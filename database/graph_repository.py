import os
from neo4j import GraphDatabase
from schemas.extraction import (
    SupplyChainExtractionPayload,
    ManufacturerExtraction,
    MedicalDeviceExtraction,
    SKUExtraction,
    UNSPSCCategoryExtraction
)

class GraphRepository:
    """
    Handles all write operations to the Neo4j instance, enforcing clean
    data separation, parameterized inputs, and idempotent merges.
    """
    def __init__(self, uri: str = None):
        self.uri = uri or os.environ["NEO4J_URI"]
        self.user = os.environ["NEO4J_USER"]
        self.password = os.environ["NEO4J_PASSWORD"]
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        self.driver.close()

    def hydrate_supply_chain_pipeline(self, payload: SupplyChainExtractionPayload):
        """
        Orchestrates the transactional insertion of the entire unified Pydantic payload.
        """
        with self.driver.session() as session:
            print("Starting Graph Hydration...")
            
            # 1. Hydrate Manufacturers
            for mfr in payload.manufacturers:
                self._upsert_manufacturer(session, mfr)
            print(f" -> Merged {len(payload.manufacturers)} Manufacturers.")
                
            # 2. Hydrate Categories
            for cat in payload.categories:
                self._upsert_category(session, cat)
            print(f" -> Merged {len(payload.categories)} UNSPSC Categories.")
                
            # 3. Hydrate Medical Devices and link to parents
            skus_processed = 0
            for device in payload.devices:
                self._upsert_medical_device(session, device)
                
                # 4. Hydrate specific SKUs as distinct nodes and link to the Device
                for sku in device.skus:
                    self._upsert_sku_and_link_to_device(session, sku, device.id)
                    skus_processed += 1
                    
            print(f" -> Merged {len(payload.devices)} Devices and {skus_processed} distinct SKUs.")

    # --- INTERNAL WRITE TRANSACTIONS ---

    def _upsert_manufacturer(self, session, mfr: ManufacturerExtraction):
        query = """
        MERGE (m:Manufacturer {id: $mfr_id})
        ON CREATE SET m.name = $mfr_name
        ON MATCH SET m.name = $mfr_name
        """
        session.run(query, mfr_id=mfr.id, mfr_name=mfr.name)

    def _upsert_category(self, session, cat: UNSPSCCategoryExtraction):
        query = """
        MERGE (c:UNSPSC_Category {code: $code})
        ON CREATE SET c.name = $name
        ON MATCH SET c.name = $name
        """
        session.run(query, code=cat.code, name=cat.name)

    def _upsert_medical_device(self, session, device: MedicalDeviceExtraction):
        """
        MERGEs the generic device, then matches the parent Manufacturer and Category
        to draw the correct [:MANUFACTURED_BY] and [:BELONGS_TO_CATEGORY] edges.
        """
        query = """
        // 1. Create or Update the base Device
        MERGE (d:MedicalDevice {id: $dev_id})
        ON CREATE SET d.name = $name, d.description = $desc
        ON MATCH SET d.name = $name, d.description = $desc
        
        // 2. Link to Manufacturer (Requires Manufacturer node to exist)
        WITH d
        MATCH (m:Manufacturer {id: $mfr_id})
        MERGE (d)-[:MANUFACTURED_BY]->(m)
        
        // 3. Link to Category (Requires Category node to exist)
        WITH d
        MATCH (c:UNSPSC_Category {code: $cat_code})
        MERGE (d)-[:BELONGS_TO_CATEGORY]->(c)
        """
        session.run(
            query, 
            dev_id=device.id, 
            name=device.name, 
            desc=device.description,
            mfr_id=device.manufacturer_id,
            cat_code=device.category_code
        )

    def _upsert_sku_and_link_to_device(self, session, sku: SKUExtraction, parent_device_id: str):
        """
        MERGEs the SKU as a distinct node and draws the [:HAS_SKU] relationship.
        """
        query = """
        MERGE (s:SKU {id: $sku_id})
        ON CREATE SET s.price = $price, s.lead_time_days = $lead_time
        ON MATCH SET s.price = $price, s.lead_time_days = $lead_time
        
        WITH s
        MATCH (d:MedicalDevice {id: $dev_id})
        MERGE (d)-[:HAS_SKU]->(s)
        """
        session.run(
            query,
            sku_id=sku.id,
            price=sku.price,
            lead_time=sku.lead_time_days,
            dev_id=parent_device_id
        )