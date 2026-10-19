import importlib

from fastapi.testclient import TestClient


def test_health_exact_response_without_external_services(monkeypatch):
    # The served health app must import without unrelated service settings.
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.setenv("FRONTEND_ORIGIN", "https://frontend.example.invalid")
    main = importlib.reload(importlib.import_module("app.main"))
    with TestClient(main.app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert response.content == b'{"status":"ok"}'
        allowed = client.get("/health", headers={"Origin": "https://frontend.example.invalid"})
        assert allowed.headers["access-control-allow-origin"] == "https://frontend.example.invalid"
        denied = client.get("/health", headers={"Origin": "https://other.example.invalid"})
        assert "access-control-allow-origin" not in denied.headers
        assert client.get("/applications").status_code == 404
