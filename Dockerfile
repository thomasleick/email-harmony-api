FROM python:3.12-slim

WORKDIR /app

# Instalar dependências de sistema necessárias para PDF se precisar
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expor a porta que o Uvicorn vai rodar
EXPOSE 8000

# Executar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
