from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import ValidationError
from app.models.schemas import AnalyzeEmailResponse
from app.services.cache import cache
from app.services.llm_service import llm_service
from app.utils.file_parser import parse_text_file, parse_pdf_file
from app.utils.preprocessor import preprocess_email_text
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/analyze-email", response_model=AnalyzeEmailResponse)
async def analyze_email_endpoint(
    text: str | None = Form(None),
    file: UploadFile | None = File(None)
):
    """
    Classifica um email recebido. Suporta texto direto (Form input) ou upload de arquivos (.txt ou .pdf).
    """
    if not text and not file:
        raise HTTPException(status_code=400, detail="É necessário enviar o campo 'text' ou um 'file'.")

    final_text = ""

    # Parse do Upload
    if file:
        if file.content_type not in ["text/plain", "application/pdf"]:
            raise HTTPException(status_code=400, detail="Formato de arquivo não suportado. Utilize apenas .txt ou .pdf.")
        
        try:
            if file.content_type == "text/plain":
                final_text = await parse_text_file(file.file)
            elif file.content_type == "application/pdf":
                final_text = await parse_pdf_file(file.file)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
    else:
        # Se for string apenas, limpar espaços mortos na ponta
        final_text = text.strip() if text else ""

    if not final_text:
        raise HTTPException(status_code=400, detail="O texto fornecido para análise está vazio após o parse.")

    logger.info(f"Analisando Payload; Hash Cache será verificado.")

    # 0. NLP Preprocessing
    final_text = preprocess_email_text(final_text)

    # 1. Recupera do TTL Hash Cache 
    cached_result = cache.get(final_text)
    if cached_result:
        logger.info("Retornando dados idênticos via Cache (Hit)")
        return cached_result

    # 2. IA Processing
    logger.info("Cache Miss: Chamando API GenAI (Gemini)")
    llm_dict = llm_service.analyze(final_text)

    # 3. Pydantic validation (Integridade da Response)
    try:
        response_model = AnalyzeEmailResponse(**llm_dict)
    except ValidationError as e:
        logger.error(f"Falha de schema ao montar a resposta da IA: {e}")
        fallback_data = llm_service._fallback_error("Falha estrutural (Schema ValidationError).")
        response_model = AnalyzeEmailResponse(**fallback_data)

    # 4. Gravação de Cache Simple stateful e TTL
    cache.set(final_text, response_model.model_dump())
    
    return response_model
