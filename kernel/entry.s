/* CatOS — Boot entry (assembly).
   GRUB gọi _start với magic trong eax.
   Setup stack + call kmain. */

.section .bootstrap, "ax"
.global _start
.extern kmain

_start:
    cli                    /* disable interrupts */
    mov $stack_top, %esp   /* setup stack */
    mov %esp, %ebp
    push %eax              /* multiboot magic */
    push %ebx              /* multiboot info */
    call kmain             /* never returns */
    hlt

.section .bss
.align 16
stack_bottom:
    .skip 16384            /* 16KB stack */
stack_top:
