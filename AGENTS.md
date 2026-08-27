# libwipi engineering guide

## Mission

`libwipi` is a clean, freestanding SDK for building native WIPI-C applications
across the 1.2.1 and 2.x API generations. It must eventually produce packages
that run in ARAM and Wie and on explicitly tested Korean feature-phone
profiles.

The checked-in 1.2.1 implementation is a bootstrap compatibility baseline, not
the project's version ceiling. The target version line is 1.2.1, 2.0, 2.0.1,
2.1.0, and 2.2.0. Detailed reference material is currently indexed for 1.2.1,
2.0, and 2.2.0; never claim an unimplemented API level as supported.

The SDK is inspired by devkitPro's developer experience, not tied to the
devkitPro toolchain. The supported compiler contract is an ordinary GNU Arm
Embedded toolchain (`arm-none-eabi-gcc`, binutils, and `ar`). Docker is only a
reproducible way to provide that toolchain.

## Non-negotiable architecture

Keep these three layers separate:

```text
selected WIPI-C source API level
        -> carrier/OEM/device ABI adapter
        -> executable container and install profile
```

WIPI standardizes APIs and behavior but does not define one universal native
machine-code container. Never present a KTF, LGT/Raptor, Samsung, EADS, ABHS,
Wie, or ARAM detail as a platform-wide WIPI requirement.

WIPI API level and device ABI profile are independent axes. Do not infer the
carrier ABI from a WIPI version or expose newer APIs merely because a device
uses a known ABI. Do not assume that every newer API level is a strict
superset: record added, removed, renamed, and signature-changed entries.

The initial profiles are:

- `ktf-samsung`: evidence anchor for the recovered Samsung/KTF table ABI;
- `lgt-raptor`: LGT numbered-import and `binary.mod` ELF profile;
- `host-sim`: host-side semantic testing only, never a device ABI.

Profile differences belong in `spec/profiles`, `src/abi`, `crt`, `ld`, and
packaging tools. Public application code must not contain emulator checks.

## Evidence and source hierarchy

Use evidence in this order:

1. The matching version of the reconstructed WIPI specification for public
   membership, types, prototypes, and semantics. Use the versioned WIPI Wiki
   indexes for 1.2.1, 2.0, and 2.2.0 and pin the source revision used.
2. Direct firmware/application callsites and reviewed maps in sibling
   `anycall_magichole` for the exact Samsung/KTF ABI.
3. Synthetic and authorized black-box behavior in ARAM and Wie.
4. Public implementations such as `dlunch/wipi` as prior art, not authority.
5. Inference, always labeled with a confidence state and a validation need.

The sibling `anycall_magichole` repository is evidence, not product source.
Consume reviewed machine-readable facts and write original implementation.
Never copy firmware, commercial application bytes, proprietary SDK binaries,
or unlicensed implementation code into this repository.

Every ABI fact in `spec` must carry a profile and confidence. Preserve unknowns
as unknown; do not fill gaps from API order unless marked `candidate`.

## ABI hard rules

- Guest data is little-endian and uses exact 8/16/32/64-bit WIPI types.
- Device pointers and `M_Addr` are 32-bit. Target builds must assert this.
- Do not use host `long`, pointer, `size_t`, `time_t`, or structure layouts as
  evidence for a device layout.
- Do not cast provider slots directly to public prototypes when 64-bit,
  floating, variadic, or aggregate ABI rules may differ.
- The observed Samsung/KTF `MC_knlSetTimer` provider receives `tm` in `r0`, the
  timeout packed in `r1:r2`, and `parm` in `r3`. Modern AAPCS callers align the
  64-bit argument differently, so this function requires a tested veneer.
- Generate ordinary table tail veneers only for APIs whose arguments are
  32-bit words/pointers and whose selector is confirmed for that profile.
- Variadic calls require explicit handling. Do not silently forward an
  unverified `va_list` representation.
- A missing table or method must fail explicitly. Never return fake success.

All target veneer changes require an object-code/disassembly test that pins
the slot or method number and any register shuffle.

## WIPI memory model

`MC_knlAlloc` and `MC_knlCalloc` return memory IDs, not stable C pointers.
Applications obtain data pointers through `MC_GETDPTR`, and compaction can
invalidate a previously resolved pointer. Keep memory IDs and native pointers
as distinct types in implementation code.

`DECLARE_INDIRECTBUF` storage and profile-specific indirect-buffer headers
must use documented guest layouts. Emulator-specific reverse conversion hacks
must never become the default hardware ABI.

Resources, images, shared buffers, and other APIs can transfer ownership.
Document and test ownership at every wrapper boundary.

## Generated API catalog

`spec/versions.json` defines the SDK's API-version line and implementation
state. Each implemented version owns a canonical catalog such as
`spec/wipi-1.2.1/api.csv`. Generated headers and veneers must come from the
selected version catalog; do not hand-edit generated files.

The 239-row 1.2.1 catalog is the current bootstrap catalog only. It must never
be described as the complete WIPI-C surface. WIPI 2.0 and 2.2.0 require their
own catalogs, type/constant sets, and generated version-delta reports before
support can be claimed. Preserve 2.0.1 and 2.1.0 as explicit version targets
until their reference sources have been acquired and compared.

The import workflow may read the reviewed sibling map, but checked-in outputs
must make this repository build independently:

```powershell
python tools/import_anycall_catalog.py `
  --source ..\anycall_magichole\docs\maps\wipi_public_syscall_c_map.csv
python tools/generate.py
python tools/generate.py --check
```

Current 1.2.1 catalog invariants:

- exactly 239 public rows and unique ordinals 1 through 239;
- exactly 13 families;
- 229 currently confirmed Samsung/KTF selectors;
- 10 candidates, all CSTDLIB order-only rows;
- CSTDLIB is implemented locally unless a profile explicitly proves a reason
  to use its provider table.

Every additional catalog must define and test its own counts; never reuse the
1.2.1 counts as a global invariant.

## Toolchain and build rules

- Baseline CPU is ARMv4T/ARM7TDMI, little-endian, soft-float, freestanding.
- Keep compiler flags centralized in `mk/wipi.mk` and target specs/linker
  files. Examples must not invent their own ABI flags.
- API-level selection must be explicit and orthogonal to `PROFILE`. Requesting
  an unavailable API level or an unmapped API/profile pair must fail loudly.
- Compile C with warnings enabled and no hosted startup assumptions.
- Do not require devkitARM, newlib internals, Rust nightly, or a proprietary
  WIPI SDK to use the C SDK.
- Avoid C++ runtime, exceptions, RTTI, TLS, unwind tables, stack protectors,
  constructors, and hidden OS dependencies in target artifacts.
- Packaging must be deterministic and reject unsafe archive paths.

## Required development loop

Before changing behavior:

1. Inspect `git status --short` and preserve unrelated work.
2. Add or strengthen the smallest catalog, layout, ABI, package, or semantic
   test that describes the change.
3. Implement the change in its owning layer.
4. Regenerate checked-in artifacts.
5. Run the focused test, then all repository gates.
6. Inspect generated diffs and target disassembly.

Repository gates, in order:

```powershell
python tools/generate.py --check
python -m unittest discover -s tests -p "test_*.py"
docker build -t libwipi-toolchain -f docker/toolchain.Dockerfile .
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain make clean all test-target
git diff --check
```

If Docker is unavailable, run the same `make` targets with a local
`arm-none-eabi-*` toolchain and report the Docker gate as unverified.

Emulator and hardware gates are additive:

- package inspection/round-trip;
- synthetic ABI probes in ARAM and Wie;
- lifecycle, framebuffer, input, timer, resource, storage, and audio examples;
- actual device tests for a named carrier/OEM/model/firmware/install path.

## Compatibility claims

Keep these milestones distinct:

```text
headers -> compiles -> links -> packages -> loads -> entry -> first frame
        -> interactive -> playable/usable -> complete -> real-device verified
```

An ARAM `ok_frame` or a Wie screenshot does not prove full application or
hardware compatibility. A real-device claim must name the exact profile and
firmware and record the tested package hash.

## Repository ownership

`libwipi` owns public headers, target runtime/ABI veneers, CRT/linker scripts,
packagers, examples, and SDK conformance fixtures. Emulator service semantics
remain owned by `aram-core`; compatibility orchestration remains owned by
`aram-test`. Fix behavior in the owning repository rather than duplicating an
emulator implementation here.
