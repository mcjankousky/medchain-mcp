import os
import sys
import json
import csv
from schemas.extraction import (
    SupplyChainExtractionPayload, 
    ManufacturerExtraction, 
    UNSPSCCategoryExtraction, 
    MedicalDeviceExtraction, 
    SKUExtraction
)
from pipeline.extraction_engine import run_genai_extraction

def run_multimodal_ingestion_pipeline() -> SupplyChainExtractionPayload:
    """
    Sequentially reads mixed-mode unstructured, tabular, and semi-structured mock documents,
    extracts type-safe data configurations using Gemini, and unifies them into a single 
    master payload.
    """
    base_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    
    contract_path = os.path.join(base_dir, "vendor_contract.txt")
    invoice_path = os.path.join(base_dir, "invoice_raw.csv")
    catalog_path = os.path.join(base_dir, "manufacturer_catalog.json")
    
    # Initialize an empty, type-safe unified payload container
    master_payload = SupplyChainExtractionPayload(
        manufacturers=[], categories=[], devices=[], substitutions=[]
    )
    
    print("========================================================================")
    print("STARTING MULTIMODAL HEALTHCARE SUPPLY CHAIN INGESTION PIPELINE")
    print("========================================================================")
    
    # --------------------------------------------------------------------------
    # STEP 1: Process Unstructured Contract Document (Text)
    # --------------------------------------------------------------------------
    print("\n[PROCESSING] Ingesting unstructured text contract via Gemini...")
    with open(contract_path, "r", encoding="utf-8") as f:
        contract_content = f.read()
    
    contract_payload = run_genai_extraction(contract_content)
    
    # Append values safely into our single master container
    master_payload.manufacturers.extend(contract_payload.manufacturers)
    master_payload.categories.extend(contract_payload.categories)
    master_payload.devices.extend(contract_payload.devices)
    master_payload.substitutions.extend(contract_payload.substitutions)
    print(f" -> [SUCCESS] Contract parsed: Found {len(contract_payload.devices)} base clinical device definitions.")

    # --------------------------------------------------------------------------
    # STEP 2: Process Tabular Invoice Document (CSV)
    # --------------------------------------------------------------------------
    print("\n[PROCESSING] Ingesting flat tabular invoice records...")
    # Because a flat tabular CSV file is incredibly token-dense and structured, we can 
    # convert the raw string layout directly into an easily digestible formatted text block
    with open(invoice_path, mode="r", encoding="utf-8") as f:
        invoice_content = f.read()
        
    invoice_payload = run_genai_extraction(f"CSV Invoiced Records Table Data:\n{invoice_content}")
    
    master_payload.manufacturers.extend(invoice_payload.manufacturers)
    master_payload.categories.extend(invoice_payload.categories)
    master_payload.devices.extend(invoice_payload.devices)
    master_payload.substitutions.extend(invoice_payload.substitutions)
    print(f" -> [SUCCESS] Tabular Invoice parsed: Extracted {len(invoice_payload.devices)} associated devices.")

    # --------------------------------------------------------------------------
    # STEP 3: Process Semi-Structured Catalog (JSON)
    # --------------------------------------------------------------------------
    print("\n[PROCESSING] Ingesting nested semi-structured catalog JSON...")
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog_raw_string = f.read()
        
    catalog_payload = run_genai_extraction(catalog_raw_string)
    
    master_payload.manufacturers.extend(catalog_payload.manufacturers)
    master_payload.categories.extend(catalog_payload.categories)
    master_payload.devices.extend(catalog_payload.devices)
    master_payload.substitutions.extend(catalog_payload.substitutions)
    print(f" -> [SUCCESS] Manufacturer Catalog parsed.")

    # --------------------------------------------------------------------------
    # STEP 4: Deduplicate Consolidated Extracted Inbound Nodes
    # --------------------------------------------------------------------------
    print("\n[PROCESSING] Deduplicating overlapping inbound graph elements...")
    
    # Deduplicate Manufacturers by unique ID
    seen_mfrs = {}
    for m in master_payload.manufacturers:
        seen_mfrs[m.id] = m
    master_payload.manufacturers = list(seen_mfrs.values())
    
    # Deduplicate Categories by unique hierarchical Code
    seen_cats = {}
    for c in master_payload.categories:
        seen_cats[c.code] = c
    master_payload.categories = list(seen_cats.values())
    
    # Deduplicate Clinical Devices by unique slug string ID
    seen_devs = {}
    for d in master_payload.devices:
        seen_devs[d.id] = d
    master_payload.devices = list(seen_devs.values())

    print("========================================================================")
    print("PIPELINE CONSOLIDATION COMPLETE SUMMARY:")
    print(f" - Normalized Unique Manufacturers: {len(master_payload.manufacturers)}")
    print(f" - Normalized Standard Categories : {len(master_payload.categories)}")
    print(f" - Normalized Unique Devices     : {len(master_payload.devices)}")
    print("========================================================================")
    
    # Save checkpoint payload locally so Phase 5 doesn't need to re-query live APIs
    checkpoint_output_path = os.path.join(base_dir, "unified_pipeline_checkpoint.json")
    with open(checkpoint_output_path, "w", encoding="utf-8") as out:
        out.write(master_payload.model_dump_json(indent=2))
        
    print(f"Saved secure data processing state checkpoint to: {checkpoint_output_path}\n")
    return master_payload

if __name__ == "__main__":
    # Fallback gatekeeper verification block to handle live system token failures safely
    if "GEMINI_API_KEY" in os.environ and not os.environ["GEMINI_API_KEY"].startswith("AIzaSyYour"):
        run_multimodal_ingestion_pipeline()
    else:
        print("\nPipeline Aborted: Cannot fire pipeline runner script.")
        print("Please configure a valid live 'GEMINI_API_KEY' within your untracked local .env file.")