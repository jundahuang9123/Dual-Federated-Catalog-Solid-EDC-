# Dual-Substrate Federated Catalog

Push-based central federated catalog for two separate substrates:

- `solid`: Solid-context publishers push DCAT catalog metadata into a Solid-mode pipeline.
- `edc`: EDC-context publishers push DCAT catalog metadata into an EDC-mode pipeline.

Only one mode is active per deployment. The two modes share a skeleton (`core/`) but keep their ingest, store, discovery, and identity handling separate under `modes/`.

## Current Status

Solid mode is wired for handover testing:

- `POST /catalog` accepts pushed RDF DCAT with `X-Participant-Id`.
- The participant WebID is checked against a real, configurable Solid registry.
- Conformant DCAT is validated with the adapted SHACL gate and stored in Fuseki.
- `GET /datasets` discovers stored datasets through SPARQL over Fuseki.
- `GET /status` reports mode, counts, and registry reachability.

EDC mode mirrors the same shape but is intentionally not operational yet.

## Layout

```text
core/                  Shared app shell, config, interfaces, and reusable utilities.
modes/solid/           Solid-mode concrete pipeline.
modes/edc/             EDC-mode concrete pipeline.
ui/                    Mode-agnostic discovery UI shell.
data/examples/         Example push payloads per mode.
tests/                 Unit and integration tests.
docker-compose.yaml    Compose profiles for solid and edc.
```

## Local Commands

```bash
make test
make up-solid
make up-edc
```

## Solid Mode: Testing Against A Real Registry

Start Solid mode:

```bash
SOLID_REGISTRY_URL=https://tmdt-solid-community-server.de/semanticdatacatalog/public/stadt-wuppertal \
make up-solid
```

`SOLID_REGISTRY_URL` must point to a Solid registry container whose contained
resources list members with `foaf:member <webid>`, matching Florian's
`solidCatalog.js` registry format.

Push a conformant Turtle catalog:

```bash
curl -i \
  -X POST http://localhost:8000/catalog \
  -H 'Content-Type: text/turtle' \
  -H 'X-Participant-Id: https://example.org/profile/card#me' \
  --data-binary @data/examples/solid/catalog-valid.ttl
```

Push a JSON-LD catalog:

```bash
curl -i \
  -X POST http://localhost:8000/catalog \
  -H 'Content-Type: application/ld+json' \
  -H 'X-Participant-Id: https://example.org/profile/card#me' \
  --data-binary @data/examples/solid/catalog-valid.jsonld
```

The WebID must be present in the configured registry. Registered + conformant
pushes return `200` and a named graph id. Unregistered WebIDs return `403`.
Malformed RDF or SHACL-invalid DCAT returns `422` with readable errors.

List discovered datasets:

```bash
curl http://localhost:8000/datasets
```

Check handover status:

```bash
curl http://localhost:8000/status
```

Re-pushing with the same WebID replaces that participant's named graph instead
of accumulating duplicate data.

## EDC Mode

`make up-edc` boots the EDC app and `/status` returns `mode=edc` with
`operational=false`. `POST /catalog` returns `501` until the EDC participant
registry and push contract are ready.

## Design Rules

- `core/` contains no mode-specific logic.
- `core/` must not import from `modes/`.
- Solid and EDC mode stores are separate.
- Push is the only implemented ingestion model for now.
- Reconciliation pull, real trust/identity, and domain-specific SHACL extensions are deferred.

## Attribution

This project reuses selected Apache-2.0 assets from Florian Hoelken et al.'s `tmdt-buw/semantic-data-catalog`. See [CREDITS.md](CREDITS.md) and [NOTICE](NOTICE).
