from typing import List, Optional
from pydantic import BaseModel, Field

# --- NODE SCHEMAS ---

class ManufacturerExtraction(BaseModel):
    id: str = Field(..., description="Normalized unique uppercase ID, e.g., 'MFR-3M'.")
    name: str = Field(..., description="Official corporate name.")

class UNSPSCCategoryExtraction(BaseModel):
    code: str = Field(..., description="The standard 8-digit commodity code string.")
    name: str = Field(..., description="The official category descriptive name.")

class SKUExtraction(BaseModel):
    id: str = Field(..., description="The explicit GTIN, SKU, or part number.")
    # FIX 1: Make price Optional and default to 0.0 if the LLM can't find it
    price: Optional[float] = Field(default=0.0, description="Unit price. Default 0.0 if unknown.")
    lead_time_days: int = Field(default=5, description="Estimated fulfillment lag in days.")

class MedicalDeviceExtraction(BaseModel):
    id: str = Field(..., description="A unique slug generated from the device class.")
    name: str = Field(..., description="Common clinical name.")
    # FIX 2: Ensure description is Optional with a None default
    description: Optional[str] = Field(default=None, description="Detailed text specs.")
    manufacturer_id: str = Field(..., description="The ID of the manufacturer.")
    category_code: str = Field(..., description="The UNSPSC code this device maps to.")
    skus: List[SKUExtraction] = Field(default_factory=list)

# --- RELATIONSHIP SCHEMAS ---

class SubstitutionProposalExtraction(BaseModel):
    source_sku_id: str
    target_sku_id: str
    confidence_score: float
    rationale: str

# --- MASTER CONTAINER SCHEMA ---

class SupplyChainExtractionPayload(BaseModel):
    manufacturers: List[ManufacturerExtraction] = Field(default_factory=list)
    categories: List[UNSPSCCategoryExtraction] = Field(default_factory=list)
    devices: List[MedicalDeviceExtraction] = Field(default_factory=list)
    substitutions: List[SubstitutionProposalExtraction] = Field(default_factory=list)