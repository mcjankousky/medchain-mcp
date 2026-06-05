import os
import json
import csv

def verify_and_load_ingestion_files():
    """
    Confirms all multimodal mock supply chain documents exist 
    and are accessible to the Python runtime container.
    """
    base_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    
    contract_path = os.path.join(base_dir, "vendor_contract.txt")
    invoice_path = os.path.join(base_dir, "invoice_raw.csv")
    catalog_path = os.path.join(base_dir, "manufacturer_catalog.json")
    
    print("Verifying ingestion layer file assets...")
    
    # 1. Test Text/PDF Excerpt Ingestion
    with open(contract_path, "r") as f:
        contract_text = f.read()
    print(f" -> [SUCCESS] Loaded Contract Text ({len(contract_text)} chars)")
    
    # 2. Test Tabular CSV Ingestion
    with open(invoice_path, mode="r", encoding="utf-8") as f:
        csv_reader = csv.DictReader(f)
        csv_rows = list(csv_reader)
    print(f" -> [SUCCESS] Loaded Tabular Invoice CSV ({len(csv_rows)} records)")
    
    # 3. Test JSON Catalog Ingestion
    with open(catalog_path, "r") as f:
        catalog_data = json.load(f)
    print(f" -> [SUCCESS] Loaded JSON Catalog System for: '{catalog_data['catalog_metadata']['publisher']}'")

if __name__ == "__main__":
    verify_and_load_ingestion_files()