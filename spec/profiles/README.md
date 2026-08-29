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

`skt-samsung-sch-w830-dl21` is an exact, library-only research profile. Its
checked binding inventory contains only public table calls directly established
by SCH-W830 DL21 application code through `*0x01001000`; SPH/KTF provider-only
slots are not promoted. The profile therefore emits 69 non-variadic veneers and
links 31 local CSTDLIB symbols, while every other declared API fails at link
time. Its install profile is `none`, and its package, load, handset, and
real-device claims remain false.

The authorized SKT package corpus still establishes an SK-VM Java runtime, not
a native WIPI-C container. The recovered `MinigameQVGAOEM` EADS path remains
scoped to one embedded title; its opaque OEM services are not used by the SKT
WIPI-C profile. A handset package and `MC_GETDPTR` implementation require
additional reviewed SCH evidence.
