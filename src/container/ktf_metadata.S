.syntax unified
.cpu arm7tdmi
.thumb

.section .text._start, "ax", %progbits
.align 1
.global _start
.type _start, %function
.thumb_func
_start:
    ldr r1, =__bss_start
    ldr r2, =__bss_end
    movs r3, #0
1:
    cmp r1, r2
    bhs 2f
    str r3, [r1]
    adds r1, #4
    b 1b
2:
    ldr r0, =__wipi_ktf_wipi_exe
    bx lr
.size _start, .-_start
.pool

.section .rodata.ktf_metadata, "a", %progbits
.balign 4

.global __wipi_ktf_wipi_exe
.type __wipi_ktf_wipi_exe, %object
__wipi_ktf_wipi_exe:
    .long __wipi_ktf_exe_interface
    .long __wipi_ktf_executable_name
#if defined(LIBWIPI_INSTALL_SCH_W8300_QPST_PROBE)
    .long 1
    .long 0
    .long __wipi_ktf_executable_init
    .long __wipi_ktf_executable_init
    .long 0
    .long 0
    .long __wipi_ktf_executable_fini
    .long 0
#else
    .long 0
    .long 0
    .long 0
    .long __wipi_ktf_executable_init
    .long 0
    .long 0
    .long 0
    .long 0
#endif
.size __wipi_ktf_wipi_exe, .-__wipi_ktf_wipi_exe

.type __wipi_ktf_exe_interface, %object
__wipi_ktf_exe_interface:
    .long __wipi_ktf_exe_functions
    .long __wipi_ktf_executable_name
#if defined(LIBWIPI_INSTALL_SCH_W8300_QPST_PROBE)
    .long 1
#else
    .long 0
#endif
    .long 0
    .long 0
    .long 0
    .long 0
    .long 0
.size __wipi_ktf_exe_interface, .-__wipi_ktf_exe_interface

.type __wipi_ktf_exe_functions, %object
__wipi_ktf_exe_functions:
    .long 0
    .long 0
    .long __wipi_ktf_interface_init
#if defined(LIBWIPI_INSTALL_SCH_W8300_QPST_PROBE)
    .long __wipi_ktf_get_state
    .long __wipi_ktf_set_state
    .long __wipi_ktf_get_class
    .long __wipi_ktf_contains_address
#else
    .long 0
    .long __wipi_ktf_get_class
    .long 0
    .long 0
#endif
.size __wipi_ktf_exe_functions, .-__wipi_ktf_exe_functions

.global __wipi_ktf_main_class
.type __wipi_ktf_main_class, %object
__wipi_ktf_main_class:
    .long __wipi_ktf_main_class + 4
    .long 0
    .long __wipi_ktf_class_descriptor
    .long __wipi_ktf_class_vtable
    .long 0x00080000
.size __wipi_ktf_main_class, .-__wipi_ktf_main_class

.type __wipi_ktf_class_descriptor, %object
__wipi_ktf_class_descriptor:
    .long __wipi_ktf_class_name
    .long 0
    .long 0
    .long __wipi_ktf_class_methods
    .long 0
    .long 0
    .long 2
    .long 0x21
    .long 0
.size __wipi_ktf_class_descriptor, .-__wipi_ktf_class_descriptor

.type __wipi_ktf_class_methods, %object
__wipi_ktf_class_methods:
    .long __wipi_ktf_constructor_method
    .long __wipi_ktf_start_method
.size __wipi_ktf_class_methods, .-__wipi_ktf_class_methods

.type __wipi_ktf_class_vtable, %object
__wipi_ktf_class_vtable:
    .long __wipi_ktf_constructor_method
    .long __wipi_ktf_start_method
.size __wipi_ktf_class_vtable, .-__wipi_ktf_class_vtable

.type __wipi_ktf_constructor_method, %object
__wipi_ktf_constructor_method:
    .long __wipi_ktf_java_constructor
    .long __wipi_ktf_main_class
    .long 0
    .long __wipi_ktf_constructor_name
    .long 0
    .long 0x00010000
    .long 0
.size __wipi_ktf_constructor_method, .-__wipi_ktf_constructor_method

.type __wipi_ktf_start_method, %object
__wipi_ktf_start_method:
    .long __wipi_ktf_java_start_app
    .long __wipi_ktf_main_class
    .long 0
    .long __wipi_ktf_start_name
    .long 0
    .long 0x00010001
    .long 0
.size __wipi_ktf_start_method, .-__wipi_ktf_start_method

.type __wipi_ktf_executable_name, %object
__wipi_ktf_executable_name:
#if defined(LIBWIPI_INSTALL_SCH_W8300_QPST_PROBE)
    .asciz "libwipi SCH-W8300 probe"
#else
    .asciz "libwipi KTF executable"
#endif

.type __wipi_ktf_class_name, %object
__wipi_ktf_class_name:
    .asciz "LibwipiClet"

.type __wipi_ktf_constructor_name, %object
__wipi_ktf_constructor_name:
    .byte 0
    .asciz "()V+<init>"

.type __wipi_ktf_start_name, %object
__wipi_ktf_start_name:
    .byte 0
    .asciz "([Ljava/lang/String;)V+startApp"
