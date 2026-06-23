"""Solid-mode push ingestion."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query, Request

from core.interfaces.ingest import IngestSource
from core.interfaces.registry import RegistryCheck
from core.interfaces.store import CatalogStore
from core.interfaces.validation import ValidationGate
from core.shared.rdf import guess_rdflib_format, serialize_rdf_to_turtle
from modes.solid.registry import SolidRegistryError
from modes.solid.store import graph_uri_for_participant


class SolidIngest(IngestSource):
    def __init__(
        self,
        registry: RegistryCheck,
        validation: ValidationGate,
        store: CatalogStore,
    ) -> None:
        self.registry = registry
        self.validation = validation
        self.store = store

    def routes(self) -> APIRouter:
        router = APIRouter()

        @router.post("/catalog")
        async def push_catalog(
            request: Request,
            participant_header: str | None = Header(default=None, alias="X-Participant-Id"),
            participant_query: str | None = Query(default=None, alias="participant_id"),
        ) -> dict[str, object]:
            participant_id = (participant_header or participant_query or "").strip()
            if not participant_id:
                raise HTTPException(
                    status_code=422,
                    detail={"errors": ["participant_id or X-Participant-Id is required"]},
                )

            try:
                registered = self.registry.is_member(participant_id)
            except SolidRegistryError as exc:
                raise HTTPException(status_code=422, detail={"errors": [str(exc)]}) from exc
            except Exception as exc:
                raise HTTPException(
                    status_code=422,
                    detail={"errors": [f"Solid registry lookup failed: {exc}"]},
                ) from exc

            if not registered:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "errors": [
                            f"participant not registered in Solid registry: {participant_id}"
                        ]
                    },
                )

            raw_body = (await request.body()).decode("utf-8")
            content_type = request.headers.get("content-type")
            rdf_format = guess_rdflib_format(content_type)
            validation = self.validation.validate(raw_body, format=rdf_format)
            if not validation.ok:
                raise HTTPException(status_code=422, detail={"errors": validation.errors})

            try:
                normalized_turtle = serialize_rdf_to_turtle(raw_body, format=rdf_format)
                graph_id = graph_uri_for_participant(participant_id)
                self.store.replace_graph(graph_id, normalized_turtle)
            except Exception as exc:
                raise HTTPException(
                    status_code=502,
                    detail={"errors": [f"catalog store write failed: {exc}"]},
                ) from exc

            return {
                "accepted": True,
                "mode": "solid",
                "participant_id": participant_id,
                "graph": graph_id,
            }

        return router

