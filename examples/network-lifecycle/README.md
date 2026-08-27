# Network Lifecycle

This WIPI-C example tests the deterministic network service lifecycle without
opening an external socket or contacting the internet. It verifies connect
callback delivery, invalid socket close handling, and service shutdown.

Controls:

- Up reconnects the modeled network service.
- OK closes an invalid socket handle and then closes the service.

Build and inspect it from the repository root:

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make -C examples/network-lifecycle clean package inspect
```

The current package target is explicitly
`1.2.1/lgt-raptor/aram-wie-raptor`. This fixture is not evidence for a carrier
network or internet endpoint.
