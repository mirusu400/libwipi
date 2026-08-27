# Synthetic Audio Player

This standalone WIPI-C example creates a media clip, supplies an original
two-note SMAF byte sequence, changes clip volume, plays and stops the clip, and
releases ownership during Clet destruction.

Controls:

- OK or Right: restart playback
- Left: stop playback
- Up and Down: change volume

The tone is synthetic and is included directly in the source. It contains no
commercial music or extracted application data.

Build and inspect the package from the repository root:

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make -C examples/audio-player clean package inspect
```

The current package target is explicitly
`1.2.1/lgt-raptor/aram-wie-raptor`.
