from pydantic import BaseModel, Field
from typing import Optional

class TranslationRequest(BaseModel):
    text: str = Field(..., description="Text content to be translated")
    target_language: str = Field(..., description="Target language code (e.g. 'hi', 'mr', 'ta', 'gu', 'bn', 'es')")
    source_language: Optional[str] = Field("en", description="Source language code (default: 'en')")

class TranslationResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    provider: str = Field("NyayaSarathi AI Translation Engine", description="Translation provider used")
