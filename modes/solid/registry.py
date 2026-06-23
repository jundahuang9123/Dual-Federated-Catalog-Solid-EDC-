# Adapted from tmdt-buw/semantic-data-catalog (F. Hoelken et al.), Apache-2.0.
"""Solid registry membership check.

This reimplements the read-membership slice from frontend/src/solidCatalog.js:
load a registry container, read its ldp:contains resources, and collect each
resource's foaf:member WebID.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

import httpx
from rdflib import Graph, Namespace, URIRef

from core.interfaces.registry import RegistryCheck
from core.shared.rdf import guess_rdflib_format

DEFAULT_SOLID_REGISTRY_URL = (
    "https://tmdt-solid-community-server.de/semanticdatacatalog/public/stadt-wuppertal"
)

LDP = Namespace("http://www.w3.org/ns/ldp#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")


class SolidRegistryError(RuntimeError):
    pass


def normalize_container_url(value: str) -> str:
    if not value:
        return ""
    return value if value.endswith("/") else f"{value}/"


@dataclass
class SolidRegistryCheck(RegistryCheck):
    registry_url: str = field(
        default_factory=lambda: normalize_container_url(
            os.getenv("SOLID_REGISTRY_URL", DEFAULT_SOLID_REGISTRY_URL)
        )
    )
    cache_ttl_seconds: float = field(
        default_factory=lambda: float(os.getenv("SOLID_REGISTRY_CACHE_SECONDS", "30"))
    )
    timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("SOLID_REGISTRY_TIMEOUT_SECONDS", "10"))
    )
    http_client: httpx.Client | None = None

    def __post_init__(self) -> None:
        self.registry_url = normalize_container_url(self.registry_url)
        self._members_cache: set[str] | None = None
        self._cache_expires_at = 0.0
        self.last_error: str | None = None

    def is_member(self, participant_id: str) -> bool:
        webid = (participant_id or "").strip()
        if not webid:
            return False
        return webid in self.load_members()

    def registry_reachable(self) -> bool:
        try:
            self.load_members(force_refresh=True)
            return True
        except SolidRegistryError:
            return False

    def load_members(self, *, force_refresh: bool = False) -> set[str]:
        now = time.monotonic()
        if not force_refresh and self._members_cache is not None and now < self._cache_expires_at:
            return set(self._members_cache)

        if not self.registry_url:
            self.last_error = "SOLID_REGISTRY_URL is not configured"
            raise SolidRegistryError(self.last_error)

        try:
            members = self._load_members_uncached()
        except Exception as exc:
            self.last_error = f"Failed to load Solid registry {self.registry_url}: {exc}"
            raise SolidRegistryError(self.last_error) from exc

        self._members_cache = members
        self._cache_expires_at = now + self.cache_ttl_seconds
        self.last_error = None
        return set(members)

    def _client(self) -> httpx.Client:
        return self.http_client or httpx.Client(timeout=self.timeout_seconds)

    def _fetch_graph(self, url: str) -> Graph:
        client = self._client()
        close_client = self.http_client is None
        try:
            response = client.get(
                url,
                headers={
                    "Accept": (
                        "text/turtle, application/ld+json;q=0.9, "
                        "application/rdf+xml;q=0.8, */*;q=0.1"
                    )
                },
            )
        finally:
            if close_client:
                client.close()

        if response.status_code == 404:
            raise SolidRegistryError(f"registry resource not found: {url}")
        response.raise_for_status()

        graph = Graph()
        content_type = response.headers.get("content-type")
        graph.parse(
            data=response.text,
            publicID=url,
            format=guess_rdflib_format(content_type),
        )
        return graph

    def _load_members_uncached(self) -> set[str]:
        container_graph = self._fetch_graph(self.registry_url)
        members = {str(member) for member in container_graph.objects(None, FOAF.member)}
        resource_urls = {
            str(resource)
            for resource in container_graph.objects(URIRef(self.registry_url), LDP.contains)
        }
        resource_urls.update(str(resource) for resource in container_graph.objects(None, LDP.contains))

        for resource_url in sorted(resource_urls):
            try:
                member_graph = self._fetch_graph(resource_url)
            except Exception:
                continue
            members.update(str(member) for member in member_graph.objects(None, FOAF.member))

        return members

