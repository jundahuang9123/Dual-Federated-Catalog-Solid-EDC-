from dataclasses import asdict, is_dataclass

from fastapi import FastAPI

from core.config import load_active_mode


def create_app() -> FastAPI:
    mode = load_active_mode()
    app = FastAPI(title="Dual-Substrate Federated Catalog")
    app.include_router(mode.ingest.routes())

    @app.get("/status")
    def status() -> dict[str, object]:
        status_result = mode.discovery.get_status()
        return asdict(status_result) if is_dataclass(status_result) else dict(status_result)

    @app.get("/datasets")
    def datasets() -> list[dict[str, object]]:
        return [asdict(item) if is_dataclass(item) else dict(item) for item in mode.discovery.list_datasets()]

    return app


app = create_app()
