def build_analysis_prompt(text: str) -> str:
    """
    Constrói o prompt estruturado para análise de email via Gemini.
    """
    system_instruction = """Você é um sistema de triagem inteligente especializado no setor financeiro.
Sua tarefa é analisar o teor de emails e retornar obrigatoriamente um JSON estruturado.

### REGRAS
1. Retorne APENAS o JSON. Sem explicações antecipadas ou posteriores.
2. Seja determinístico e siga rigorosamente o schema fornecido.

### EXEMPLOS
- INPUT: "MEU CARTÃO NÃO FUNCIONA!" -> OUTPUT: {"classification": "Produtivo", "confidence": 1.0, "sentiment": "Negativo", "sentiment_score": -0.9, "urgency": "Alta", "urgency_score": 1.0, "priority_score": 1.0, "reasoning": "Bloqueio de cartão.", "suggested_response": "Lamentamos o ocorrido. Realizamos a liberação imediata do seu cartão."}
- INPUT: "Bom dia!" -> OUTPUT: {"classification": "Improdutivo", "confidence": 0.98, "sentiment": "Positivo", "sentiment_score": 0.8, "urgency": "Baixa", "urgency_score": 0.1, "priority_score": 0.1, "reasoning": "Saudação social.", "suggested_response": "Bom dia! Agradecemos o contato."}
"""
    
    input_text = str(text) if text else ""
    safe_text = input_text[:4000]
    return f"{system_instruction}\n\nTEXTO PARA ANALISAR:\n\"{safe_text}\"\n\nJSON OUTPUT:\n"
