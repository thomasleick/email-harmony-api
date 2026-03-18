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

SYSTEM_PROMPT = """Você é um analista financeiro sênior corporativo.
Classifique o email recebido e retorne a resposta OBRIGATORIAMENTE formatada em JSON ESTRITO.

### DEFINIÇÃO DAS CATEGORIAS
1. **Produtivo**: Emails com demanda operacional, dúvidas sobre contas, envios de comprovantes, solicitações de suporte, pedidos de resgate/transferência.
2. **Improdutivo**: Emails sem necessidade de ação como saudações isoladas, felicitações, spam ou newsletters.

### INSTRUÇÕES E FORMATO
- Analise o contexto sem alucinar focar nos fatos.
- Escreva a "suggested_response" em PT-BR corporativo, gentil e direto.
- Se Produtivo, garanta ao cliente que o caso está em análise. Se Improdutivo, gere uma constatação educada ou ignore se for spam.
- O formato final de saída DEVE OBRIGATORIAMENTE ser JSON válido e seguir a estrutura exata:

{
  "classification": "Produtivo" ou "Improdutivo",
  "confidence": <float de 0.0 a 1.0>,
  "reasoning": "<explicação curta de no máximo 2 linhas>",
  "suggested_response": "<texto da resposta sugerida>"
}

### EXEMPLOS (FEW-SHOT)

Input: "Gostaria de solicitar o extrato do mês corrente referente à conta 1234."
Output:
{
  "classification": "Produtivo",
  "confidence": 0.98,
  "reasoning": "O cliente solicita documento financeiro da sua conta, configurando ação do suporte.",
  "suggested_response": "Prezado,\\n\\nRecebemos a sua solicitação. Nosso time já está processando e o extrato será enviado para seu email seguro em breve.\\n\\nAtenciosamente,\\nEquipe."
}

Input: "Parabéns equipe pelo excelente serviço de vocês! Excelente sexta-feira."
Output:
{
  "classification": "Improdutivo",
  "confidence": 0.99,
  "reasoning": "Apenas um elogio isolado de fim de semana, sem demanda operacional.",
  "suggested_response": "Prezado,\\n\\nAgradecemos profundamente o seu reconhecimento! Tenha uma excelente sexta-feira.\\n\\nAtenciosamente,\\nEquipe."
}
"""

class LLMService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-flash-latest')
        # Temperatura 0.0 garante determinismo. JSON mime_type garante schema robusto.
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
            prompt = f"{SYSTEM_PROMPT}\n\n[INÍCIO DO EMAIL DO CLIENTE]\n{text}\n[FIM DO EMAIL DO CLIENTE]"
            
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            return self._parse_json(response.text)
        except Exception as e:
            logger.error(f"LLM Error generating content: {e}")
            return self._fallback_error(str(e))

    def _parse_json(self, raw_text: str) -> Dict[str, Any]:
        """Tenta parsear JSON de forma resiliente, considerando eventuais anomalias da IA."""
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
            logger.warning("Falha crítica no JSON da IA, indo pro fallback. Texto bruto: %s", raw_text)
            return self._fallback_error("Erro de Parsing de Estrutura da IA.")

    def _fallback_error(self, reason: str) -> Dict[str, Any]:
        """Fallback ultra robusto, evita Crash da API do backend e frontend."""
        return {
            "classification": "Produtivo",
            "confidence": 0.5,
            "reasoning": f"Fallback ativado devido a erro interno ou timeout da IA: {reason}",
            "suggested_response": "Prezado,\\n\\nRecebemos seu email e nossa equipe iniciou a análise da solicitação. Retornaremos o mais breve possível com atualizações.\\n\\nAtenciosamente."
        }
        
    def _fallback_no_api_key(self, text: str) -> Dict[str, Any]:
        """Para funcionar em desenvolvimento se a chave (GEMINI_API_KEY) ainda não foi setada no .env"""
        is_prod = len(text) > 30
        return {
            "classification": "Produtivo" if is_prod else "Improdutivo",
            "confidence": 0.82,
            "reasoning": "Resolução de Mock via Fallback (Nenhuma API Key Configurada)",
            "suggested_response": "Prezado,\\n\\nAgradecemos o contato. Sua manifestação foi recebida com sucesso e nossa equipe responderá em breve.\\n\\nAtenciosamente,"
        }

llm_service = LLMService()
