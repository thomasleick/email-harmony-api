from enum import Enum
from dataclasses import dataclass

class ClassificationEnum(str, Enum):
    PRODUTIVO = "Produtivo"
    IMPRODUTIVO = "Improdutivo"

@dataclass
class EmailAnalysisEntity:
    classification: ClassificationEnum
    confidence: float
    reasoning: str
    suggested_response: str
