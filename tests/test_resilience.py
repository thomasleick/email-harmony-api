import pytest
from unittest.mock import AsyncMock, patch
from app.services.llm_service import LLMService

@pytest.mark.asyncio
async def test_invalid_json_fallback():
    """
    Verifica se o sistema retorna o fallback seguro quando o LLM envia um JSON quebrado.
    """
    service = LLMService()
    
    # Mock do método interno de chamada ao LLM para retornar lixo
    with patch.object(service, '_call_llm', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "ESTE NÃO É UM JSON VÁLIDO { { ["
        
        # Executa a análise
        result = await service.analyze("Texto qualquer")
        
        # Verifica se o fallback foi acionado (usando os defaults do schema)
        assert result["classification"] == "Improdutivo"
        assert result["confidence"] == 0.0
        assert "Falha na análise" in result["reasoning"]
        assert "JSON inválido da IA" in result["reasoning"]
        assert "Olá! Recebemos sua mensagem" in result["suggested_response"]

@pytest.mark.asyncio
async def test_empty_response_fallback():
    """
    Verifica o fallback para resposta vazia.
    """
    service = LLMService()
    
    with patch.object(service, '_call_llm', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = ""
        
        result = await service.analyze("Texto qualquer")
        
        assert "LLM retornou resposta vazia" in result["reasoning"]
