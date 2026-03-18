from enum import Enum
from dataclasses import dataclass

class ClassificationEnum(str, Enum):
    PRODUTIVO = "Produtivo"
    IMPRODUTIVO = "Improdutivo"

class SentimentEnum(str, Enum):
    POSITIVO = "Positivo"
    NEUTRO = "Neutro"
    NEGATIVO = "Negativo"

class UrgencyEnum(str, Enum):
    ALTA = "Alta"
    MEDIA = "Média"
    BAIXA = "Baixa"

@dataclass
class EmailAnalysisEntity:
    classification: ClassificationEnum
    confidence: float
    reasoning: str
    suggested_response: str
    sentiment: SentimentEnum
    sentiment_score: float
    urgency: UrgencyEnum
    urgency_score: float
    priority_score: float
