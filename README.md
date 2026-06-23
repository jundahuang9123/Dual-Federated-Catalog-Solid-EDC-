# Dual-Substrate Federated Catalog

Push-based central federated catalog for two separate substrates:

- `solid`: Solid-context publishers push DCAT catalog metadata into a Solid-mode pipeline.
- `edc`: EDC-context publishers push DCAT catalog metadata into an EDC-mode pipeline.

Only one mode is active per deployment. The two modes share a skeleton (`core/`) but keep their ingest, store, discovery, and identity handling separate under `modes/`.

## Current Status

This repository has been created as the local starting point for the work plan. The first implementation pass should start with reuse intake from `tmdt-buw/semantic-data-catalog`, including the SHACL shape, validation wrapper, DCAT serializer, Fuseki helpers, and UI assets where applicable.

No files from the upstream repository have been imported yet.

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

## Design Rules

- `core/` contains no mode-specific logic.
- `core/` must not import from `modes/`.
- Solid and EDC mode stores are separate.
- Push is the only implemented ingestion model for now.
- Reconciliation pull, real trust/identity, and domain-specific SHACL extensions are deferred.

## Attribution

This project is planned to reuse selected Apache-2.0 assets from Florian Hoelken et al.'s `tmdt-buw/semantic-data-catalog`. See [CREDITS.md](CREDITS.md) and [NOTICE](NOTICE).

