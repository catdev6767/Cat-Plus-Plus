/* CatOS linker script */
ENTRY(_start)

SECTIONS {
    /* GRUB load kernel tại 1MB */
    . = 1M;

    .multiboot : ALIGN(4K) {
        *(.multiboot)
    }

    .text : ALIGN(4K) {
        *(.text)
        *(.text.*)
    }

    .rodata : ALIGN(4K) {
        *(.rodata)
        *(.rodata.*)
    }

    .data : ALIGN(4K) {
        *(.data)
        *(.data.*)
    }

    .bss : ALIGN(4K) {
        *(COMMON)
        *(.bss)
        *(.bss.*)
    }
}
