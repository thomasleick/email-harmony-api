import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import router as analyze_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="Email Harmony API",
    description="Backend escalável em FastAPI de classificação textual turbinado por Gemini AI",
    version="1.0.0"
)

# Configuração de CORS para permitir que o Frontend (Next.js) se conecte globalmente no dev mode
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Atenção: ajustar domínios em Prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Versionamento implícito
app.include_router(analyze_router, prefix="/api/v1", tags=["Analysis"])

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "message": "Email Harmony API is fully operational"}
