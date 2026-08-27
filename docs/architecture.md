# Architecture

## Compatibility layers

`libwipi` treats compatibility as three independent contracts:

1. **Source API**: the selected WIPI-C version's names, prototypes, constants,
   callbacks, and ownership semantics.
2. **Binary ABI**: function discovery, table slots or method IDs, calling
   convention, guest layouts, and memory-ID representation.
3. **Container/install**: entry/bootstrap metadata, relocations, archive
   layout, signing/DRM, and device installation policy.

An API can be source-compatible while its selector or container remains
unknown. The catalog therefore records confidence per target profile instead
of pretending that one result applies to every WIPI implementation.

API version is independent of ABI profile. The initial 1.2.1 catalog is the
implemented compatibility base; 2.0 through 2.2.0 are explicit targets tracked
in `spec/versions.json`. See `docs/versioning.md` for the version matrix.
Profile manifests contain explicit `api_level_mappings`; they do not select an
API level themselves. `tools/generate.py` turns the version line and available
target-build pairs into the checked-in Make include and API-level header.

## Current profiles

### `ktf-samsung`

This profile is based on direct Samsung firmware and application evidence. It
uses interface tables, with kernel/graphics/filesystem/network/utility and
several provider tables recovered independently. The public table surface has
229 confirmed selectors. Ten CSTDLIB slots remain order-only candidates and
are not called by this SDK.

The profile's shared-buffer kernel order is:

```text
+0x3c Create
+0x40 Get
+0x44 GetSize
+0x48 Resize
+0x4c Destroy
```

This differs from some emulator-era public implementations and is pinned by
tests.

At runtime, `wipi_ktf_bind_default_imports()` reads the process-import pointer
at `0x01001000`, binds the directly exposed tables, and invokes the confirmed
kernel `+0x84` getter for the 17-entry non-kernel master vector. This is an
in-process table binder; it is not yet a carrier package loader or CRT.
Binding rejects null tables before changing state. A partial process root or
master vector therefore returns `M_E_ERROR` instead of reporting success.

### `lgt-raptor`

LGT uses an ELF32 ARM `binary.mod` and numbered imports from module `0x1fb`.
Known method IDs are recorded separately from the WIPI public ordinal because
the two numbers are unrelated. The device-wide facts in
`spec/profiles/lgt-raptor.json` remain candidates until an authorized module or
handset confirms them.

The narrower `aram-wie-raptor` install profile is implemented and independently
confirmed against pinned emulator revisions. Its target build provides:

- an ELF entry/bootstrap and 12-word Clet descriptor;
- 59 generated numbered-import veneers from module `0x1fb`;
- a `.raptor` metadata section required by the current ARAM loader;
- deterministic outer ZIP and inner JAR packaging; and
- install-scoped adapter differences between ARAM and WIE.

The ELF header holds an aligned entry address. ARAM selects Thumb with
`entry | 1`, while WIE invokes `entry + 1`; callback pointers in the descriptor
are Thumb pointers. The third entry argument distinguishes the two pinned
loader environments inside the ABI adapter. Six graphics method IDs and the
WIE display-info success value are selected or normalized there, never in
public application code.

Input follows the same rule. ARAM already delivers the signed WIPI direction
and select values, while the pinned WIE bridge delivers MIDP values. The LGT
callback adapter normalizes the latter to `WIPI_CLET_KEY_*` before application
dispatch, allowing held-key game code to remain profile-independent.

The conformance application has crossed the package, load, entry, first-frame,
and interactive milestones on both emulators. This does not promote the
install-scoped evidence into a general LGT device ABI claim.

### `host-sim`

The simulator profile is for fast semantics and ownership tests. Host
pointers and host standard-library types never cross into target ABI facts.

## Calling convention boundary

Most table functions consist only of 32-bit words and pointers. A Thumb tail
veneer can resolve the selected table slot and branch without disturbing the
caller's arguments.

The important first exception is:

```c
M_Int32 MC_knlSetTimer(MCTimer *tm, M_Int64 timeout, void *parm);
```

AAPCS aligns the timeout to `r2:r3` and places `parm` on the stack. The observed
Samsung/KTF provider expects `r0`, `r1:r2`, and `r3`, respectively. Both target
adapters use a tested shuffle before resolving and tail-branching to their
provider; object-code tests pin the register moves, selector or method number,
and ARMv4T-compatible branch sequence. The LGT form is also exercised by the
timer portion of the ARAM and WIE conformance app.

## Generated files

The currently implemented catalog is `spec/wipi-1.2.1/api.csv`.
`tools/generate.py` owns its bootstrap outputs:

- `include/wipi/generated/*.h`;
- `mk/generated/api-levels.mk`;
- `src/abi/ktf/generated_veneer.S`;
- `src/abi/lgt/generated_veneer.S`;
- `docs/generated/api-coverage.md`.

Generated files begin with a warning and must never be edited by hand.

## Deliberate bootstrap limits

`MC_knlPrintk`, `MC_knlSprintk`, and `MC_knlExecute` remain declared but are
not defined by the target archive. Their variadic provider convention has not
been validated, so an application using one gets an explicit link failure.
Missing or null confirmed table slots increment `wipi_missing_import_count`,
optionally call the installed diagnostic hook, and return an all-bits-set
failure value.

The KTF `MC_GETDPTR` helper implements the recorded dynamic
handle-to-head-to-payload model, but that profile fact remains a candidate
pending a direct callsite or named-device probe. A general LGT device
memory-ID layout remains unknown. Only `aram-wie-raptor` resolves its emulator
memory IDs as direct guest addresses; that rule is compile-time scoped to the
install profile and is not a hardware default. Static indirect-buffer
declaration macros are absent until their header contents are proven.

Ownership behavior is not changed by a tail veneer. The source-standard rules
and the additional constraints for memory IDs, images, media clips, resources,
and shared buffers are recorded in `docs/ownership.md`.

The source-facing Clet callbacks use the full classic signatures
`startClet(argc, argv)` and `paintClet(x, y, width, height)`. Loaders that pass
no startup arguments naturally supply zero/null values; applications may
ignore repaint bounds. `CletHandleEvent` is accepted as a source alias for the
more commonly exported `handleCletEvent` spelling.
