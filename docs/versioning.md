# WIPI-C API versioning

`libwipi` targets the native WIPI-C application API across multiple WIPI
generations. An API level and a carrier/device ABI profile are independent:

```text
WIPI-C API level (1.2.1, 2.0, ...)
        x
carrier/OEM ABI profile (KTF/Samsung, LGT/Raptor, ...)
        -> container/install profile
```

A handset claiming WIPI 2.x does not thereby use the Samsung/KTF table ABI,
and two handsets using the same carrier ABI need not expose the same WIPI API
level.

## Version line

| API level | Standard/reference | Catalog state | SDK state |
|---|---|---|---|
| 1.2.1 | reconstructed WIPI 1.2.1 reference | checked in | headers and KTF ABI; LGT/Raptor interactive emulator target |
| 2.0 | TTAS.KO-06.0036/R3 | reference indexed | planned |
| 2.0.1 | TTAS.KO-06.0036/R4 | source acquisition needed | planned |
| 2.1.0 | TTAS.KO-06.0036/R5 | source acquisition needed | planned |
| 2.2.0 | TTAK.KO-06.0036/R6 | reference indexed | planned |

The machine-readable state is `spec/versions.json`. The current 239-row
catalog is only the 1.2.1 bootstrap catalog; it is not the complete libwipi
surface. The Wiki-derived references are pinned there to the reviewed source
revision rather than silently following future site changes.

The build selects the source level independently from the ABI and install
profiles. The three currently accepted triples are:

| API level | ABI profile | Install profile | Scope |
|---|---|---|---|
| `1.2.1` | `ktf-samsung` | `none` | Library and relocatable target evidence; no container/runtime claim |
| `1.2.1` | `lgt-raptor` | `aram-raptor` | ARAM-only synthetic SDK lab with 100 mapped APIs; no WIE or device ABI claim |
| `1.2.1` | `lgt-raptor` | `aram-wie-raptor` | ELF/package and interactive ARAM/WIE emulator verification |

For example:

```text
make API_LEVEL=1.2.1 PROFILE=lgt-raptor \
     INSTALL_PROFILE=aram-wie-raptor conformance
```

The checked-in `mk/generated/api-levels.mk` is derived from `versions.json`
and `spec/profiles/*.json`. It recognizes the full target version line but
enables only target-build triples explicitly marked available. A planned or
unknown level, a profile without an adapter, or an unsupported install pairing
fails during Make parsing.
The selected level is also passed to the compiler, where
`wipi/generated/api_levels.h` rejects absent or conflicting selection macros.

The versioned WIPI Wiki indexes 1.2.1, 2.0, and 2.2.0 separately:

- <https://mirusu400.github.io/wipi-wiki/llms.txt>
- <https://mirusu400.github.io/wipi-wiki/v20/c-api/index/>
- <https://mirusu400.github.io/wipi-wiki/v22/c-api/index/>

WIPI 2.0 adds native C families and functions including Generic I/O, terminal
resources, SMS, secure communication, mathematics, and dynamic-library
support. WIPI 2.2.0 also removes or renames parts of the 2.0 surface, so the
SDK must not model 2.x as an unconditional append-only extension.

## Implementation contract

Each implemented API level gets its own canonical catalog and generated
coverage report. A shared symbol may reuse one declaration only after its
prototype, types, constants, and semantics have been compared across every
supported level. Added, removed, renamed, and signature-changed entries remain
explicit in a generated version-delta manifest.

The public umbrella header selects an API level at build time. Requesting
an API level whose headers or selected device ABI are incomplete must fail at
compile or link time; it must never silently fall back to 1.2.1.

Adding one API level requires, in order:

1. a pinned, provenance-recorded reference corpus;
2. a complete public C catalog, types, constants, callbacks, and error values;
3. version-delta tests against the adjacent catalog;
4. ABI selector evidence for each device profile being claimed;
5. compile, link, emulator, and hardware gates labeled with both axes.
