# Getting started with a WIPI-C application

This guide uses the WIPI-C 1.2.1 install target shared by the pinned ARAM and
WIE test paths:

```text
API_LEVEL=1.2.1
PROFILE=lgt-raptor
INSTALL_PROFILE=aram-wie-raptor
```

That triple is the default, portable emulator contract. The separately tested
`1.2.1/lgt-raptor/aram-raptor` contract adds synthetic ARAM-only methods for SDK
testing. Neither is a generic LGT handset package or a real-device compatibility
claim.

## Prerequisites

Use either:

- Docker, which supplies the exact GNU Arm Embedded build environment; or
- GNU Make, Python 3, `arm-none-eabi-gcc`, binutils, and `ar` locally.

Python unit tests do not replace target tests: target disassembly, ELF layout,
and package inspection require the Arm tools.

## 1. Verify the SDK checkout

From the repository root:

```powershell
python tools/generate.py --check
python -m unittest discover -s tests -p "test_*.py"
docker build -t libwipi-toolchain -f docker/toolchain.Dockerfile .
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make clean all test-target
```

The last command builds both current ABI adapters, checks the generated ARM
object code, validates ELF/package structure, and builds the external-style
starter application.

## 2. Copy the starter

The shortest supported setup is:

```powershell
Copy-Item -Recurse examples/template examples/my-app
```

Its Makefile contains only application-owned settings:

```make
LIBWIPI_ROOT ?= ../..

APP_AID := my-wipi-app
APP_NAME := My WIPI application
APP_SOURCES := main.c
# APP_RESOURCES := assets/title.bin=res/title.bin

include $(LIBWIPI_ROOT)/mk/application.mk
```

`APP_AID` is also the package filename stem. Every resource uses
`SOURCE=ARCHIVE_PATH`; archive paths are validated and sorted for deterministic
packaging. Add several mappings separated by spaces.

For an application outside the checkout, point `LIBWIPI_ROOT` at this
repository either in its Makefile or on the Make command line:

```text
make LIBWIPI_ROOT=C:/path/to/libwipi package
```

Do not copy target flags from the SDK into the application. The included build
fragment selects ARM7TDMI, ARMv4T Thumb, little-endian soft-float, the CRT,
linker script, library, and packager as one reviewed contract.

## 3. Implement the lifecycle

Include the umbrella header:

```c
#include <wipi/wipi.h>
```

An application supplies these six callbacks with exactly the declared
signatures:

```c
void startClet(M_Int32 argc, M_Char *argv[]);
void destroyClet(void);
void pauseClet(void);
void resumeClet(void);
void paintClet(M_Int32 x, M_Int32 y, M_Int32 width, M_Int32 height);
void handleCletEvent(M_Int32 type, M_Int32 param1, M_Int32 param2);
```

[`examples/template/main.c`](../examples/template/main.c) provides a minimal
screen, font, repaint, and key-input example. The more extensive
[`examples/conformance/main.c`](../examples/conformance/main.c) demonstrates
memory IDs, a timer callback, system properties, graphics, font rendering,
input, and a generated SMAF audio clip.

[`examples/platformer/main.c`](../examples/platformer/main.c) is an original
side-scrolling game example. It demonstrates fixed-step timers, normalized
`WIPI_CLET_KEY_*` input, held buttons, jump/platform collision, camera
scrolling, collectibles, hazards, score/lives, and a win/restart state without
external assets. Build it with `make platformer`; its README includes automated
ARAM and WIE movement/jump checks.

Use the pinned WIPI 1.2.1 reference in `spec/versions.json` for public behavior,
types, and ownership. Use `include/wipi` for the declarations this checkout
actually exposes. The list of 59 linkable Raptor methods is
`imports.confirmed_public_methods` in
[`spec/install/aram-wie-raptor.json`](../spec/install/aram-wie-raptor.json).
Headers contain the broader bootstrap catalog, so declaration alone does not
promise a provider veneer; use of an unmapped method deliberately produces a
link error.

For ARAM-only SDK development, select `aram-raptor`. It exposes 100 methods:
the common graphics, kernel, network, and misc subset plus all 17 filesystem,
13 database, and 21 media APIs. The extra method numbers are a synthetic ARAM
test contract, not a device ABI. The independent examples are
[`database-crud`](generated/examples/database-crud.md),
[`filesystem`](generated/examples/filesystem.md), and
[`media-suite`](generated/examples/media-suite.md).

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make aram-sdk-examples
python ..\aram-test\libwipi_examples.py `
  --manifest examples\sdk-lab-aram.json --build-probe `
  --output ..\aram-test\build\libwipi-examples-aram
```

Memory allocation returns `M_MemID`, not a stable C pointer. Retain the ID and
call `MC_GETDPTR(id)` whenever a pointer is needed. Do not retain a resolved
pointer across an operation that can compact provider memory. In this emulator
install profile the numeric ID currently resolves as a direct guest address,
but that fact must not be used as a device ABI assumption.

## 4. Build and inspect the package

For an in-repository application:

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make -C examples/my-app clean package inspect
```

The package appears under:

```text
examples/my-app/build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/<APP_AID>.zip
```

`inspect` verifies the nested archive, metadata, `binary.mod`, duplicate names,
unsafe paths, and resources. Rebuilding identical inputs produces identical
package bytes.

If setting the axes manually, always name all three:

```text
make API_LEVEL=1.2.1 PROFILE=lgt-raptor \
     INSTALL_PROFILE=aram-wie-raptor conformance
```

Unknown and unavailable combinations fail during Make parsing; they never
fall back to another WIPI level or ABI.

## 5. Run the conformance application

Build the repository's instrumented application first:

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make API_LEVEL=1.2.1 PROFILE=lgt-raptor `
       INSTALL_PROFILE=aram-wie-raptor conformance
```

### ARAM

Place `aram-core` and `aram-emu` beside this checkout at the revisions recorded
in the install manifest, then run:

```powershell
python tools/verify_aram.py --build-probe
```

The verifier checks both revisions before building the probe. It requires an
interactive frame, Thumb entry, at least 24 observed public APIs, key press and
release, multiple frame changes, zero unimplemented calls, and continuous
44.1-kHz stereo audio without reported loss or overlap.

### WIE

With Git, Cargo, and the Rust toolchain available:

```powershell
python tools/verify_wie.py --prepare
```

`--prepare` clones and checks out the pinned WIE revision when `.cache/wie` is
absent. The verifier temporarily installs the checked-in Rust harness, runs the
package, injects an OK key, checks distinct frames and audio events, and removes
the temporary harness even on failure.

Both verifier scripts are specific to the conformance application. A custom
application can use the produced Raptor package with the corresponding
emulator, but it should define its own observable assertions instead of
pretending to pass the conformance dashboard.

The exact recorded run is
[`spec/evidence/emulator-conformance.json`](../spec/evidence/emulator-conformance.json).
The test intentionally excludes storage, backlight, vibration, and font
metrics because the two pinned runtimes do not yet share proven selectors or
semantics for those operations; see
[`examples/conformance/coverage.json`](../examples/conformance/coverage.json).

## Current completion boundary

For `1.2.1/lgt-raptor/aram-wie-raptor`, the demonstrated milestone is:

```text
headers -> compiles -> links -> packages -> loads -> entry -> first frame
        -> interactive graphics/input/timer/audio
```

It is not yet `complete` WIPI-C coverage and it is not `real-device verified`.
A handset claim must name a carrier, OEM, model, firmware, install path, and
tested package hash.
