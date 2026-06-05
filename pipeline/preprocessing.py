import re
from typing import Optional
from rapidfuzz import process, fuzz

# The Graph's "Single Source of Truth" 
# These map exactly to the 'id' properties governed by Neo4j's unique constraints
MASTER_MANUFACTURERS = [
    "MEDTRONIC",
    "STRYKER",
    "BOSTON SCIENTIFIC",
    "BAXTER",
    "ZIMMER BIOMET",
    "COVIDIEN"
]

def clean_manufacturer_name(raw_name: str) -> str:
    """Strips corporate noise and punctuation from a manufacturer string."""
    name = raw_name.lower()
    noise_words = r'\b(inc|llc|corp|corporation|holdings|co|ltd|international|healthcare)\b\.?'
    name = re.sub(noise_words, '', name)
    name = re.sub(r'[.,-]', '', name)
    name = " ".join(name.split())
    return name.strip().upper()

def resolve_manufacturer_entity(raw_name: str, threshold: float = 85.0) -> Optional[str]:
    """
    The Hybrid Pipeline:
    1. Runs the fast Regex cleaner.
    2. Uses Levenshtein distance to find the closest master entity.
    3. Returns the deterministic ID if the confidence score meets the threshold.
    """
    # Step 1: Fast Regex Pass
    cleaned_name = clean_manufacturer_name(raw_name)
    
    # Step 2: String-Distance Calculation
    # fuzz.WRatio handles case, ordering, and partial string matches brilliantly
    match = process.extractOne(
        cleaned_name, 
        MASTER_MANUFACTURERS, 
        scorer=fuzz.WRatio
    )
    
    if not match:
        return None
        
    best_string, score, _index = match
    
    # Step 3: Confidence Thresholding
    if score >= threshold:
        return best_string
    else:
        # In a real pipeline, returning None flags the entity for human review
        # or triggers a fallback LLM agentic search.
        return None