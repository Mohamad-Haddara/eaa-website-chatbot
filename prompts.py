"""
Everything the chat model reads, plus the fixed replies that skip the model.

Fixed replies (greetings, "not found", errors) are written in here in English and Arabic,
so they cost nothing and can never be made up by the model.

"""


import re
from models import Lang



_ARABIC_LETTER = re.compile(r"[ء-يٱ-ۓ]")
_LATIN_LETTER = re.compile(r"[A-Za-z]")
_ARABIC_MARKS = re.compile(r"[ً-ْٰـ]")  # short vowels, dagger alef, tatweel


# --------------------------------
# Language
# --------------------------------

def detect_language(text: str, fallback: Lang = "en") -> Lang:
    """
    Return "ar" or "en": the scripts that most letters od 'text' are written in.

    Text with no letters ar all (for example "2024 ?") returns 'fallback'.
    Example: detect_language("Tell me about EAA?") -> "en"
    
    """
    arabic = len(_ARABIC_LETTER.findall(text))
    latin = len(_LATIN_LETTER.findall(text))
    if arabic == 0 and latin == 0:
        return fallback

    return "ar" if arabic >= latin else "en"





    