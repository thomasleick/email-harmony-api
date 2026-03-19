from pydantic import BaseModel, Field
from app.domain.entities import ClassificationEnum, SentimentEnum, UrgencyEnum

class AnalyzeEmailTextRequest(BaseModel):
    text: str = Field(..., description="O conteúdo do email a ser analisado.", min_length=1)

class AnalyzeEmailResponse(BaseModel):
    classification: ClassificationEnum = ClassificationEnum.IMPRODUTIVO
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    sentiment: SentimentEnum = SentimentEnum.NEUTRO
    sentiment_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    urgency: UrgencyEnum = UrgencyEnum.BAIXA
    urgency_score: float = Field(default=0.0, ge=0.0, le=1.0)
    priority_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: str = "Resumo indisponível."
    suggested_response: str = "Olá! Recebemos sua mensagem e estamos processando as informações. Entraremos em contato em breve."
