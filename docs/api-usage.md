# Reading and using the API reference

The API portal joins three kinds of information without collapsing them into
one compatibility claim:

1. the versioned public WIPI-C catalog supplies membership and prototypes;
2. reviewed semantic notes explain parameters, results, and ownership; and
3. profile/install manifests say whether libwipi can currently adapt the call
   for a particular target.

Start at the [WIPI-C 1.2.1 family index](generated/api/1.2.1/index.md), or use
the site search for a function such as
[`MC_knlAlloc`](generated/api/1.2.1/symbols/MC_knlAlloc.md).

## Documentation states

Each function page labels its semantic documentation as `reviewed`, `draft`,
or `cataloged`. `Cataloged` means the versioned reference establishes the
function name and prototype, while detailed behavior has deliberately not been
filled in from guesswork. The profile table is a separate statement about the
SDK implementation.

Likewise, a `confirmed`, `candidate`, or `unknown` Samsung/KTF selector is ABI
evidence for that profile only. It does not change WIPI-standard behavior and
does not establish an LGT, ARAM, WIE, or handset selector.

## The memory-ID pattern

WIPI allocation returns a memory ID rather than a stable C pointer:

```c
M_MemID storage = MC_knlAlloc(256);
M_Byte *bytes = (M_Byte *)MC_GETDPTR(storage);

if (bytes != M_NULL) {
    bytes[0] = 0;
}

MC_knlFree(storage);
```

Retain `storage`, not `bytes`, across operations that may compact provider
memory. Resolve the ID again before later access. See
[Ownership and memory IDs](ownership.md) for transfer and borrowing rules.

## Checked examples are part of the guide

The [example gallery](generated/examples/index.md) is generated from checked-in
C sources and suite manifests. A function page links back to every detected
compiled example that uses it. Those links establish build coverage and, when
the named evidence says so, scoped emulator observations. They do not silently
promote an example to real-device verification.
