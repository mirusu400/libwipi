# libwipi Examples

The examples are small, independent WIPI-C applications. They are intended for
learning one SDK area at a time and for packaging as ordinary applications.

| Example | Main SDK area | Interaction |
|---|---|---|
| `template` | Minimal lifecycle and first frame | Any key changes the accent color |
| `graphics-gallery` | Drawing primitives, colors, fonts, and text | Left and Right change pages |
| `memory-resource` | Memory IDs, pointer resolution, and package resources | OK repeats the checks |
| `audio-player` | Clip creation, data, volume, playback, stop, and cleanup | OK, directions |
| `vibrate` | Vibration strength and duration with host haptics | OK, directions, digits |
| `system-services` | Identity, properties, time, timers, and exit | Directions and OK |
| `image-pipeline` | Images, offscreen buffers, RGB transfer, copy, and repaint | Any key rebuilds |
| `network-lifecycle` | Deterministic connect, callback, close, and error path | Up and OK |
| `database-crud` | All 13 database APIs and restart-persistent records | OK redraws the result |
| `filesystem` | All 17 filesystem APIs and restart-persistent files | OK redraws the result |
| `media-suite` | All 21 media APIs, PCM output, recording boundary, and haptics | OK toggles playback |
| `platformer` | Timer, held input, collision, scrolling, and game state | Directions and OK |
| `conformance` | Compact multi-family conformance fixture | Automated input |

Build the SDK-focused examples together:

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make sdk-examples
```

Build all ten examples for the ARAM-only 100-API contract:

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make aram-sdk-examples
```

The applications and their package manifest live in `libwipi`. Runtime
orchestration lives in the sibling `aram-test` repository. From this workspace,
build and execute every declared case with:

```powershell
python ..\aram-test\libwipi_examples.py --build-examples --build-probe
```

The current runnable package axis is
`1.2.1/lgt-raptor/aram-wie-raptor` for the shared subset and
`1.2.1/lgt-raptor/aram-raptor` for ARAM-only extended tests. An emulator pass
is not a physical handset compatibility claim.
