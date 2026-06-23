# Mirrors modes/solid/ingest.py; wire when EDC substrate is ready.
"""EDC-mode push ingestion."""

from fastapi import APIRouter, HTTPException

from core.interfaces.ingest import IngestSource


class EdcIngest(IngestSource):
    def routes(self) -> APIRouter:
        router = APIRouter()

        @router.post("/catalog")
        async def push_catalog() -> None:
            raise HTTPException(
                status_code=501,
                detail={"errors": ["EDC mode not wired for testing yet"]},
            )

        return router

