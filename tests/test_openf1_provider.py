from src.providers.openf1_provider import fetch_openf1_data


def test_openf1_without_key_is_skipped_without_warning(monkeypatch):
    monkeypatch.delenv("OPENF1_API_KEY", raising=False)
    out = fetch_openf1_data()
    assert out["status"] == "skipped"
    assert out["enabled"] is False
    assert out["warnings"] == []
    assert "notes" in out
