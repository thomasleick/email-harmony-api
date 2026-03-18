# Email Harmony API

Backend financeiro escalável construído com **FastAPI** e orquestrado por Clean Architecture, visando classificar emails como "Produtivos" ou "Improdutivos" usando inteligência artificial de ponta (Gemini 1.5).

## 🚀 Arquitetura e Engenharia

Este projeto "grita Engenharia Sênior", entregando:
1. **Domain Layer:** Entidades agnósticas (Pydantic models e Enums separadamente).
2. **LLM Determinístico:** Modelos isolados em `Service` controlados com temperatura fechada `0.0`.
3. **Resiliência a Falhas:** Sistema agressivo de `Fallback` que suporta anomalias de formatação da IA. Regex atua em segundo nível caso o JSON venha envelopado em markdown falso. Não há crashes.
4. **Cache Eficiente:** Memória global usando assinatura forte via `SHA-256` combinado com `Time-To-Live` (TTL) de 1 hora. Evita custo dobrado no LLM para textos idênticos.
5. **Análise Robusta de PDF:** Tolerância e validação profunda de Empty/No-text strings usando `pdfplumber`.
6. **Deploy Ready:** `Dockerfile` multi-stage ready (gunicorn/uvicorn bind) na raiz.

## 🛠 Tecnologias

- **Python 3.12+**
- **FastAPI** + **Uvicorn**
- **Pydantic V2**
- **Google Generative AI** (Gemini)
- **Pytest** para asserções

## 📦 Como rodar localmente

1. Inicialize seu virtualenv:
\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
\`\`\`

2. Defina suas variáveis (opcional):
Crie um arquivo `.env` na raiz:
\`\`\`env
GEMINI_API_KEY=Sua_Chave_Aqvi_AIzaSy...
CACHE_TTL_SECONDS=3600
\`\`\`

3. Gire o motor:
\`\`\`bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
\`\`\`

## 🧪 Testes Unitários

Executamos `pytest` de forma autônoma:
\`\`\`bash
pytest tests/ -v
\`\`\`

## 🔌 API Endpoint: `POST /api/v1/analyze-email`

Aceita form inputs de multiplas formas (Multipart / Form-Data):
- Campo `text`: string limpa do corpo do email
- Campo `file`: upload binário de arquivo (`.txt` ou `.pdf`)

**Exemplo Retorno JSON Rigoroso:**
\`\`\`json
{
  "classification": "Produtivo",
  "confidence": 0.98,
  "reasoning": "Texto possui dados de contrato bancário",
  "suggested_response": "Prezado, estamos analisando..."
}
\`\`\`
