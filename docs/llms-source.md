# libwipi

> A clean, freestanding SDK and evidence-indexed documentation set for native WIPI-C applications.

API level, device ABI profile, and install profile are independent. The only
implemented public catalog is WIPI-C 1.2.1. ARAM and WIE observations are
scoped emulator evidence and make no real-device claim. Preserve unknown ABI
and semantic facts as unknown.

## Start here

- [Documentation home](index.md): project scope, compatibility milestones, and reader paths.
- [Getting started](getting-started.md): copy the starter, implement Clet callbacks, build, package, and inspect.
- [API usage model](api-usage.md): understand semantic review states, profile availability, and memory IDs.
- [Architecture](architecture.md): separation of source API, device ABI adapter, and install/container profile.
- [한국어 시작 페이지](ko/index.md): Korean navigation and workflow guidance.

## API reference

- [WIPI-C 1.2.1 API index](generated/api/1.2.1/index.md): 239 versioned public rows grouped into 13 families.
- [Support matrix](generated/support-matrix.md): strongest current milestone for each exact API/ABI/install combination.
- [Ownership rules](ownership.md): memory IDs, borrowed pointers, resources, images, media clips, and shared buffers.
- [API versioning](versioning.md): implemented and planned levels without assuming an append-only 2.x surface.
- [Provenance](provenance.md): source hierarchy, confidence labels, revision pins, and clean implementation policy.

## Tests and downloads

- [Compiled example gallery](generated/examples/index.md): API use derived from checked-in sources and suite manifests.
- [Testing guide](testing.md): repository, emulator, and named-device evidence workflows.
- [Release downloads](generated/downloads.md): deterministic bundles with packages, source, manifests, evidence, and hashes.

Every source-backed documentation page publishes a nearby Markdown alternate. Subdirectory
`llms.txt` files provide smaller indexes, while `llms-full.txt` is an optional
secondary aggregate rather than the primary discovery document.
