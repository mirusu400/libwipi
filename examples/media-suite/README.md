# Media suite

This original WIPI-C clet exercises all 21 `MC_mda*` APIs through the
`1.2.1/lgt-raptor/aram-raptor` synthetic emulator contract.

One data clip checks buffer and package-file transfer, type reporting,
available size, data extraction, clearing, seeking, recording state, per-clip
volume, and clip release. A second clip plays an original two-note SMAF and
checks play, pause, resume, and stop. The clet also verifies global volume,
mute state, and vibration.

Build with:

```sh
make -C examples/media-suite package inspect
```

ARAM records decoder-backed PCM and haptics telemetry for this example. The
record call is a modeled service boundary and does not open a host microphone.
