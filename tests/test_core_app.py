import importlib


def test_core_app_imports_in_both_modes(monkeypatch) -> None:
    monkeypatch.setenv("CATALOG_STARTUP_CHECKS", "false")

    monkeypatch.setenv("CATALOG_MODE", "solid")
    import core.app as app_module

    app_module = importlib.reload(app_module)
    assert app_module.app.title == "Dual-Substrate Federated Catalog"

    monkeypatch.setenv("CATALOG_MODE", "edc")
    app_module = importlib.reload(app_module)
    assert app_module.app.title == "Dual-Substrate Federated Catalog"

