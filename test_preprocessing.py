import pytest
from pipeline.preprocessing import clean_manufacturer_name
from pipeline.preprocessing import resolve_manufacturer_entity, MASTER_MANUFACTURERS

def test_strips_corporate_suffixes():
    """Verify that legal and corporate entity suffixes are completely removed."""
    assert clean_manufacturer_name("Medtronic Inc.") == "MEDTRONIC"
    assert clean_manufacturer_name("BOSTON SCIENTIFIC LLC") == "BOSTON SCIENTIFIC"
    assert clean_manufacturer_name("Stryker Corporation") == "STRYKER"
    assert clean_manufacturer_name("Baxter International") == "BAXTER"

def test_removes_stray_punctuation():
    """Verify that commas, hyphens, and periods are stripped safely."""
    assert clean_manufacturer_name("Medtronic, LLC") == "MEDTRONIC"
    assert clean_manufacturer_name("Zimmer-Biomet, Inc.") == "ZIMMERBIOMET"
    # Though the line above isn't completely standardized, 
    # it gives us a good case to use the next filter, string distance.
    assert clean_manufacturer_name("Stryker Holdings, Inc.") == "STRYKER"

def test_normalizes_case_and_whitespace():
    """Verify that messy capitalization and double-spaces are normalized to uppercase."""
    assert clean_manufacturer_name("   medtronic   inc   ") == "MEDTRONIC"
    assert clean_manufacturer_name("baxter HEALTHCARE corp.") == "BAXTER"

def test_preserves_valid_substrings():
    """Verify that the regex boundary \b prevents stripping valid name parts (e.g., 'co' in Covidien)."""
    assert clean_manufacturer_name("Covidien LLC") == "COVIDIEN"

def test_exhaustive_master_list_resolution():
    """
    Exhaustively verify that every master manufacturer correctly resolves 
    to itself, and handles known messy variations successfully.
    """
    # 1. Verify exact matches resolve perfectly without degradation
    for master_name in MASTER_MANUFACTURERS:
        assert resolve_manufacturer_entity(master_name) == master_name
        
    # 2. Verify deterministic routing for known variations
    variations = {
        "MEDTRONIC": ["Medtronic Inc.", "Medtronic, LLC", "MEDTRONIC CORPORATION"],
        "STRYKER": ["Stryker Corp.", "Stryker Corporation", "Stryker Holdings, Inc."],
        "BOSTON SCIENTIFIC": ["Boston Scientific Corp", "Boston Scientific, Inc.", "BOSTON SCIENTIFIC LLC"],
        "BAXTER": ["Baxter International", "Baxter International, Inc.", "Baxter Healthcare Corp."],
        "ZIMMER BIOMET": ["Zimmer Biomet Holdings", "Zimmer Biomet, LLC", "Zimmer Biomet Inc."]
    }
    
    for target_master, messy_list in variations.items():
        for messy_name in messy_list:
            resolved_name = resolve_manufacturer_entity(messy_name)
            assert resolved_name == target_master, f"Failed resolving '{messy_name}'. Expected '{target_master}', got '{resolved_name}'"