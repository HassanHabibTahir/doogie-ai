# core/language_utils.py
from langdetect import detect, DetectorFactory, detect_langs
from langdetect.lang_detect_exception import LangDetectException

# Fix randomness in langdetect
DetectorFactory.seed = 0

def detect_language(text: str) -> dict:
    """
    Detect the language of a given text.
    Returns:
        {
            'language': 'en',
            'confidence': 0.99
        }
    """
    try:
        lang = detect(text)
        # Optional: detect multiple probabilities
        langs = detect_langs(text)
        top_lang = langs[0] if langs else None
        confidence = top_lang.prob if top_lang else None
        return {
            "language": lang,
            "confidence": confidence
        }
    except LangDetectException:
        return {
            "language": "unknown",
            "confidence": 0
        }
