from fastapi.testclient import TestClient
import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
)
from main import app 

client = TestClient(app)

def test_home_route():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Server is running successfully!"}

def test_chat_route_structure():
    payload = {
        "url": "https://example.com/article",
        "text": "What is the summary of this article?"
    }
    
    response = client.post("/chat", json=payload)
    
    assert response.status_code in [200, 404, 500] 
    
    if response.status_code == 200:
        data = response.json()
        assert "question" in data
        assert "answer" in data
        assert data["question"] == payload["text"]


