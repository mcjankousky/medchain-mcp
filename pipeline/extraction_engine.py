import os
import sys
from google import genai
from google.genai import types
from schemas.extraction import SupplyChainExtractionPayload
from pipeline.preprocessing import resolve_manufacturer_entity

def run_genai_extraction(file_content: str) -> SupplyChainExtractionPayload:
    """
    Leverages Gemini's native structured outputs engine to parse unvalidated text,
    then intercepts and normalizes entity names via our deterministic hybrid layer.
    """
    # Enforce that the newly specified Gemini key exists in the environment boundaries
    if "GEMINI_API_KEY" not in os.environ:
        print("CRITICAL CONFIGURATION ERROR: GEMINI_API_KEY environment variable is missing.", file=sys.stderr)
        sys.exit(1)

    # Initialize the modern Google GenAI Client
    client = genai.Client()
    
    system_instruction = (
        "You are an expert healthcare supply chain ontology analyst. "
        "Analyze the provided document text and extract all entities exactly "
        "matching the requested schema format. Generate distinct slug IDs "
        "for generic medical devices based closely on their functional definitions."
    )

    # Execute the structured content generation call using gemini-1.5-flash
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=f"<document>\n{file_content}\n</document>",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            # Force the model to respond matching our exact Pydantic structural schema
            response_mime_type="application/json",
            response_schema=SupplyChainExtractionPayload,
            temperature=0.1, # Keep creativity low for structural parsing
        ),
    )

    # The SDK automatically binds and returns the response parsed into our Pydantic class
    parsed_payload: SupplyChainExtractionPayload = response.parsed

    # --- CRITICAL HYBRID NORMALIZATION PASSTHROUGH ---
    # Intercept stochastic strings and map them deterministically before database hydration
    for mfr in parsed_payload.manufacturers:
        resolved_id = resolve_manufacturer_entity(mfr.name)
        if resolved_id:
            mfr.id = f"MFR-{resolved_id}"
            
    for dev in parsed_payload.devices:
        resolved_mfr_id = resolve_manufacturer_entity(dev.manufacturer_id)
        if resolved_mfr_id:
            dev.manufacturer_id = f"MFR-{resolved_mfr_id}"
            
    return parsed_payload

if __name__ == "__main__":
    # Test block to verify execution mechanics locally
    mock_text = "Agreement with Medtronic Inc for device DEV-SYRINGE-3ML"
    if not os.environ.get("GEMINI_API_KEY", "").startswith("AIzaSyYour"):
        result = run_genai_extraction(mock_text)
        print("Successfully extracted and resolved payload using Gemini free tier:")
        print(result.model_dump_json(indent=2))
    else:
        print("Skipping execution line: Live Gemini API Key placeholder detected.")