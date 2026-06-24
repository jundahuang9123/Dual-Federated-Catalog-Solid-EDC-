# Solid Registry Contract

## Status

Draft template.

This document defines the Solid registry shape expected by the central
federated catalogue in Solid mode. If the registry shape changes, update this
contract first, then adapt the checker and tests.

## Purpose

The registry is an admission-control source. A WebID listed in the configured
registry is allowed to publish DCAT RDF to the central catalogue. A WebID that
is not listed is rejected.

The registry does not publish catalogues automatically. The publisher still
sends the RDF payload; the central catalogue decides whether the authenticated
participant may publish it.

## Boundary

- The Solid publisher sends the RDF payload and participant identity.
- The central catalogue verifies identity, checks registry membership, validates
  RDF, and stores accepted metadata.
- The registry check answers only: "Is this WebID allowed to publish?"

## Configuration

Set the registry container URL with:

```text
SOLID_REGISTRY_URL=<registry-container-url>
```

Example:

```text
SOLID_REGISTRY_URL=https://example.org/public/registry/
```

## Expected RDF Shape

The default registry shape is:

```text
LDP container -> ldp:contains -> member resource -> foaf:member -> WebID
```

Registry container example:

```turtle
@prefix ldp: <http://www.w3.org/ns/ldp#> .

<https://registry.example/public/registry/>
    a ldp:Container ;
    ldp:contains
        <https://registry.example/public/registry/member-a>,
        <https://registry.example/public/registry/member-b> .
```

Member resource example:

```turtle
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

<#group>
    a foaf:Group ;
    foaf:member
        <https://alice.example/profile/card#me>,
        <https://bob.example/profile/card#me> .
```

A participant is registered when its WebID appears as an object of
`foaf:member` in any member resource reachable from the registry container.

## Membership Resolution

The central catalogue should:

1. Fetch `SOLID_REGISTRY_URL`.
2. Parse it as RDF.
3. Read all `ldp:contains` targets.
4. Fetch each contained member resource.
5. Parse each member resource as RDF.
6. Collect all `foaf:member` WebIDs.
7. Compare the authenticated WebID against that set.

## WebID Matching

WebID comparison is exact after basic string normalization:

- trim whitespace;
- keep fragment identifiers such as `#me`;
- preserve scheme and host;
- do not rewrite profile document URLs into WebIDs.

For example, `https://alice.example/profile/card#me` is not the same as
`https://alice.example/profile/card`.

## Failure And Cache Behaviour

The registry check should fail closed by default:

- unavailable registry: reject publication;
- unparsable registry RDF: reject publication;
- unavailable member resource: reject publication unless a documented cache
  policy says otherwise;
- WebID not found: reject publication.

Known unregistered participants should receive `403 Forbidden` with stage
`registry`. Registry availability or parsing failures should use a documented
error response.

Membership may be cached with `SOLID_REGISTRY_CACHE_SECONDS`, but caching must
not silently weaken admission control. The current policy is fail closed.

## Security Notes

In production-like Solid mode, the WebID must come from a verified Solid-OIDC
token or equivalent trusted identity mechanism. Client-supplied WebID headers
are acceptable only in explicit local/trusted-header mode.

The registry check does not prove that the RDF is truthful, that datasets
exist, or that the publisher is allowed to offer every dataset in the payload.
Those concerns belong to validation, provenance, governance, or future policy
checks.

## Change Process

When changing the registry structure:

1. Update this contract.
2. Add or update registry RDF fixtures.
3. Update `modes/solid/registry.py`.
4. Update tests.
5. Confirm publisher documentation still points to this contract.
