import re

def extract_references(text: str) -> list:
    """Extract references or citations from text"""
    pattern = r"\[(?:[^\]]+)\]|\b(NICE|NHS|PubMed|DOI|Guideline|BNF)\b.*"
    matches = re.findall(pattern, text)
    return matches
