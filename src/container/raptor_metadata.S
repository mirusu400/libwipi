.syntax unified
.cpu arm7tdmi

.section .raptor, "", %progbits
.balign 4
.global __wipi_raptor_metadata
.type __wipi_raptor_metadata, %object
__wipi_raptor_metadata:
    .ascii "RAPT"
    .long 0x20050512
    .long 1f - __wipi_raptor_metadata
    .long __wipi_raptor_entry_offset
    .long 0
    .long 0
    .long 0x00010001
    .long 1
    .long 0
    .long 2f - __wipi_raptor_metadata
    .long 0
    .long 3f - __wipi_raptor_metadata
2:
    .asciz "libwipi"
3:
    .asciz "kernel dlet wipic"
1:
.size __wipi_raptor_metadata, .-__wipi_raptor_metadata
