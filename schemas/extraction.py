from typing import List, Optional
from pydantic import BaseModel, Field

# --- NODE SCHEMAS ---

class ManufacturerExtraction(BaseModel):
    """Extracted details for a medical device manufacturer."""
    id: str = Field(..., description="Normalized unique uppercase ID, e.g., 'MFR-3M' or 'MFR-MEDTRONIC'.")
    name: str = Field(..., description="Official, full clean corporate name of the manufacturer.")

class UNSPSCCategoryExtraction(BaseModel):
    """Extracted United Nations Standard Products and Services Code."""
    code: str = Field(..., description="The standard 8-digit commodity code string, e.g., '42142611'.")
    name: str = Field(..., description="The official category descriptive name.")

class SKUExtraction(BaseModel):
    """Extracted physical catalog packaging asset (Global Trade Item Number / SKU)."""
    id: str = Field(..., description="The explicit GTIN, SKU, or manufacturer part number.")
    price: float = Field(..., description="The unit or contract price of the item. Default to 0.0 if unknown.")
    lead_time_days: int = Field(default=5, description="Estimated distribution fulfillment lag in days.")

class MedicalDeviceExtraction(BaseModel):
    """Extracted generic clinical product definition."""
    id: str = Field(..., description="A unique slug generated from the device class, e.g., 'DEV-SYRINGE-3ML'.")
    name: str = Field(..., description="Common clinical name used by practitioners.")
    description: Optional[str] = Field(None, description="Detailed text regarding product specs or dimensions.")
    manufacturer_id: str = Field(..., description="The ID of the manufacturer who makes this device.")
    category_code: str = Field(..., description="The UNSPSC code this device maps to.")
    skus: List[SKUExtraction] = Field(default_factory=list, description="List of physical inventory packages tied to this clinical item.")

# --- RELATIONSHIP SCHEMAS (WORKFLOW METADATA) ---

class SubstitutionProposalExtraction(BaseModel):
    """An agent-proposed inventory substitution path based on document analysis."""
    source_sku_id: str = Field(..., description="The SKU that is currently unavailable or backordered.")
    target_sku_id: str = Field(..., description="The functional alternative SKU.")
    confidence_score: float = Field(..., description="Value between 0.0 and 1.0 indicating clinical equivalence certainty.")
    rationale: str = Field(..., description="Plain-text justification for why this item works as a drop-in replacement.")

# --- MASTER CONTAINER SCHEMA ---

class SupplyChainExtractionPayload(BaseModel):
    """The complete transaction payload containing all entities extracted from a document source."""
    manufacturers: List[ManufacturerExtraction] = Field(default_factory=list)
    categories: List[UNSPSCCategoryExtraction] = Field(default_factory=list)
    devices: List[MedicalDeviceExtraction] = Field(default_factory=list)
    substitutions: List[SubstitutionProposalExtraction] = Field(default_factory=list)