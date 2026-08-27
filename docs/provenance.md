# Provenance and clean implementation policy

The current public API inventory is the WIPI 1.2.1 bootstrap catalog. It is not
the complete libwipi version scope. Versioned WIPI Wiki references for 1.2.1,
2.0, and 2.2.0 are recorded in `spec/versions.json`; intermediate 2.0.1 and
2.1.0 sources remain acquisition tasks.
Samsung/KTF selector facts are imported mechanically from reviewed maps in the
local `anycall_magichole` evidence repository. ARAM and WIE are used for
synthetic and authorized black-box validation. The implemented
`aram-wie-raptor` install profile pins both emulator revisions, while the
profile-wide LGT/device facts retain their independent candidate or unknown
confidence states.

The `aram-raptor` profile is a separate synthetic emulator contract. Its FS,
DB, and MDA import numbers are derived from the pinned 1.2.1 catalog only
inside the reserved ARAM lab range. They are not evidence for Wie, an LGT
provider, or a physical device.

Each profile manifest has a `fact_evidence` entry for every ABI fact group.
The entry repeats the profile, records `confirmed`, `candidate`, or `unknown`,
names a privacy-safe source locator, and states the validation need for every
non-confirmed group. API/profile availability is a separate implementation
mapping and is never inferred from those confidence labels.

No firmware, commercial application, proprietary WIPI SDK binary, extracted
asset, signing key, or private corpus byte belongs in this repository.

The reproducible emulator result is recorded in
`spec/evidence/emulator-conformance.json`. It binds a deterministic package
hash to the source/API/ABI/install axes, emulator revisions, observed API count,
frame/input/audio diagnostics, exclusions, and an explicit `real_device=false`
claim. `tools/verify_aram.py` and `tools/verify_wie.py` re-check revisions before
running that package.

The ARAM-only 100-method lab is recorded separately in
`spec/evidence/aram-sdk-lab.json`. Its two restart checks use isolated temporary
state roots and contain no user save paths or private input data.

Public prior art may inform architecture, but implementation copied from a
third-party repository must be license-compatible and attributed explicitly.
The initial implementation is written for this repository from documented
interfaces and factual maps.
