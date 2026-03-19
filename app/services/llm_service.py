import google.generativeai as genai
import logging
import asyncio
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from google.generativeai.types import GenerationConfig
from app.core.config import settings
from app.models.schemas import AnalyzeEmailResponse
from app.services.prompt_builder import build_analysis_prompt

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        # Singleton pattern: Reutilizamos a instância do model
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.generation_config = GenerationConfig(
            temperature=0.1,
            top_p=0.9,
            max_output_tokens=2048,
            response_mime_type="application/json",
        )
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(min=1, max=5),
        reraise=True,
        before_sleep=lambda retry_state: logger.warning(f"Retrying LLM call (attempt {retry_state.attempt_number})...")
    )
    async def _call_llm(self, prompt: str) -> str:
        """
        Chamada interna para o Gemini com timeout e retry.
        """
        response = await self.model.generate_content_async(
            prompt,
            generation_config=self.generation_config,
            request_options={"timeout": 10}
        )
        return response.text if response else ""

    async def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analisa o texto do email usando IA e retorna um dicionário validado.
        """
        if not settings.GEMINI_API_KEY:
             logger.info("Simulação (Sem API Key)")
             return AnalyzeEmailResponse(reasoning="Simulação (Sem API Key).").model_dump()

        prompt = build_analysis_prompt(text)
        
        try:
            logger.info("Calling LLM (Gemini)")
            raw_text = await self._call_llm(prompt)
            
            if not raw_text:
                return self._fallback("LLM retornou resposta vazia.")

            # Validação via Pydantic diretamente do JSON
            try:
                validated_data = AnalyzeEmailResponse.model_validate_json(raw_text)
                return validated_data.model_dump()
            except Exception as ve:
                logger.error(f"Erro de validação Pydantic no JSON da IA: {ve}")
                return self._fallback(f"JSON inválido da IA: {ve}")

        except Exception as e:
            logger.error(f"Falha crítica na chamada do LLM: {e}", exc_info=True)
            return self._fallback(str(e))

    def _fallback(self, reason: str) -> Dict[str, Any]:
        """
        Retorna uma resposta padrão segura em caso de falha.
        """
        return AnalyzeEmailResponse(
            reasoning=f"Falha na análise: {reason}"
        ).model_dump()

# Instância Singleton
llm_service = LLMService()
