# Filesystem

This original WIPI-C clet exercises all 17 `MC_fs*` APIs through the
`1.2.1/lgt-raptor/aram-raptor` synthetic emulator contract.

It creates a private directory and file, writes and reads an exact marker,
checks seek and tell positions, inspects attributes and directory listings,
renames the file in both directions, and removes temporary files and
directories. The marker file remains after shutdown. On the second isolated
launch the clet must read that marker before it reports `RESTART FILE PASS`.

Build with:

```sh
make -C examples/filesystem package inspect
```

This profile proves ARAM emulator behavior only. It does not claim a handset
filesystem ABI.
