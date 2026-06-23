import logging
import os
from contextlib import asynccontextmanager
from dataclasses import asdict, is_dataclass
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.config import load_active_mode

logger = logging.getLogger(__name__)


def _as_dict(value: object) -> dict[str, object]:
    return asdict(value) if is_dataclass(value) else dict(value)  # type: ignore[arg-type]


def _readiness_payload(mode_name: str, status_payload: dict[str, object]) -> tuple[bool, dict[str, object]]:
    dependencies = status_payload.get("dependencies") or {}
    fuseki_ready = bool(dependencies.get("fuseki")) if isinstance(dependencies, dict) else False
    registry_value = dependencies.get("registry") if isinstance(dependencies, dict) else None
    registry_ready = registry_value is not False
    ready = bool(status_payload.get("operational")) and fuseki_ready and registry_ready
    return ready, {"mode": mode_name, "ready": ready, "dependencies": dependencies}


def _startup_checks(mode) -> None:
    if os.getenv("CATALOG_STARTUP_CHECKS", "true").lower() in {"0", "false", "no"}:
        logger.warning("Catalog startup dependency checks are disabled")
        return

    status_payload = _as_dict(mode.discovery.get_status())
    ready, payload = _readiness_payload(mode.name, status_payload)
    dependencies = payload["dependencies"]
    logger.info("Catalog startup dependency status", extra={"mode": mode.name, **payload})
    if isinstance(dependencies, dict) and dependencies.get("registry") is False:
        logger.warning("Solid registry is not reachable at startup", extra={"mode": mode.name})
    if mode.name == "solid" and isinstance(dependencies, dict) and dependencies.get("fuseki") is False:
        raise RuntimeError(f"Fuseki is not reachable: {status_payload.get('detail')}")
    if not ready:
        logger.warning("Catalog started but is not ready", extra={"mode": mode.name, **payload})


def create_app() -> FastAPI:
    mode = load_active_mode()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _startup_checks(mode)
        yield

    app = FastAPI(title="Dual-Substrate Federated Catalog", lifespan=lifespan)
    app.include_router(mode.ingest.routes())

    @app.get("/status")
    def status() -> dict[str, object]:
        status_result = mode.discovery.get_status()
        return _as_dict(status_result)

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "mode": mode.name}

    @app.get("/ready")
    def ready() -> JSONResponse:
        status_payload = _as_dict(mode.discovery.get_status())
        is_ready, payload = _readiness_payload(mode.name, status_payload)
        payload["status"] = status_payload
        return JSONResponse(status_code=200 if is_ready else 503, content=payload)

    @app.get("/datasets")
    def datasets() -> list[dict[str, object]]:
        return [_as_dict(item) for item in mode.discovery.list_datasets()]

    @app.get("/datasets/detail", response_model=None)
    def dataset_detail(dataset_id: str = Query(...)):
        detail = mode.discovery.get_dataset(dataset_id)
        if detail is None:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "dataset_not_found",
                    "detail": f"Dataset not found: {dataset_id}",
                    "stage": "discovery",
                },
            )
        return _as_dict(detail)

    ui_dir = Path(__file__).resolve().parent.parent / "ui"
    if (ui_dir / "index.html").exists():
        app.mount("/", StaticFiles(directory=str(ui_dir), html=True), name="ui")

    return app


app = create_app()
