# SCH-W8300 QPST handset probe

This is the first physical-device experiment for the owner-reported Samsung
SCH-W8300. It is intentionally small and uses only static storage plus eleven
graphics/timer calls. Its KTF adapter follows the dynamic provider path observed
in a loaded SPH-W8300 KTF client: init parameter 4 supplies the named-interface
lookup, `WIPIC_knlInterface` resolves the kernel table, and kernel slot `+0x84`
returns the master vector. It does not use the SKT SCH-W830 fixed import root.

The ABI path has live sibling-device evidence. The owner-reported model string,
firmware, install container acceptance, and lifecycle behavior are still
SCH-W8300 candidates until this exact handset is tested.

Build and inspect the candidate ZIP:

```powershell
make package inspect
```

The package is written to:

```text
build/wipi-1.2.1/ktf-samsung/
  sch-w8300-qpst-probe/010100D5.zip
```

This ZIP is pre-bound to the `010100D5` replacement slot. Extract it on the PC;
its only payload files are `__adf__` and `010100D5.jar`, and the descriptor
already contains `AID:010100D5`. Do not run WIPI Manager on it.

Before copying anything, back up the entire existing
`/brew/mod/wipiplayer/W/apps/010100D5` directory. Copy only the two extracted
payload files into that directory. Never delete or overwrite `__env__`; retain
the existing `__class__`, icon, and `P` files for this first probe. Then remove
`/brew/mod/wipiplayer/W/exe_info` as the public QPST procedure describes and
reboot the handset.

Whether this firmware can retain the slot's existing `__class__` and icon
metadata is not yet known. The SDK does not synthesize those device files from
an inferred layout. A failure to list or launch the application at this stage
is evidence that the slot metadata must be recovered, not proof that the KTF
native ABI failed.

Expected milestones, in order:

1. QPST accepts the two extracted payload files without replacing firmware or
   any file outside the backed-up `010100D5` application slot.
2. The application appears as `libwipi SCH-W8300 probe`.
3. Launch shows a blue screen with `SCH-W8300 PROBE` and `SCREEN OK`.
4. `TICK` advances once per second.
5. Key delivery remains outside this first package's claim. The recovered
   physical-client lifecycle bridge must be implemented before input is tested.

Stop after the first failed milestone and record the exact result. A package
build or successful QPST copy is not a load, entry, first-frame, timer,
interaction, or real-device compatibility result. The current firmware version
and the tested ZIP SHA-256 must be recorded before any milestone is promoted.

Use only the phone's ordinary user-application install location. Do not
overwrite firmware, boot, security, or existing system application files.
