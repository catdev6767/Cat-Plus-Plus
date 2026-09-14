/* CatOS — Kernel entry point. */

#include "catpp_rt.h"

/* Multiboot header — GRUB tìm để load */
__attribute__((section(".multiboot")))
const unsigned long multiboot_header[] = {
    0x1BADB002,  /* magic */
    0x0,         /* flags */
    0xE4524FFE,  /* checksum = -(magic + flags) */
};

/* Đây là hàm Cat++ sinh ra, hoặc viết tay để test */
extern int catpp_main(void);

void kmain(void) {
    catpp_init();
    catpp_print_str("CatOS v0.1");
    catpp_print_str("---------------");
    catpp_print_str("Kernel loaded.");
    catpp_print_str("Running Cat++ code...");
    catpp_print_str("");

    catpp_main();

    catpp_print_str("");
    catpp_print_str("Halted.");
    while (1) __asm__ volatile("hlt");
}
