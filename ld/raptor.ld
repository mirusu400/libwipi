OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(__text_start)

SECTIONS
{
    . = 0x00010000;
    .rodata : ALIGN(4)
    {
        *(.rodata .rodata.*)
        *(.ARM.extab .ARM.extab.*)
        __exidx_start = .;
        *(.ARM.exidx .ARM.exidx.*)
        __exidx_end = .;
    }

    . = 0x00020000;
    __text_start = .;
    .text : ALIGN(4)
    {
        KEEP(*(.text._start))
        *(.text .text.*)
        *(.glue_7 .glue_7t .v4_bx)
    }
    __text_end = .;
    /* ARAM ORs in Thumb while the pinned WIE loader adds the Thumb bit. */
    __wipi_raptor_entry_offset = _start - __text_start;

    . = 0x00030000;
    .data : ALIGN(4)
    {
        __data_start = .;
        KEEP(*(.data.wipi_clet))
        *(.data .data.*)
        __data_end = .;
    }

    .bss (NOLOAD) : ALIGN(4)
    {
        __bss_start = .;
        *(.bss .bss.* COMMON)
        __bss_end = .;
    }

    .raptor 0 : ALIGN(4)
    {
        KEEP(*(.raptor))
    }

    /DISCARD/ :
    {
        *(.comment)
        *(.note .note.*)
        *(.eh_frame .eh_frame.*)
        *(.ARM.attributes)
    }
}

ASSERT(_start >= __text_start && _start < __text_end,
       "Raptor entry must be in the executable section")
ASSERT((_start - __text_start) == 0,
       "Raptor runtime entry must be first in the executable section")
ASSERT((__data_end - __data_start) >= 0x30,
       "Raptor Clet descriptor is missing")
