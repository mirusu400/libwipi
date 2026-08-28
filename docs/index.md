---
myst:
  html_meta:
    description: Build, understand, and test native WIPI-C applications with libwipi.
---

# Native WIPI-C development, with the boundaries made explicit

`libwipi` is a clean, freestanding C SDK for native WIPI applications. It
provides version-selected public headers, carrier/OEM ABI adapters, startup and
linker support, deterministic packaging, compiled examples, and conformance
fixtures for explicitly named environments.

The currently implemented source level is **WIPI-C 1.2.1**. ARAM and WIE
results are emulator evidence for named install profiles; they are not a claim
that an unnamed Korean feature phone will accept or run the same package.

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Build an application
:link: getting-started
:link-type: doc

Copy the starter, implement the Clet lifecycle, build an ARM package, and
inspect it before loading it.
:::

:::{grid-item-card} Browse the API
:link: generated/api/1.2.1/index
:link-type: doc

Search 239 cataloged WIPI-C 1.2.1 functions with prototypes, semantic review
state, profile availability, ownership notes, and compiled example links.
:::

:::{grid-item-card} Choose a tested combination
:link: generated/support-matrix
:link-type: doc

Keep the source API level, device ABI profile, and executable/install profile
as independent choices.
:::

:::{grid-item-card} Download test fixtures
:link: generated/downloads
:link-type: doc

Release archives contain packages, sources, manifests, evidence boundaries,
and SHA-256 inventories for emulator developers and device researchers.
:::
::::

## What “supported” means here

Compatibility is a sequence of independently recorded milestones:

```text
headers -> compiles -> links -> packages -> loads -> entry -> first frame
        -> interactive -> usable -> complete -> real-device verified
```

The [support matrix](generated/support-matrix.md) reports the strongest current
result for an exact API/ABI/install combination. Public declarations can be
broader than a provider adapter, and an emulator screenshot cannot establish a
handset result.

## Paths through the documentation

- Application developer: [Getting started](getting-started.md), then the
  [compiled examples](generated/examples/index.md).
- Emulator developer: [Testing and fixture contract](testing.md), then the
  [download bundles](generated/downloads.md).
- ABI researcher: [Architecture](architecture.md), [versioning](versioning.md),
  and [provenance](provenance.md).
- 한국어 사용자: [한국어 문서 시작](ko/index.md).
- Automated tools and coding agents: [`llms.txt`](llms-source.md) plus a
  Markdown alternate for every source-backed documentation page.

```{toctree}
:hidden:
:maxdepth: 2

getting-started
api-usage
generated/api/1.2.1/index
generated/api-coverage
generated/examples/index
generated/support-matrix
testing
generated/downloads
architecture
versioning
ownership
provenance
ko/index
llms-source
```
