from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_analyze_email_empty_bad_request():
    # Envio completamente vazio do FormData
    response = client.post("/api/v1/analyze-email", data={})
    assert response.status_code == 400

def test_analyze_email_invalid_file_extension():
    # Enviando arquivo png no lugar do pdf
    files = {'file': ('test.png', b'conteudo fake de imagem', 'image/png')}
    response = client.post("/api/v1/analyze-email", files=files)
    assert response.status_code == 400
    assert "Formato de arquivo não suportado" in response.json()["detail"]

def test_analyze_email_valid_text():
    # Este teste passará utilizando o método Mock Fallback ou API dependendo da .env!
    data = {'text': 'Bom dia. Qual o status do meu empréstimo no contrato 4490?'}
    response = client.post("/api/v1/analyze-email", data=data)
    assert response.status_code == 200
    res_json = response.json()
    assert "classification" in res_json
    assert res_json["classification"] in ["Produtivo", "Improdutivo"]
    assert "confidence" in res_json
    assert "suggested_response" in res_json
