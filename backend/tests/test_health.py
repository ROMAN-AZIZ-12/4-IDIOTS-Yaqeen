import importlib

from fastapi.testclient import TestClient


def test_health_exact_response_without_external_services(monkeypatch):
    # main's production app validates all settings; isolate the route factory
    # using a patched configuration loader before importing the module.
    from app import config
    monkeypatch.setenv("FRONTEND_ORIGIN", "https://frontend.example.invalid")
    monkeypatch.setattr(config, "get_settings", lambda: config.load_settings(config.CorsSettings))
    main = importlib.import_module("app.main")
    with TestClient(main.create_app(validate_all=False)) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert response.content == b'{"status":"ok"}'
        allowed = client.get("/health", headers={"Origin": "https://frontend.example.invalid"})
        assert allowed.headers["access-control-allow-origin"] == "https://frontend.example.invalid"
        denied = client.get("/health", headers={"Origin": "https://other.example.invalid"})
        assert "access-control-allow-origin" not in denied.headers
        assert client.get("/applications").status_code == 404
