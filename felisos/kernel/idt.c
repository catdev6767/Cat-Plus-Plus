/* FelisOS — IDT + IRQ setup */
#include <stdint.h>

struct idt_entry {
    uint16_t base_lo;
    uint16_t sel;
    uint8_t always0;
    uint8_t flags;
    uint16_t base_hi;
} __attribute__((packed));

struct idt_ptr {
    uint16_t limit;
    uint32_t base;
} __attribute__((packed));

struct idt_entry idt[256];
struct idt_ptr idtp;

extern void idt_load(uint32_t idtp_addr);
extern void irq1_stub(void);
extern void irq12_stub(void);

static inline void outb(uint16_t port, uint8_t val) {
    __asm__ volatile("outb %0, %1" : : "a"(val), "Nd"(port));
}

void idt_set_gate(uint8_t num, uint32_t base, uint16_t sel, uint8_t flags) {
    idt[num].base_lo = base & 0xFFFF;
    idt[num].base_hi = (base >> 16) & 0xFFFF;
    idt[num].sel = sel;
    idt[num].always0 = 0;
    idt[num].flags = flags;
}

void idt_init(void) {
    idtp.limit = sizeof(struct idt_entry) * 256 - 1;
    idtp.base = (uint32_t)&idt;

    uint8_t* p = (uint8_t*)&idt;
    for (unsigned i = 0; i < sizeof(idt); i++) p[i] = 0;

    /* IRQ1 = keyboard → interrupt 33 (32 + 1) */
    uint16_t cs_val;
    __asm__ volatile("mov %%cs, %0" : "=r"(cs_val));
    idt_set_gate(33, (uint32_t)irq1_stub, cs_val, 0x8E);
    /* IRQ12 = mouse = int 0x2C (44) */
    idt_set_gate(44, (uint32_t)irq12_stub, cs_val, 0x8E);

    idt_load((uint32_t)&idtp);

    /* Remap PIC */
    outb(0x20, 0x11); outb(0xA0, 0x11);
    outb(0x21, 0x20); outb(0xA1, 0x28);
    outb(0x21, 0x04); outb(0xA1, 0x02);
    outb(0x21, 0x01); outb(0xA1, 0x01);
    /* PIC: IRQ0 timer + IRQ1 keyboard + IRQ2 cascade (master),
       IRQ12 mouse (slave) */
    outb(0x21, 0xF9);   /* master: mask IRQ0 timer, unmask IRQ1 kb + IRQ2 cascade */
    outb(0xA1, 0xEF);   /* slave: unmask IRQ12 (bit 4) */

    __asm__ volatile("sti");
}
