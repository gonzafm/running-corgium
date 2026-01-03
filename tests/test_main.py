from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_read_hello_name():
    response = client.get("/hello/Gemini")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello Gemini"}

def test_read_hello_another_name():
    response = client.get("/hello/World")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
