# Testing libwipi applications and provider implementations

The downloadable fixtures are intended for two related jobs: application
developers can check that their toolchain emits a valid package, while emulator
or device-profile developers can measure lifecycle and API behavior against a
known source fixture.

## Repository gates

Run generation and host tests first:

```powershell
python tools/generate.py --check
python tools/generate_docs.py --check
python -m unittest discover -s tests -p "test_*.py"
```

Then use the pinned GNU Arm environment for object-code and package gates:

```powershell
docker build -t libwipi-toolchain -f docker/toolchain.Dockerfile .
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make clean all test-target
```

These tests pin generated selectors, the special 64-bit timer register
shuffle, ELF structure, deterministic archive paths, and the external-style
application build. Passing them establishes neither emulator behavior nor
hardware compatibility.

## Emulator integration

Use [the release bundles](generated/downloads.md) rather than copying an
unlabeled `binary.mod`. Each bundle carries:

- packages for one API/ABI/install triple;
- original fixture source and resources;
- the suite manifest and expected observations;
- evidence and revision pins;
- a machine-readable bundle manifest and SHA-256 inventory.

The conformance fixture covers the common pinned ARAM/WIE contract. The common
SDK lab splits behavior into seven applications, and the ARAM-only lab adds
storage and expanded media behavior under an explicitly synthetic import
range. Compatibility orchestration remains owned by `aram-test`; libwipi owns
the source fixtures and fixture-specific verifiers.

## Feature-phone research

A device run should be recorded as a new, exact result. At minimum preserve
the carrier, OEM, model, firmware, install path, package SHA-256, API level,
device ABI profile, observed milestone, and failures. Do not translate an ARAM
or WIE result into a device claim, and do not infer a device ABI solely from
the WIPI version printed by a handset.

The current KTF/Samsung profile has target library and disassembly evidence but
no checked-in executable/install profile. Therefore the release workflow does
not manufacture a KTF handset package.
