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

SYSTEM_PROMPT = """Você é um sistema de triagem inteligente especializado no setor financeiro.
Sua tarefa é analisar o teor de emails e retornar obrigatoriamente um JSON estruturado.

### REGRAS
1. Retorne APENAS o JSON. Sem explicações antecipadas ou posteriores.
2. Formato:
{
  "classification": "Produtivo" | "Improdutivo",
  "confidence": float (0.0 a 1.0),
  "sentiment": "Positivo" | "Neutro" | "Negativo",
  "sentiment_score": float (-1.0 a 1.0),
  "urgency": "Alta" | "Média" | "Baixa",
  "urgency_score": float (0.0 a 1.0),
  "priority_score": float (0.0 a 1.0),
  "reasoning": "Resumo técnico curto",
  "suggested_response": "Resposta corporativa curta em PT-BR (NÃO use quebras de linha)."
}

### EXEMPLOS
- INPUT: "MEU CARTÃO NÃO FUNCIONA!" -> OUTPUT: {"classification": "Produtivo", "confidence": 1.0, "sentiment": "Negativo", "sentiment_score": -0.9, "urgency": "Alta", "urgency_score": 1.0, "priority_score": 1.0, "reasoning": "Bloqueio de cartão.", "suggested_response": "Lamentamos o ocorrido. Realizamos a liberação imediata do seu cartão."}
- INPUT: "Bom dia!" -> OUTPUT: {"classification": "Improdutivo", "confidence": 0.98, "sentiment": "Positivo", "sentiment_score": 0.8, "urgency": "Baixa", "urgency_score": 0.1, "priority_score": 0.1, "reasoning": "Saudação social.", "suggested_response": "Bom dia! Agradecemos o contato."}
"""

class LLMService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-flash-latest')
        self.generation_config = GenerationConfig(
            temperature=0.1, # Subi levemente para evitar repetições travadas
            top_p=0.9,
            max_output_tokens=2048,
            response_mime_type="application/json",
        )

    def analyze(self, text: str) -> Dict[str, Any]:
        if not settings.GEMINI_API_KEY:
             return self._fallback_no_api_key(text)

        try:
            input_text = str(text) if text else ""
            safe_text = input_text[:4000] 
            prompt = f"{SYSTEM_PROMPT}\n\nTEXTO PARA ANALISAR:\n\"{safe_text}\"\n\nJSON OUTPUT:\n"
            
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            raw_text = response.text if response else ""
            logger.info(f"LLM Raw Response: {repr(raw_text)}")
            
            if not raw_text:
                return self._fallback_error("Resposta vazia da IA.")
                
            return self._parse_json(raw_text)
        except Exception as e:
            logger.error(f"LLM Error generating content: {e}")
            return self._fallback_error(str(e))

    def _parse_json(self, raw_text: str) -> Dict[str, Any]:
        clean_text = raw_text.strip()
        
        # Limpar blocos de código se houver
        if clean_text.startswith("```"):
            clean_text = re.sub(r'^```[a-z]*\n?', '', clean_text, flags=re.MULTILINE)
            clean_text = re.sub(r'\n?```$', '', clean_text, flags=re.MULTILINE)

        try:
            data = json.loads(clean_text)
            return self._normalize_and_ensure(data)
        except json.JSONDecodeError as jde:
            logger.warning(f"JSONDecodeError: {jde}. tentando Regex.")
            # Fallback Regex
            match = re.search(r'(\{.*\})', clean_text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    return self._normalize_and_ensure(data)
                except Exception:
                    pass
            return self._fallback_error(f"Erro de parsing JSON: {str(jde)}")

    def _normalize_and_ensure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza campos de enum e garante tipos numéricos corretos com fallbacks agressivos."""
        
        # 1. Normalização de Enum
        def to_enum_case(val, options):
            if not val or not isinstance(val, str): 
                return options[0]
            for opt in options:
                if val.lower() == opt.lower(): return opt
            return options[0]

        data["classification"] = to_enum_case(data.get("classification"), ["Produtivo", "Improdutivo"])
        data["sentiment"] = to_enum_case(data.get("sentiment"), ["Neutro", "Positivo", "Negativo"])
        data["urgency"] = to_enum_case(data.get("urgency"), ["Média", "Baixa", "Alta"])

        # 2. Garantia de Scores
        def clamp(val, min_v, max_v, default):
            try:
                if val is None: return default
                f_val = float(val)
                return max(min_v, min(max_v, f_val))
            except (ValueError, TypeError):
                return default

        data["confidence"] = clamp(data.get("confidence"), 0.0, 1.0, 0.8)
        data["sentiment_score"] = clamp(data.get("sentiment_score"), -1.0, 1.0, 0.0)
        data["urgency_score"] = clamp(data.get("urgency_score"), 0.0, 1.0, 0.5)
        data["priority_score"] = clamp(data.get("priority_score"), 0.0, 1.0, 0.5)

        # 3. Campos de Texto
        if not data.get("reasoning") or not isinstance(data.get("reasoning"), str):
            data["reasoning"] = "Análise concluída."
            
        if not data.get("suggested_response") or not isinstance(data.get("suggested_response"), str):
            data["suggested_response"] = "Olá, recebemos seu e-mail e estamos analisando as informações. Atenciosamente."
        
        # 4. Limpeza radical de caracteres
        resp = data["suggested_response"]
        resp = resp.replace("\n", " ").replace("\r", " ").replace("\\n", " ").replace("\"", "'")
        data["suggested_response"] = re.sub(r'\s+', ' ', resp).strip()

        return data

    def _fallback_error(self, reason: str) -> Dict[str, Any]:
        return self._normalize_and_ensure({
            "classification": "Produtivo",
            "confidence": 0.5,
            "sentiment": "Neutro",
            "reasoning": f"Falha AI: {reason}"
        })
        
    def _fallback_no_api_key(self, text: str) -> Dict[str, Any]:
        return self._normalize_and_ensure({
            "reasoning": "Simulação (Sem API Key)."
        })

llm_service = LLMService()
