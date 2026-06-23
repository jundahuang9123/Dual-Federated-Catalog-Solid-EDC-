import logging

import httpx
import pytest

from modes.solid.registry import SolidRegistryCheck, SolidRegistryError

REGISTRY_URL = "https://registry.example/public/test/"
WEBID_ONE = "https://pod.example/alice/profile/card#me"
WEBID_TWO = "https://pod.example/bob/profile/card#me"
WEBID_FALLBACK = "https://pod.example/fallback/profile/card#me"


def _client_for(responses: dict[str, str | tuple[int, str]]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        response = responses.get(str(request.url), (500, "unexpected URL"))
        status, body = response if isinstance(response, tuple) else (200, response)
        return httpx.Response(status, text=body, headers={"Content-Type": "text/turtle"})

    return httpx.Client(transport=httpx.MockTransport(handler))


def _registry(client: httpx.Client) -> SolidRegistryCheck:
    return SolidRegistryCheck(
        registry_url=REGISTRY_URL,
        cache_ttl_seconds=0,
        http_client=client,
    )


def test_registry_reads_two_level_ldp_member_resources() -> None:
    client = _client_for(
        {
            REGISTRY_URL: f"""
                @prefix ldp: <http://www.w3.org/ns/ldp#> .
                <{REGISTRY_URL}> ldp:contains
                    <{REGISTRY_URL}member-alice>,
                    <{REGISTRY_URL}member-bob> .
            """,
            f"{REGISTRY_URL}member-alice": f"""
                @prefix foaf: <http://xmlns.com/foaf/0.1/> .
                <#it> a foaf:Group ;
                    foaf:member <{WEBID_ONE}> .
            """,
            f"{REGISTRY_URL}member-bob": f"""
                @prefix foaf: <http://xmlns.com/foaf/0.1/> .
                <#it> a foaf:Group ;
                    foaf:member <{WEBID_TWO}> .
            """,
        }
    )

    registry = _registry(client)

    assert registry.is_member(WEBID_ONE)
    assert registry.is_member(WEBID_TWO)
    assert not registry.is_member("https://pod.example/not-listed/profile/card#me")


def test_registry_falls_back_to_first_thing_when_it_is_absent() -> None:
    client = _client_for(
        {
            REGISTRY_URL: f"""
                @prefix ldp: <http://www.w3.org/ns/ldp#> .
                <{REGISTRY_URL}> ldp:contains <{REGISTRY_URL}member-fallback> .
            """,
            f"{REGISTRY_URL}member-fallback": f"""
                @prefix foaf: <http://xmlns.com/foaf/0.1/> .
                <{REGISTRY_URL}member-fallback> a foaf:Group ;
                    foaf:member <{WEBID_FALLBACK}> .
            """,
        }
    )

    assert _registry(client).is_member(WEBID_FALLBACK)


def test_registry_skips_member_resource_without_foaf_member(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING, logger="modes.solid.registry")
    client = _client_for(
        {
            REGISTRY_URL: f"""
                @prefix ldp: <http://www.w3.org/ns/ldp#> .
                <{REGISTRY_URL}> ldp:contains
                    <{REGISTRY_URL}member-empty>,
                    <{REGISTRY_URL}member-alice> .
            """,
            f"{REGISTRY_URL}member-empty": """
                @prefix foaf: <http://xmlns.com/foaf/0.1/> .
                <#it> a foaf:Group .
            """,
            f"{REGISTRY_URL}member-alice": f"""
                @prefix foaf: <http://xmlns.com/foaf/0.1/> .
                <#it> a foaf:Group ;
                    foaf:member <{WEBID_ONE}> .
            """,
        }
    )

    registry = _registry(client)

    assert registry.is_member(WEBID_ONE)
    assert "did not yield foaf:member" in caplog.text


def test_registry_404_fails_closed() -> None:
    registry = _registry(_client_for({REGISTRY_URL: (404, "")}))

    with pytest.raises(SolidRegistryError):
        registry.is_member(WEBID_ONE)


def test_registry_refresh_failure_can_serve_existing_cache() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                200,
                text=f"""
                    @prefix ldp: <http://www.w3.org/ns/ldp#> .
                    <{REGISTRY_URL}> ldp:contains <{REGISTRY_URL}member-alice> .
                """,
                headers={"Content-Type": "text/turtle"},
            )
        if calls == 2:
            return httpx.Response(
                200,
                text=f"""
                    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
                    <#it> a foaf:Group ;
                        foaf:member <{WEBID_ONE}> .
                """,
                headers={"Content-Type": "text/turtle"},
            )
        return httpx.Response(503, text="down")

    registry = _registry(httpx.Client(transport=httpx.MockTransport(handler)))

    assert registry.is_member(WEBID_ONE)
    assert registry.is_member(WEBID_ONE)
    assert not registry.registry_reachable()
