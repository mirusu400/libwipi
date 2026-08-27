# System Services

This WIPI-C example checks program identity, monotonic time, mutable system
properties, timer definition, timer cancellation, timer delivery, and clean
application exit.

Controls:

- Any direction refreshes the current time and redraws the status.
- OK exits through `MC_knlExit` after the first interactive frame.

Build and inspect it from the repository root:

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make -C examples/system-services clean package inspect
```

The current package target is explicitly
`1.2.1/lgt-raptor/aram-wie-raptor`.
