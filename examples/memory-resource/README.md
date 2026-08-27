# Memory and Resource

This example separates WIPI memory IDs from resolved data pointers and tests a
small packaged resource. It demonstrates `MC_knlAlloc`, `MC_knlCalloc`,
`MC_GETDPTR`, `MC_knlFree`, memory statistics, resource lookup, and resource
copying.

The resource buffer is resolved only while its memory ID is valid. The example
copies display text into static storage before freeing the ID, so it never
keeps a stale pointer after compaction or release.

Press OK to run the checks again. The app exits with a failure code if a
required check fails.

Build and inspect the package from the repository root:

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make -C examples/memory-resource clean package inspect
```

The current package target is explicitly
`1.2.1/lgt-raptor/aram-wie-raptor`.
