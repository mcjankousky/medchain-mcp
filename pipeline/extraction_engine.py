import os
import sys
import json
from google import genai
from google.genai import types
from schemas.extraction import SupplyChainExtractionPayload
from pipeline.preprocessing import resolve_manufacturer_entity

def run_genai_extraction(file_content: str) -> SupplyChainExtractionPayload:
    if "GEMINI_API_KEY" not in os.environ:
        print("CRITICAL CONFIGURATION ERROR: GEMINI_API_KEY environment variable is missing.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
    # 1. Dump our Pydantic structure to a string so Gemini knows exactly what to return
    schema_instructions = json.dumps(SupplyChainExtractionPayload.model_json_schema(), indent=2)

    # 2. Inject the schema directly into the system prompt
    system_instruction = (
        "You are an expert healthcare supply chain ontology analyst. "
        "Analyze the provided document text and extract all entities exactly "
        "matching the requested schema format. Generate distinct slug IDs "
        "for generic medical devices based closely on their functional definitions.\n\n"
        f"You MUST return valid JSON that perfectly matches this JSON Schema:\n{schema_instructions}"
    )

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"<document>\n{file_content}\n</document>",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            # Force JSON output, but bypass the SDK's buggy response_schema parser
            response_mime_type="application/json", 
            temperature=0.1, 
        ),
    )

    # 3. Manually parse and validate the raw JSON text string into our Pydantic model
    parsed_payload = SupplyChainExtractionPayload.model_validate_json(response.text)

    # --- CRITICAL HYBRID NORMALIZATION PASSTHROUGH ---
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