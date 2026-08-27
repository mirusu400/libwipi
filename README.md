# libwipi

`libwipi` is a clean, freestanding C SDK for native WIPI applications. The
currently usable emulator target is WIPI-C 1.2.1 on the LGT/Raptor ABI and the
`aram-wie-raptor` install profile. It builds with an ordinary GNU Arm Embedded
toolchain and does not require a proprietary WIPI SDK.

The source API, carrier/device ABI, and executable/install profile are separate
contracts. In particular, an emulator result is not presented as a handset
result and an LGT fact is not presented as a platform-wide WIPI requirement.

## Supported now

| API / ABI / install selection | Result | Boundary |
|---|---|---|
| `1.2.1/lgt-raptor/aram-wie-raptor` | Compiles, links an ELF `binary.mod`, packages, loads, reaches entry and first frame, and passes interactive graphics, font, system, memory, timer, input, and audio checks in pinned ARAM and WIE revisions | 59 public numbered-import veneers are linkable; 24 are exercised by the conformance app; no real-device claim |
| `1.2.1/ktf-samsung/none` | Generated headers, table binder, 205 generated veneers, special timer ABI adapter, freestanding C library, relocatable example, and object-code tests | No package/install profile and no emulator or real-device runtime claim |
| WIPI-C `2.0`, `2.0.1`, `2.1.0`, or `2.2.0` | Tracked as explicit future API levels | No catalog or SDK support claim; the build rejects them |

The checked-in 239-row WIPI-C 1.2.1 catalog is the current bootstrap catalog,
not a claim that every WIPI-C API generation or every provider method is
implemented. A declared API without a proven adapter fails at link time instead
of returning fake success.

## Build and test

The reproducible path is Docker:

```powershell
docker build -t libwipi-toolchain -f docker/toolchain.Dockerfile .
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make clean all test-target
```

Build the tested conformance package explicitly:

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make API_LEVEL=1.2.1 PROFILE=lgt-raptor `
       INSTALL_PROFILE=aram-wie-raptor conformance
```

The result is:

```text
build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/examples/conformance/libwipi-conformance.zip
```

With local `arm-none-eabi-gcc`, binutils, GNU Make, and Python 3 installed, the
same `make` commands work without Docker.

## Start an application

[`examples/template`](examples/template) is a copyable application, not a
pseudocode snippet. Copy it under `examples`, change its AID/name/source list,
and build it:

```powershell
Copy-Item -Recurse examples/template examples/my-app
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make -C examples/my-app package
```

Applications outside this repository can include `mk/application.mk` and pass
`LIBWIPI_ROOT` as the path to this checkout. The shared build fragment owns the
CPU, Thumb, soft-float, freestanding, linker, CRT, and package flags, so an
application Makefile only supplies its AID, name, sources, and resources.

[`examples/platformer`](examples/platformer) is a larger original game example
with held-key movement, jumping, platform collision, scrolling, collectibles,
hazards, lives, scoring, and a goal state. Build it with `make platformer`.

See [Getting started](docs/getting-started.md) for the complete application
layout, lifecycle callbacks, resource syntax, supported method list, package
inspection, and emulator verification commands.

A separate Korean walkthrough is available in
[libwipi usage guide](docs/usage.ko.md).

## Reproduce the emulator result

After building the conformance package:

```powershell
python tools/verify_aram.py --build-probe
python tools/verify_wie.py --prepare
```

The ARAM command expects pinned `aram-core` and `aram-emu` sibling checkouts;
the WIE command can prepare its pinned public checkout in `.cache/wie`. The
recorded artifact hash, source revisions, observations, and exclusions are in
[`spec/evidence/emulator-conformance.json`](spec/evidence/emulator-conformance.json).

These gates establish the `interactive` emulator milestone. They do not
establish complete WIPI-C coverage or compatibility with a physical handset.

## Documentation map

- [Getting started](docs/getting-started.md): build a new application and run
  the conformance gates.
- [Korean usage guide](docs/usage.ko.md): build, package, run, and troubleshoot
  an application with copyable commands.
- [Architecture](docs/architecture.md): API, ABI, and install boundaries.
- [API versioning](docs/versioning.md): implemented and planned WIPI levels.
- [Ownership and memory IDs](docs/ownership.md): handle, pointer, and resource
  rules application code must preserve.
- [Provenance](docs/provenance.md): evidence hierarchy and clean-room policy.
- [Generated 1.2.1 coverage](docs/generated/api-coverage.md): catalog and KTF
  selector counts.
