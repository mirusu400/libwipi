# Install profiles

An install profile binds one source API level and one ABI adapter to a specific
container, loader, import, entry, and installation contract. It must not be
used to infer facts about every device that shares the ABI profile.

`aram-wie-raptor.json` is the implemented WIPI-C 1.2.1 emulator contract. It
records the LGT/Raptor ELF and package layout, pinned ARAM and WIE revisions,
their environment-specific method/return differences, the install-scoped
memory rule, and the exact conformance evidence file. Its package and
interactive emulator claims are true; its real-device claim is false.

`aram-ktf.json` records the observed KTF distribution ZIP shape and ARAM's
raw-image bootstrap contract for the `ktf-samsung` ABI. The libwipi MClass
wrapper is explicitly emulator-scoped: the ZIP has the carrier archive shape,
but no real handset/model/firmware installation claim is made.
