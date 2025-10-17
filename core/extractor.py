from langdetect import detect

def detect_language(text: str) -> str:
    """Detect language from extracted text"""
    try:
        lang = detect(text)
        return lang
    except Exception as e:
        return f"Error detecting language: {str(e)}"
