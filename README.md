# Email Harmony API 🧠

Backend financeiro escalável construído com **FastAPI** e orquestrado por Clean Architecture, transformando emails em dados operacionais acionáveis usando **GenAI (Gemini 1.5 Flash)**.

## 🚀 Arquitetura e Engenharia de Elite

Este projeto entrega um motor de triagem de nível corporativo e resiliente:
1.  **Motor Assíncrono:** Backend totalmente não-bloqueante para máxima concorrência.
2.  **Resiliência de Produção:** Implementação de retries com **Exponential Backoff** (via `tenacity`) e timeouts por requisição.
3.  **Inteligência Multidimensional:** Classificação, Sentimento (-1.0 a 1.0) e Urgência com **Priority Score** (0.0 a 1.0).
4.  **NLP Preprocessing:** Pipeline para normalização Unicode e extração determinística de arquivos `.pdf`.
5.  **Schema Robust com Pydantic:** Validação rigorosa e fallbacks automáticos para garantir zero crashes em caso de respostas inesperadas da IA.
6.  **Cache Inteligente v2:** Sistema de cache em memória com assinatura SHA-256 e versionamento de chave.

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

```bash
pytest tests/ -v
```

## 🐳 Docker Deployment

Para rodar a aplicação em um container (estilo Render):

1.  **Build:**
    ```bash
    docker build -t email-harmony-api .
    ```
2.  **Run:**
    ```bash
    docker run -p 8000:8000 --env-file .env email-harmony-api
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
