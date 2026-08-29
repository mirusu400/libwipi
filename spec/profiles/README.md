# ABI profile schema

Each JSON file describes one carrier/OEM/device ABI profile. It does not select
a WIPI-C source version. `api_level_mappings` records the independently reviewed
pairings and marks `target_build` true only when this repository has a usable
adapter for that exact pair.

Top-level ABI fact groups such as `layouts`, `container`, or
`known_public_methods` have a same-named entry in `fact_evidence`. That metadata
applies to every value in the group and contains:

- `profile`: the profile ID, repeated so extracted facts retain their scope;
- `confidence`: `confirmed`, `candidate`, or `unknown`;
- `source`: a privacy-safe evidence locator;
- `validation_need`: required for candidate and unknown facts.

A candidate group may be compiled into a research fixture, but it cannot
support a hardware compatibility claim by itself. A narrower install profile
may enable an emulator-only target mapping when it carries separate, pinned
black-box evidence and preserves the device claim as false. An unknown fact
must fail explicitly if code requests behavior that depends on it.

There is intentionally no `skt-*` native WIPI-C profile yet. The authorized
SKT package corpus currently establishes an SK-VM Java container/runtime, not
a native WIPI-C import ABI. The recovered SCH-W830 `MinigameQVGAOEM` EADS path
is scoped to one exact embedded title and explicitly does not generalize its
opaque OEM service slots to SKT WIPI. Creating an SKT profile requires a
reviewed native container plus public-API callsites and provider mappings.
