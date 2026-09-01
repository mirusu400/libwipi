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
  sch-w8300-qpst-probe/libwipi-sch-w8300-probe.zip
```

Expected milestones, in order:

1. QPST accepts the ZIP without replacing any firmware or system file.
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
