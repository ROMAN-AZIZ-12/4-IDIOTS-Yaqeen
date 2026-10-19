import pytest

from app.config import ConfigurationError, CorsSettings, DatabaseSettings, Settings, load_settings


def test_missing_settings_report_names_only(monkeypatch):
    for name in Settings.model_fields:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-sensitive-marker")
    with pytest.raises(ConfigurationError) as caught:
        load_settings(Settings)
    message = str(caught.value)
    assert "DATABASE_URL" in message
    assert "FRONTEND_ORIGIN" in message
    assert "synthetic-sensitive-marker" not in message
    assert caught.value.__suppress_context__


def test_invalid_database_value_is_not_disclosed(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "invalid-sensitive-marker")
    with pytest.raises(ConfigurationError) as caught:
        load_settings(DatabaseSettings)
    assert str(caught.value) == "Missing or invalid environment variables: DATABASE_URL"


@pytest.mark.parametrize("origin", ["*", "https://*.invalid", "https://example.invalid/path"])
def test_cors_rejects_non_origins(monkeypatch, origin):
    monkeypatch.setenv("FRONTEND_ORIGIN", origin)
    with pytest.raises(ConfigurationError):
        load_settings(CorsSettings)
