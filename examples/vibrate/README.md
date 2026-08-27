# Vibration test

A minimal original WIPI-C clet for `1.2.1/lgt-raptor/aram-wie-raptor` that
exercises vibration, media mute state, and backlight control. A host gamepad
rumble motor or phone vibrator can be verified end to end. It draws only
code-drawn rectangles and text and contains no commercial assets.

Controls (host controls map to these WIPI keys):

- OK / any key: buzz at the current level for the current duration;
- Up / Down: raise or lower the level by 10 (0..100), previewing it;
- Left / Right: shorten or lengthen the pulse by 100 ms (100..2000);
- 0..9: set the level to that digit x10 (0 stops), then buzz.

Build and inspect it from the repository root:

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make -C examples/vibrate package inspect
```

The package is written to:

```text
examples/vibrate/build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/libwipi-vibrate.zip
```

Open that `.zip` in ARAM with a controller connected and press buttons to feel
the rumble. This is an emulator example, not evidence for a physical LGT handset.
