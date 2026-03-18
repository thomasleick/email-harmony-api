import google.generativeai as genai
import json
import logging
import re
from typing import Dict, Any
from google.generativeai.types import GenerationConfig
from app.core.config import settings

logger = logging.getLogger(__name__)

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

SYSTEM_PROMPT = """Você é um sistema de triagem inteligente e analista de CRM sênior.
Sua tarefa é analisar emails financeiros, classificar sua intenção, detectar o sentimento do cliente e determinar a urgência operacional.

### 1. DEFINIÇÃO DE CATEGORIAS (classification)
- **Produtivo**: Demandas operacionais, dúvidas sobre contas, envios de comprovantes, suporte, resgates.
- **Improdutivo**: Saudações, newsletters, spam, elogios isolados sem demanda.

### 2. SENTIMENTO (sentiment & sentiment_score)
Analise o tom emocional do texto:
- **Positivo** (score: 0.1 a 1.0): Agradecimentos, elogios, satisfação.
- **Neutro** (score: -0.1 a 0.1): Consultas puramente técnicas, informativas.
- **Negativo** (score: -1.0 a -0.1): Reclamações, frustração, irritação.

### 3. URGÊNCIA (urgency & urgency_score)
Determine o nível de prioridade baseado em regras explícitas:
- **Alta** (score: 0.8 a 1.0): Cliente irritado, risco financeiro iminente, bloqueio de conta/operação, prazo final explícito ("preciso hoje", "até amanhã").
- **Média** (score: 0.4 a 0.7): Solicitações que exigem resposta humana, dúvidas operacionais padrão, envio de documentos.
- **Baixa** (score: 0.0 a 0.3): Agradecimentos, informativos sem prazo, sugestões, feedbacks.

### 4. SCORE DE PRIORIDADE (priority_score)
Calcule um valor de 0.0 a 1.0 combinando Urgência e Sentimento.
Regra sugerida: Prioridade máxima para Urgência Alta + Sentimento Negativo.

### FORMATO DE SAÍDA (JSON ESTRITO)
Retorne OBRIGATORIAMENTE um JSON válido com todos os campos preenchidos:
{
  "classification": "Produtivo" | "Improdutivo",
  "confidence": float (0.0 a 1.0),
  "sentiment": "Positivo" | "Neutro" | "Negativo",
  "sentiment_score": float (-1.0 a 1.0),
  "urgency": "Alta" | "Média" | "Baixa",
  "urgency_score": float (0.0 a 1.0),
  "priority_score": float (0.0 a 1.0),
  "reasoning": "string curta (max 2 linhas)",
  "suggested_response": "string em PT-BR corporativo"
}

### EXEMPLO
Input: "Preciso do meu extrato agora, estou tentando fechar um contrato e não consigo acessar o app! Absurdo."
Output:
{
  "classification": "Produtivo",
  "confidence": 0.99,
  "sentiment": "Negativo",
  "sentiment_score": -0.85,
  "urgency": "Alta",
  "urgency_score": 0.95,
  "priority_score": 0.98,
  "reasoning": "Cliente com bloqueio de acesso e prazo crítico (contrato), demonstrando alta frustração.",
  "suggested_response": "Prezado,\\n\\nLamentamos o transtorno. Identificamos a urgência na sua solicitação. Nosso suporte técnico já está priorizando o seu acesso e o extrato será enviado para seu email seguro em instantes.\\n\\nAtenciosamente."
}
"""

class LLMService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-flash-latest')
        self.generation_config = GenerationConfig(
            temperature=0.0,
            top_p=0.1,
            max_output_tokens=1024,
            response_mime_type="application/json",
        )

    def analyze(self, text: str) -> Dict[str, Any]:
        if not settings.GEMINI_API_KEY:
             return self._fallback_no_api_key(text)

        try:
            prompt = f"{SYSTEM_PROMPT}\n\n[TEXTO DO CLIENTE]\n{text}\n"
            
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            return self._parse_json(response.text)
        except Exception as e:
            logger.error(f"LLM Error generating content: {e}")
            return self._fallback_error(str(e))

    def _parse_json(self, raw_text: str) -> Dict[str, Any]:
        try:
            data = json.loads(raw_text)
            return self._ensure_fields(data)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                    return self._ensure_fields(data)
                except Exception:
                    pass
            return self._fallback_error("Erro de Parsing de Estrutura da IA.")

    def _ensure_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Garante que todos os campos obrigatórios existam com valores padrão se necessário."""
        defaults = {
            "classification": "Produtivo",
            "confidence": 0.5,
            "sentiment": "Neutro",
            "sentiment_score": 0.0,
            "urgency": "Média",
            "urgency_score": 0.5,
            "priority_score": 0.5,
            "reasoning": "Processado com campos padrão.",
            "suggested_response": "Prezado,\\n\\nRecebemos sua mensagem e estamos analisando sua solicitação.\\n\\nAtenciosamente."
        }
        for field, default in defaults.items():
            if field not in data:
                data[field] = default
        return data

    def _fallback_error(self, reason: str) -> Dict[str, Any]:
        return self._ensure_fields({"reasoning": f"Erro detectado: {reason}"})
        
    def _fallback_no_api_key(self, text: str) -> Dict[str, Any]:
        is_urgent = "urgente" in text.lower() or "hoje" in text.lower()
        return self._ensure_fields({
            "classification": "Produtivo" if len(text) > 30 else "Improdutivo",
            "confidence": 0.8,
            "urgency": "Alta" if is_urgent else "Baixa",
            "urgency_score": 0.9 if is_urgent else 0.2,
            "priority_score": 0.85 if is_urgent else 0.3,
            "reasoning": "Modo de simulação (Sem API Key)."
        })

llm_service = LLMService()
