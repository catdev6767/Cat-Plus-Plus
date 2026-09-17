/* FelisOS — IRQ stubs (assembly) */

.section .text

.global idt_load
idt_load:
    mov 4(%esp), %eax
    lidt (%eax)
    ret

.global irq1_stub
.extern keyboard_handler
irq1_stub:
    pusha
    call keyboard_handler
    mov $0x20, %al
    outb %al, $0x20
    popa
    iret


/* IRQ12 — mouse */
.global irq12_stub
.extern mouse_handler
irq12_stub:
    pusha
    call mouse_handler
    mov $0x20, %al
    outb %al, $0xA0
    outb %al, $0x20
    popa
    iret
