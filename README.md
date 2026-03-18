# Email Harmony API 🧠

Backend financeiro escalável construído com **FastAPI** e orquestrado por Clean Architecture, transformando emails em dados operacionais acionáveis usando **GenAI (Gemini 1.5 Flash)**.

## 🚀 Arquitetura e Engenharia de Elite

Este projeto entrega um motor de triagem de nível corporativo:
1.  **Inteligência Multidimensional:** Além de classificar entre "Produtivo" e "Improdutivo", o motor detecta **Sentimento** (-1.0 a 1.0) e **Urgência**, gerando um **Priority Score** (0.0 a 1.0) para triagem automática.
2.  **NLP Preprocessing:** Pipeline dedicado para normalização Unicode, remoção de cabeçalhos de email (`From:`, `Subject:`) e colapso de espaços mortos em arquivos `.pdf` e `.txt`.
3.  **LLM Determinístico:** Configurado em `temperature: 0.0` para máxima consistência nas respostas sugeridas.
4.  **Resiliência & Parsing:** Sistema de `Fallback` estruturado e reparo de JSON via Regex. Não há crashes por formatação da IA.
5.  **Cache Inteligente v2:** Sistema de cache em memória com assinatura SHA-256 e **versionamento de chave**, garantindo que mudanças no schema invalidem dados obsoletos automaticamente.
6.  **Pydantic V2:** Validação rigorosa de tipos e ranges (ex: scores sempre entre 0 e 1).

## 🛠 Tecnologias

-   **Python 3.12+**
-   **FastAPI** + **Uvicorn**
-   **Pydantic V2** (Validation & Serialization)
-   **Google Generative AI** (Gemini Flash)
-   **pdfplumber** (Extração determinística de PDF)

## 📦 Instalação e Execução

1.  **Virtualenv:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Configuração:**
    Crie um arquivo `.env` na raiz:
    ```env
    GEMINI_API_KEY=Sua_Chave_Ai...
    CACHE_TTL_SECONDS=3600
    ```

3.  **Start:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

## 🧪 Testes

```bash
pytest tests/ -v
```

## 🔌 API Endpoint: `POST /api/v1/analyze-email`

**Exemplo de Resposta Inteligente:**
```json
{
  "classification": "Produtivo",
  "confidence": 0.98,
  "sentiment": "Negativo",
  "sentiment_score": -0.85,
  "urgency": "Alta",
  "urgency_score": 0.95,
  "priority_score": 0.98,
  "reasoning": "Cliente frustrado reportando bloqueio de conta com prazo final hoje.",
  "suggested_response": "Prezado, lamentamos o ocorrido..."
}
```
