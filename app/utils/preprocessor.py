"""
Módulo de Pré-Processamento de Texto (NLP).

Realiza limpeza e normalização do conteúdo de email antes de
enviar para a LLM, cumprindo o requisito explícito de NLP do desafio.
"""
import re
import unicodedata
import logging

logger = logging.getLogger(__name__)


def preprocess_email_text(raw_text: str) -> str:
    """
    Pipeline de pré-processamento NLP para emails.

    Etapas:
    1. Normalização Unicode (NFKD → NFC).
    2. Remoção de cabeçalhos técnicos de email (De:, Para:, Assunto:, etc.).
    3. Colapso de espaços em branco redundantes e linhas vazias consecutivas.
    4. Strip final.
    """
    if not raw_text:
        return raw_text

    text = raw_text

    # 1. Normalizar caracteres Unicode (acentos compostos → pré-compostos)
    text = unicodedata.normalize("NFC", text)

    # 2. Remover cabeçalhos técnicos de email (case-insensitive)
    header_pattern = re.compile(
        r"^(From|To|Cc|Bcc|Subject|Date|De|Para|Assunto|Data|Cópia|Cco|Enviado|Recebido|Reply-To|Content-Type|MIME-Version|X-[\w-]+):.*$",
        re.MULTILINE | re.IGNORECASE,
    )
    text = header_pattern.sub("", text)

    # 3. Remover separadores horizontais (----, ====, ____)
    text = re.sub(r"[-=_]{3,}", "", text)

    # 4. Colapsar múltiplos espaços em branco em uma única whitespace
    text = re.sub(r"[^\S\n]+", " ", text)

    # 5. Colapsar mais de 2 quebras de linha consecutivas em uma
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 6. Strip final
    text = text.strip()

    logger.info("Texto pré-processado: %d → %d chars", len(raw_text), len(text))
    return text
