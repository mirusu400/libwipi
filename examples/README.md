# libwipi Examples

The examples are small, independent WIPI-C applications. They are intended for
learning one SDK area at a time and for packaging as ordinary applications.

| Example | Main SDK area | Interaction |
|---|---|---|
| `template` | Minimal lifecycle and first frame | Any key changes the accent color |
| `graphics-gallery` | Drawing primitives, colors, fonts, and text | Left and Right change pages |
| `memory-resource` | Memory IDs, pointer resolution, and package resources | OK repeats the checks |
| `audio-player` | Clip creation, data, volume, playback, stop, and cleanup | OK, directions |
| `platformer` | Timer, held input, collision, scrolling, and game state | Directions and OK |
| `conformance` | Compact multi-family conformance fixture | Automated input |

Build the three SDK-focused examples together:

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make sdk-examples
```

The applications and their package manifest live in `libwipi`. Runtime
orchestration lives in the sibling `aram-test` repository. From this workspace,
build and execute every declared case with:

```powershell
python ..\aram-test\libwipi_examples.py --build-examples --build-probe
```

The current runnable package axis is
`1.2.1/lgt-raptor/aram-wie-raptor`. An emulator pass is not a physical handset
compatibility claim.
