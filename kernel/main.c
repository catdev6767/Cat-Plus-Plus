#include "catpp_rt.h"

__attribute__((section(".multiboot")))
const unsigned long multiboot_header[] = {
    0x1BADB002, 0x0, 0xE4524FFE,
};

extern void shell_run(void);
extern void commands_init(void);

void kmain(void) {
    catpp_init();
    commands_init();
    shell_run();
    while (1) __asm__ volatile("hlt");
}
