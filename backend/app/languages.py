"""Language metadata shared by validation, prompts and the HTTP API."""
from __future__ import annotations

# ISO 639-1/BCP-47 codes are deliberately explicit. The DeepSeek prompt receives
# the human-readable target language rather than relying on model code guesses.
LANGUAGES: tuple[dict[str, str], ...] = (
    {"code": "af", "name": "Afrikaans", "native": "Afrikaans"},
    {"code": "sq", "name": "Albanian", "native": "Shqip"},
    {"code": "am", "name": "Amharic", "native": "አማርኛ"},
    {"code": "ar", "name": "Arabic", "native": "العربية"},
    {"code": "hy", "name": "Armenian", "native": "Հայերեն"},
    {"code": "az", "name": "Azerbaijani", "native": "Azərbaycanca"},
    {"code": "eu", "name": "Basque", "native": "Euskara"},
    {"code": "be", "name": "Belarusian", "native": "Беларуская"},
    {"code": "bn", "name": "Bengali", "native": "বাংলা"},
    {"code": "bs", "name": "Bosnian", "native": "Bosanski"},
    {"code": "bg", "name": "Bulgarian", "native": "Български"},
    {"code": "ca", "name": "Catalan", "native": "Català"},
    {"code": "zh", "name": "Chinese", "native": "中文"},
    {"code": "hr", "name": "Croatian", "native": "Hrvatski"},
    {"code": "cs", "name": "Czech", "native": "Čeština"},
    {"code": "da", "name": "Danish", "native": "Dansk"},
    {"code": "nl", "name": "Dutch", "native": "Nederlands"},
    {"code": "en", "name": "English", "native": "English"},
    {"code": "et", "name": "Estonian", "native": "Eesti"},
    {"code": "fi", "name": "Finnish", "native": "Suomi"},
    {"code": "fr", "name": "French", "native": "Français"},
    {"code": "gl", "name": "Galician", "native": "Galego"},
    {"code": "ka", "name": "Georgian", "native": "ქართული"},
    {"code": "de", "name": "German", "native": "Deutsch"},
    {"code": "el", "name": "Greek", "native": "Ελληνικά"},
    {"code": "gu", "name": "Gujarati", "native": "ગુજરાતી"},
    {"code": "he", "name": "Hebrew", "native": "עברית"},
    {"code": "hi", "name": "Hindi", "native": "हिन्दी"},
    {"code": "hu", "name": "Hungarian", "native": "Magyar"},
    {"code": "is", "name": "Icelandic", "native": "Íslenska"},
    {"code": "id", "name": "Indonesian", "native": "Bahasa Indonesia"},
    {"code": "ga", "name": "Irish", "native": "Gaeilge"},
    {"code": "it", "name": "Italian", "native": "Italiano"},
    {"code": "ja", "name": "Japanese", "native": "日本語"},
    {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ"},
    {"code": "kk", "name": "Kazakh", "native": "Қазақша"},
    {"code": "ko", "name": "Korean", "native": "한국어"},
    {"code": "ky", "name": "Kyrgyz", "native": "Кыргызча"},
    {"code": "lo", "name": "Lao", "native": "ລາວ"},
    {"code": "lv", "name": "Latvian", "native": "Latviešu"},
    {"code": "lt", "name": "Lithuanian", "native": "Lietuvių"},
    {"code": "mk", "name": "Macedonian", "native": "Македонски"},
    {"code": "ms", "name": "Malay", "native": "Bahasa Melayu"},
    {"code": "ml", "name": "Malayalam", "native": "മലയാളം"},
    {"code": "mr", "name": "Marathi", "native": "मराठी"},
    {"code": "mn", "name": "Mongolian", "native": "Монгол"},
    {"code": "ne", "name": "Nepali", "native": "नेपाली"},
    {"code": "no", "name": "Norwegian", "native": "Norsk"},
    {"code": "fa", "name": "Persian", "native": "فارسی"},
    {"code": "pl", "name": "Polish", "native": "Polski"},
    {"code": "pt", "name": "Portuguese", "native": "Português"},
    {"code": "pa", "name": "Punjabi", "native": "ਪੰਜਾਬੀ"},
    {"code": "ro", "name": "Romanian", "native": "Română"},
    {"code": "ru", "name": "Russian", "native": "Русский"},
    {"code": "sr", "name": "Serbian", "native": "Српски"},
    {"code": "sk", "name": "Slovak", "native": "Slovenčina"},
    {"code": "sl", "name": "Slovenian", "native": "Slovenščina"},
    {"code": "es", "name": "Spanish", "native": "Español"},
    {"code": "sw", "name": "Swahili", "native": "Kiswahili"},
    {"code": "sv", "name": "Swedish", "native": "Svenska"},
    {"code": "tl", "name": "Tagalog", "native": "Tagalog"},
    {"code": "ta", "name": "Tamil", "native": "தமிழ்"},
    {"code": "te", "name": "Telugu", "native": "తెలుగు"},
    {"code": "th", "name": "Thai", "native": "ไทย"},
    {"code": "tr", "name": "Turkish", "native": "Türkçe"},
    {"code": "uk", "name": "Ukrainian", "native": "Українська"},
    {"code": "ur", "name": "Urdu", "native": "اردو"},
    {"code": "uz", "name": "Uzbek", "native": "Oʻzbekcha"},
    {"code": "vi", "name": "Vietnamese", "native": "Tiếng Việt"},
    {"code": "cy", "name": "Welsh", "native": "Cymraeg"},
    {"code": "zu", "name": "Zulu", "native": "isiZulu"},
)

LANGUAGE_BY_CODE = {language["code"]: language for language in LANGUAGES}


def valid_language(code: str) -> bool:
    return code.lower() in LANGUAGE_BY_CODE


def language_name(code: str) -> str:
    return LANGUAGE_BY_CODE[code.lower()]["name"]
