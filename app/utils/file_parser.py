import pdfplumber
from typing import BinaryIO
import logging

logger = logging.getLogger(__name__)

async def parse_text_file(upload_file: BinaryIO) -> str:
    content = upload_file.read()
    try:
        text = content.decode('utf-8').strip()
    except UnicodeDecodeError:
        text = content.decode('latin-1', errors='ignore').strip()
    
    if not text:
        raise ValueError("Não foi possível extrair texto do arquivo txt (arquivo vazio ou formatação incorreta).")
    return text

async def parse_pdf_file(upload_file: BinaryIO) -> str:
    text_content = []
    try:
        with pdfplumber.open(upload_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
    except Exception as e:
        logger.error(f"Erro ao parsear PDF: {e}")
        raise ValueError(f"Não foi possível parsear o arquivo PDF: {str(e)}")
    
    final_text = "\n".join(text_content).strip()
    if not final_text:
        raise ValueError("Não foi possível extrair texto do arquivo PDF (vazio ou criptografado).")
    
    return final_text
