# Solid Mode Operator Guide

Solid mode is the implemented handover path. It accepts pushed DCAT, authenticates the pusher, checks the pusher WebID against a Solid registry, validates with SHACL, stores in Fuseki, and exposes discovery APIs plus the UI.

## Quick Start

```bash
make up-solid
```

Services:

- Catalog API and UI: `http://localhost:8000`
- Fuseki Solid dataset: host port `3031`

For local development without real Solid-OIDC tokens:

```bash
SOLID_AUTH_MODE=trusted-header make up-solid
```

`trusted-header` logs a warning and trusts `X-Participant-Id`. Do not use it as proof of identity in shared or production environments.

## Registry

Point the catalog at a registry:

```bash
SOLID_REGISTRY_URL=https://tmdt-solid-community-server.de/semanticdatacatalog/public/test make up-solid
```

Presets:

- Test: `https://tmdt-solid-community-server.de/semanticdatacatalog/public/test`
- Gesundes Tal: `https://tmdt-solid-community-server.de/semanticdatacatalog/public/stadt-wuppertal`
- DACE: `https://tmdt-solid-community-server.de/semanticdatacatalog/public/dace`
- TimberConnect: `https://tmdt-solid-community-server.de/semanticdatacatalog/public/timberconnect`

Expected structure:

```turtle
@prefix ldp: <http://www.w3.org/ns/ldp#> .
<https://registry.example/public/test/> ldp:contains <https://registry.example/public/test/member-abc> .
```

Each contained resource:

```turtle
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
<#it> a foaf:Group ;
  foaf:member <https://some-pod.example/profile/card#me> .
```

Logs report:

- `registry_url`
- contained resource count
- resolved member count
- warnings for contained resources without `foaf:member`

## Auth

`SOLID_AUTH_MODE=oidc` is the default. It verifies the access token signature from OIDC discovery/JWKS, extracts the `webid` claim, and verifies a DPoP proof when `SOLID_AUTH_REQUIRE_DPOP=true`.

Still needing Florian confirmation:

- exact token scheme and claims issued by the Solid-OIDC setup
- whether the token always carries a `webid` claim
- whether DPoP `cnf.jkt` is present on access tokens

`SOLID_AUTH_MODE=trusted-header` is available only as a dev fallback.

## Push A Catalog

OIDC mode:

```bash
curl -i \
  -X POST http://localhost:8000/catalog \
  -H 'Authorization: DPoP <access-token>' \
  -H 'DPoP: <dpop-proof-jwt>' \
  -H 'Content-Type: text/turtle' \
  --data-binary @data/examples/solid/catalog-valid.ttl
```

Trusted-header mode:

```bash
curl -i \
  -X POST http://localhost:8000/catalog \
  -H 'Content-Type: text/turtle' \
  -H 'X-Participant-Id: https://example.org/profile/card#me' \
  --data-binary @data/examples/solid/catalog-valid.ttl
```

Responses:

- `200`: accepted
- `401`: auth failure
- `403`: authenticated WebID not registered
- `422`: RDF parse or SHACL validation failure
- `502`: Fuseki write failure

Each rejection includes `error`, `detail`, and `stage`.

## Discovery

```bash
curl http://localhost:8000/datasets
curl 'http://localhost:8000/datasets/detail?dataset_id=https%3A%2F%2Fexample.org%2Fdatasets%2Fair-quality'
```

Browse the UI at `http://localhost:8000`.

## Health And Readiness

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

`/ready` reports Fuseki and registry separately. Fuseki failure makes the app not ready. Registry failure is fail-closed for new pushes; if a cached membership list exists, pushes may use the stale cache briefly while logging a warning.

## Diagnosing

Successful push logs:

- auth success with WebID and auth mode
- registry decision
- validation success
- store graph id

Registry-format mismatch:

- contained resources found but zero members resolved
- warnings for resources that do not expose `#it foaf:member`

Fuseki problem:

- `/ready` shows `fuseki=false`
- push returns `502` at stage `store`

## Publish-Side Gap

This service expects a participant to POST DCAT to `/catalog`. Florian's current app writes catalogs into Pods and discovers them by pulling from Pods. Confirm whether a push-producer exists or whether a small publisher should be added to authenticate, read the Pod catalog, and POST it here.

