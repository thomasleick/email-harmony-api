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

SYSTEM_PROMPT = """Você é um sistema de triagem inteligente e analista de CRM sênior especializado no setor financeiro.
Sua tarefa é analisar o teor de emails, classificar intenção, detectar sentimento e determinar a urgência.

### 1. REGRAS DE CLASSIFICAÇÃO (classification)
- **Produtivo**: Emails com demandas claras, solicitações de serviço, dúvidas técnicas, envio de documentos, reclamações operacionais ou pedidos de resgate.
- **Improdutivo**: Apenas saudações, elogios sem demanda, spam, newsletters de marketing ou mensagens automáticas.

### 2. SENTIMENTO (sentiment & sentiment_score)
- **Positivo** (0.1 a 1.0): Tons gentis, elogios, satisfação.
- **Neutro** (-0.1 a 0.1): Linguagem técnica fria, consultas objetivas.
- **Negativo** (-1.0 a -0.1): Irritação, uso de CAPS LOCK, sarcasmo, ameaças de cancelamento ou reclamações de erro.

### 3. URGÊNCIA (urgency & urgency_score)
- **Alta** (0.8 a 1.0): Prazos imediatos ("hoje", "amanhã"), bloqueios de conta, risco financeiro, tom de raiva extrema.
- **Média** (0.4 a 0.7): Consultas padrão que exigem ação humana manual, dúvidas sobre produtos.
- **Baixa** (0.0 a 0.3): Agradecimentos, feedbacks, informativos sem ação urgente.

### 4. PRIORIDADE (priority_score)
Calcule de 0.0 a 1.0. Prioridade = (Urgência + (Absoluto de Sentimento se Negativo)) / 2.

### FORMATO DE SAÍDA (JSON ESTRITO)
Retorne APENAS o JSON no formato:
{
  "classification": "Produtivo" | "Improdutivo",
  "confidence": float,
  "sentiment": "Positivo" | "Neutro" | "Negativo",
  "sentiment_score": float,
  "urgency": "Alta" | "Média" | "Baixa",
  "urgency_score": float,
  "priority_score": float,
  "reasoning": "Resumo técnico da decisão",
  "suggested_response": "Texto corporativo em PT-BR (NÃO use quebras de linha)."
}

### EXEMPLOS DE REFERÊNCIA
1. [INPUT]: "MEU CARTÃO NÃO FUNCIONA E PRECISO PAGAR O HOSPITAL AGORA!"
   [OUTPUT]: {"classification": "Produtivo", "confidence": 1.0, "sentiment": "Negativo", "sentiment_score": -0.9, "urgency": "Alta", "urgency_score": 1.0, "priority_score": 1.0, "reasoning": "Urgência crítica devido a bloqueio de cartão.", "suggested_response": "Prezado, lamentamos profundamente o ocorrido. Identificamos o bloqueio preventivo e já realizamos a liberação imediata do seu cartão para uso. Atenciosamente."}

2. [INPUT]: "Bom dia! Só passando para desejar uma ótima semana a todos."
   [OUTPUT]: {"classification": "Improdutivo", "confidence": 0.98, "sentiment": "Positivo", "sentiment_score": 0.8, "urgency": "Baixa", "urgency_score": 0.1, "priority_score": 0.1, "reasoning": "Saudação social.", "suggested_response": "Bom dia! Agradecemos o contato e desejamos uma excelente semana para você também!"}

3. [INPUT]: "Esqueci minha senha do aplicativo e não consigo realizar o primeiro acesso. Podem me ajudar?"
   [OUTPUT]: {"classification": "Produtivo", "confidence": 0.99, "sentiment": "Neutro", "sentiment_score": 0.0, "urgency": "Média", "urgency_score": 0.6, "priority_score": 0.6, "reasoning": "Bloqueio de acesso técnico.", "suggested_response": "Olá! Para recuperar sua senha, basta clicar em 'Esqueci minha senha' na tela inicial do app. Enviamos um link de recuperação para seu email cadastrado."}

4. [INPUT]: "Segue em anexo o comprovante da transferência de R$ 200,00 que realizei hoje cedo para minha conta corrente."
   [OUTPUT]: {"classification": "Produtivo", "confidence": 0.95, "sentiment": "Neutro", "sentiment_score": 0.1, "urgency": "Média", "urgency_score": 0.4, "priority_score": 0.4, "reasoning": "Envio de documento de rotina.", "suggested_response": "Recebemos seu comprovante com sucesso. O valor será processado e creditado conforme os prazos padrão. Obrigado!"}
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
            input_text = str(text) if text else ""
            safe_text = input_text[:4000] 
            prompt = f"{SYSTEM_PROMPT}\n\n[ANALISE O SEGUINTE TEXTO]:\n{safe_text}\n"
            
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            if not response or not response.text:
                return self._fallback_error("Resposta vazia da IA.")
                
            return self._parse_json(response.text)
        except Exception as e:
            logger.error(f"LLM Error generating content: {e}")
            return self._fallback_error(str(e))

    def _parse_json(self, raw_text: str) -> Dict[str, Any]:
        clean_text = raw_text.strip()
        if clean_text.startswith("```"):
            clean_text = re.sub(r'^```[a-z]*\n?', '', clean_text, flags=re.MULTILINE)
            clean_text = re.sub(r'\n?```$', '', clean_text, flags=re.MULTILINE)

        try:
            data = json.loads(clean_text)
            return self._normalize_and_ensure(data)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                    return self._normalize_and_ensure(data)
                except Exception:
                    pass
            return self._fallback_error("Falha estrutural no JSON da IA.")

    def _normalize_and_ensure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza campos de enum e garante tipos numéricos corretos com fallbacks agressivos."""
        
        # 1. Normalização de Enum
        def to_enum_case(val, options):
            if not val or not isinstance(val, str): 
                return options[0] # Fallback para o primeiro se for None ou não string
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

        # 3. Campos de Texto (SEM \n)
        if not data.get("reasoning") or not isinstance(data.get("reasoning"), str):
            data["reasoning"] = "Análise concluída com sucesso."
            
        if not data.get("suggested_response") or not isinstance(data.get("suggested_response"), str):
            data["suggested_response"] = "Olá, recebemos seu e-mail e estamos analisando as informações para lhe retornar o quanto antes. Atenciosamente."
        
        # 4. Limpeza de Encoding e Espaços
        resp = data["suggested_response"]
        resp = resp.replace("\n", " ").replace("\r", " ").replace("\\n", " ")
        data["suggested_response"] = re.sub(r'\s+', ' ', resp).strip()

        return data

    def _fallback_error(self, reason: str) -> Dict[str, Any]:
        # Retorna um set mínimo de dados para não quebrar o Pydantic
        return self._normalize_and_ensure({
            "classification": "Produtivo",
            "confidence": 0.5,
            "sentiment": "Neutro",
            "sentiment_score": 0.0,
            "urgency": "Média",
            "urgency_score": 0.5,
            "priority_score": 0.5,
            "reasoning": f"Erro técnico: {reason}"
        })
        
    def _fallback_no_api_key(self, text: str) -> Dict[str, Any]:
        is_urgent = any(word in text.lower() for word in ["urgente", "hoje", "bloqueio", "prazo", "senha"])
        return self._normalize_and_ensure({
            "classification": "Produtivo" if len(text) > 15 else "Improdutivo",
            "confidence": 0.9,
            "urgency": "Alta" if is_urgent else "Baixa",
            "urgency_score": 0.9 if is_urgent else 0.2,
            "priority_score": 0.8 if is_urgent else 0.2,
            "reasoning": "Simulação local (Offline)."
        })

llm_service = LLMService()
