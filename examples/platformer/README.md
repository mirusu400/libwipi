# Sky Hopper

Sky Hopper is a small, original side-scrolling platformer example for
`1.2.1/lgt-raptor/aram-wie-raptor`. It uses only code-drawn rectangles, arcs,
lines, and text; it contains no characters, maps, images, sounds, or names from
an existing commercial game.

Controls:

- Left/Right or keypad 4/6: move;
- Up/OK or keypad 2/5: jump;
- OK after reaching the portal: restart the course.

The course demonstrates a fixed-step WIPI timer, held-key input, jumping and
platform collision, camera scrolling, collectible orbs, patrolling hazards,
lives, scoring, a goal state, and lifecycle pause/resume handling.

Build and inspect it from the repository root:

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make platformer
```

The package is written to:

```text
examples/platformer/build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/libwipi-sky-hopper.zip
```

This is an emulator example, not evidence for a physical LGT handset.

Run its automated ARAM and WIE movement/jump checks with:

```powershell
python tools/verify_aram.py --suite platformer --build-probe
python tools/verify_wie.py --suite platformer --prepare
```

The pinned artifact hash and observed frame/input results are recorded in
[`spec/evidence/platformer-example.json`](../../spec/evidence/platformer-example.json).
