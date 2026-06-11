import os
import sys
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP
from database.graph_repository import GraphRepository

# 1. Initialize the FastMCP server instance
mcp = FastMCP("MedChain Healthcare Supply Chain Server")

# 2. Establish global connection pool to the Neo4j container
try:
    repo = GraphRepository()
except Exception as e:
    print(f"CRITICAL ERROR: FastMCP failed to initialize Neo4j connection: {e}", file=sys.stderr)
    sys.exit(1)


# --- MCP TOOL 1: CLINICAL PRODUCT ALTERNATIVES ---

@mcp.tool()
def get_product_alternatives(sku_id: str) -> str:
    """
    Finds alternative replacement products or SKUs when a target item faces a backorder or shortage.
    Prioritizes explicit packaging-level SKU substitutes before falling back to generic matching 
    via shared UNSPSC category classifications.
    
    Args:
        sku_id: The unique identifier code for the physical SKU asset (e.g., a GTIN or part number).
    """
    sku_id = sku_id.strip()
    
    # Query A: Check for explicit Packaging-Tier Substitutes first (High Precision)
    sku_sub_query = """
    MATCH (target:SKU {id: $sku_id})
    MATCH (alt:SKU)-[r:POTENTIAL_SUBSTITUTE_FOR]->(target)
    MATCH (dev:MedicalDevice)-[:HAS_SKU]->(alt)
    MATCH (dev)-[:MANUFACTURED_BY]->(mfr:Manufacturer)
    RETURN alt.id as alternative_sku, 
           dev.name as device_name, 
           mfr.name as manufacturer, 
           alt.price as price, 
           alt.lead_time_days as lead_time,
           r.confidence_score as confidence,
           r.rationale as rationale
    ORDER BY r.confidence_score DESC
    """
    
    # Query B: Fallback to Category-Level Peer Matching if no explicit SKU matches exist
    category_fallback_query = """
    MATCH (target:SKU {id: $sku_id})<-[:HAS_SKU]-(target_dev:MedicalDevice)-[:BELONGS_TO_CATEGORY]->(cat:UNSPSC_Category)
    MATCH (alt_dev:MedicalDevice)-[:BELONGS_TO_CATEGORY]->(cat)
    MATCH (alt_dev)-[:HAS_SKU]->(alt_sku:SKU)
    MATCH (alt_dev)-[:MANUFACTURED_BY]->(mfr:Manufacturer)
    WHERE alt_sku.id <> $sku_id
    RETURN alt_sku.id as alternative_sku, 
           alt_dev.name as device_name, 
           mfr.name as manufacturer, 
           alt_sku.price as price, 
           alt_sku.lead_time_days as lead_time
    ORDER BY alt_sku.price ASC
    LIMIT 5
    """
    
    try:
        with repo.driver.session() as session:
            # Try high-precision structural SKU match first
            result = session.run(sku_sub_query, sku_id=sku_id)
            records = list(result)
            
            if records:
                output = f"🔍 CRITICAL MATCH: Found {len(records)} verified packaging-tier substitute SKUs:\n"
                for rec in records:
                    output += (
                        f"- SKU: {rec['alternative_sku']} | Device: {rec['device_name']} "
                        f"({rec['manufacturer']}) | Price: ${rec['price']:.2f} | "
                        f"Lead Time: {rec['lead_time']} days [Confidence: {rec['confidence']:.2f}]\n"
                        f"  Rationale: {rec['rationale']}\n"
                    )
                return output
                
            # If empty, run taxonomic fallback query
            output = "⚠️ Notice: No explicit SKU alternative edges defined. Falling back to UNSPSC Taxonomy peers.\n"
            result = session.run(category_fallback_query, sku_id=sku_id)
            fallback_records = list(result)
            
            if not fallback_records:
                return f"❌ Error: Product SKU '{sku_id}' not found in the supply chain ontology mapping registry."
                
            output += f"Found {len(fallback_records)} category peer devices sharing the same clinical functional classification:\n"
            for rec in fallback_records:
                output += (
                    f"- SKU: {rec['alternative_sku']} | Device: {rec['device_name']} "
                    f"({rec['manufacturer']}) | Price: ${rec['price']:.2f} | "
                    f"Lead Time: {rec['lead_time']} days\n"
                )
            return output

    except Exception as e:
        return f"Database query compilation error: {str(e)}"


# --- MCP TOOL 2: SUPPLY CHAIN TOPOLOGY MAPPING ---

@mcp.tool()
def query_supply_chain_topology(manufacturer_id: str) -> str:
    """
    Maps out localized supply chain network nodes for a vendor entity to identify systemic dependency risks.
    Returns all medical equipment classifications, items, and SKUs reliant on this specific company.
    
    Args:
        manufacturer_id: The clean, unique normalized ID of the target company (e.g., 'MFR-MEDTRONIC').
    """
    # Force uppercase formatting to maintain alignment with our Phase 2 resolution engine normalization rules
    mfr_id = manufacturer_id.strip().upper()
    if not mfr_id.startswith("MFR-"):
        mfr_id = f"MFR-{mfr_id}"
        
    query = """
    MATCH (mfr:Manufacturer {id: $mfr_id})<-[:MANUFACTURED_BY]-(dev:MedicalDevice)
    MATCH (dev)-[:HAS_SKU]->(sku:SKU)
    MATCH (dev)-[:BELONGS_TO_CATEGORY]->(cat:UNSPSC_Category)
    RETURN mfr.name as company_name,
           dev.name as product_name,
           sku.id as sku_id,
           sku.price as price,
           cat.name as classification,
           cat.code as class_code
    ORDER BY cat.code, dev.name
    """
    
    try:
        with repo.driver.session() as session:
            result = session.run(query, mfr_id=mfr_id)
            records = list(result)
            
            if not records:
                return f"ℹ️ Supplier Analysis: No active product dependencies mapped to manufacturer ID '{mfr_id}'."
                
            company_name = records[0]["company_name"]
            output = f"🏭 STRATEGIC TOPOLOGY REPORT FOR: {company_name} ({mfr_id})\n"
            output += f"Total vulnerable product tracks monitored: {len(records)}\n"
            output += "------------------------------------------------------------------------\n"
            
            current_class = ""
            for rec in records:
                if rec["classification"] != current_class:
                    current_class = rec["classification"]
                    output += f"\n📂 Category Hierarchy: {current_class} [UNSPSC: {rec['class_code']}]\n"
                output += f"   └── Device Entity: {rec['product_name']} ➔ SKU: {rec['sku_id']} (${rec['price']:.2f})\n"
                
            return output

    except Exception as e:
        return f"Database query compilation error: {str(e)}"


if __name__ == "__main__":
    print("Initializing MedChain MCP Server via stdio...", file=sys.stderr)
    try:
        mcp.run()
    finally:
        repo.close()