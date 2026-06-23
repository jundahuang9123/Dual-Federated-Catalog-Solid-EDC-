from fastapi import FastAPI

from core.config import load_active_mode


def create_app() -> FastAPI:
    mode = load_active_mode()
    app = FastAPI(title="Dual-Substrate Federated Catalog")

    @app.get("/status")
    def status() -> dict[str, str]:
        return {"mode": mode.name, "status": "ok"}

    return app


app = create_app()

