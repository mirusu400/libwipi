OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(_start)

SECTIONS
{
    . = 0x00100000;
    .text : ALIGN(4)
    {
        KEEP(*(.text._start))
        *(.text .text.*)
        *(.glue_7 .glue_7t .v4_bx)
    }

    .rodata : ALIGN(4)
    {
        KEEP(*(.rodata.ktf_metadata))
        *(.rodata .rodata.*)
        *(.ARM.extab .ARM.extab.*)
        __exidx_start = .;
        *(.ARM.exidx .ARM.exidx.*)
        __exidx_end = .;
    }

    .data : ALIGN(4)
    {
        *(.data .data.*)
        *(.got .got.*)
        . = ALIGN(8);
        LONG(0)
        LONG(0)
        __image_end = .;
    }

    .bss (NOLOAD) : ALIGN(8)
    {
        __bss_start = .;
        *(.bss .bss.*)
        *(COMMON)
        . = ALIGN(8);
        __bss_end = .;
    }
    __wipi_bss_size = __bss_end - __bss_start;

    /DISCARD/ :
    {
        *(.comment)
        *(.note .note.*)
        *(.eh_frame .eh_frame.*)
    }
}

ASSERT(_start == 0x00100000, "KTF bootstrap must be the first Thumb procedure")
ASSERT(__bss_start == __image_end, "KTF BSS must immediately follow the raw image")
