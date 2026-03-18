from pydantic import BaseModel, Field
from app.domain.entities import ClassificationEnum

class AnalyzeEmailTextRequest(BaseModel):
    text: str = Field(..., description="O conteúdo do email a ser analisado.", min_length=1)

class AnalyzeEmailResponse(BaseModel):
    classification: ClassificationEnum
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    suggested_response: str
