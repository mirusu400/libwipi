# Ownership and memory IDs

Generated ABI veneers are call adapters. Except where an explicitly documented
ABI wrapper repacks arguments or normalizes a return value, they neither copy
application objects nor change ownership; the selected WIPI-C source contract
remains authoritative.
Any future wrapper that allocates, copies, retains, or releases an object must
add a semantic test for that transition before it is enabled for a profile.

The 1.2.1 bootstrap uses these boundaries:

| Boundary | Ownership rule |
|---|---|
| `MC_knlAlloc`, `MC_knlCalloc` | Return a memory ID owned by the caller until `MC_knlFree`; the value is not a C pointer. |
| `MC_GETDPTR` | Returns a borrowed pointer. Compaction can invalidate it, so resolve the memory ID again after any operation that may compact. |
| `MC_knlGetResource` | Writes into a caller-owned indirect buffer; it does not transfer ownership of the memory ID. |
| `MC_grpCreateImage` | Transfers the input image-data memory ID to the image provider. The provider releases it after a non-animated decode or when the animated image is destroyed. |
| `MC_mdaClipPutData` | Copies from the caller's direct buffer; the caller retains the buffer. |
| `MC_mdaClipFree` | Releases the clip and all resources allocated to it; the clip handle must not be reused. |
| KTF shared-buffer calls | The provider owns shared storage and reference tracking. `DestroySharedBuf` releases the current program's reference; application code must not free a shared pointer with `MC_knlFree`. |

The public memory-ID semantics and the image/media transfer rules come from the
pinned WIPI 1.2.1 reference revision in `spec/versions.json`. KTF shared-buffer
reference behavior is profile-specific firmware evidence and is tracked in
`spec/profiles/ktf-samsung.json`. The KTF `MC_GETDPTR` byte layout remains a
candidate profile fact. The general LGT device layout is unknown. The
`aram-wie-raptor` install profile has a narrower confirmed emulator rule in
which a memory ID resolves to the same guest address value. Application code
must still retain it as `M_MemID` and use `MC_GETDPTR`; relying on numeric
pointer equivalence would incorrectly turn an emulator observation into a
device ABI assumption.
