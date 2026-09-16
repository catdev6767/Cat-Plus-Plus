#include "catpp_rt.h"

__attribute__((section(".multiboot")))
const unsigned long multiboot_header[] = {
    0x1BADB002,         /* magic */
    0x2,                /* flags: chỉ mem info, KHÔNG video */
    0xE4524FFC,         /* checksum = -(magic + 0x2) */
    0,                  /* mode_type: 0 = linear graphics */
    1024, 768, 32,      /* width, height, depth */
};

extern void shell_run(void);
extern void commands_init(void);

#include <stdint.h>

/* Multiboot info structure (chỉ cần framebuffer fields) */
struct mb_info {
    uint32_t flags;
    uint32_t mem_lower, mem_upper;
    uint32_t boot_device;
    uint32_t cmdline;
    uint32_t mods_count, mods_addr;
    uint32_t syms[4];
    uint32_t mmap_length, mmap_addr;
    uint32_t drives_length, drives_addr;
    uint32_t config_table;
    uint32_t boot_loader_name;
    uint32_t apm_table;
    uint32_t vbe_control_info;
    uint32_t vbe_mode_info;
    uint16_t vbe_mode, vbe_interface_seg, vbe_interface_off, vbe_interface_len;
    uint64_t framebuffer_addr;
    uint32_t framebuffer_pitch;
    uint32_t framebuffer_width;
    uint32_t framebuffer_height;
    uint8_t  framebuffer_bpp;
    uint8_t  framebuffer_type;
} __attribute__((packed));

extern void fb_init(uint64_t addr, uint32_t pitch, uint32_t width,
                    uint32_t height, uint8_t bpp);
extern int fb_is_active(void);
extern void mouse_init(void);

static void print_hex(uint32_t v) {
    char buf[11];
    buf[0] = '0'; buf[1] = 'x';
    for (int i = 0; i < 8; i++) {
        int nib = (v >> ((7-i) * 4)) & 0xF;
        buf[2+i] = nib < 10 ? ('0' + nib) : ('A' + nib - 10);
    }
    buf[10] = 0;
    catpp_print_str(buf);
}

void kmain(uint32_t mbi_addr, uint32_t magic) {
    catpp_init();

    catpp_print_str("[DBG] magic=");
    print_hex(magic);
    catpp_print_str("[DBG] mbi=");
    print_hex(mbi_addr);

    if (magic == 0x2BADB002) {
        struct mb_info* mbi = (struct mb_info*)mbi_addr;
        catpp_print_str("[DBG] flags=");
        print_hex(mbi->flags);
        catpp_print_str("[DBG] fb_type=");
        print_hex(mbi->framebuffer_type);
        catpp_print_str("[DBG] fb_addr_lo=");
        print_hex((uint32_t)mbi->framebuffer_addr);
        catpp_print_str("[DBG] fb_w=");
        print_hex(mbi->framebuffer_width);
        catpp_print_str("[DBG] fb_h=");
        print_hex(mbi->framebuffer_height);
        catpp_print_str("[DBG] fb_bpp=");
        print_hex(mbi->framebuffer_bpp);

        int has_fb = 0;
        if (has_fb) {
            fb_init(mbi->framebuffer_addr, mbi->framebuffer_pitch,
                    mbi->framebuffer_width, mbi->framebuffer_height,
                    mbi->framebuffer_bpp);
            catpp_print_str("[Kitty] Framebuffer OK");
            mouse_init();
            catpp_print_str("[Kitty] Mouse OK");
        } else {
            catpp_print_str("[Kitty] Khong co framebuffer, dung VGA text");
        }
    } else {
        catpp_print_str("[Kitty] Magic sai, khong co multiboot info");
    }

    commands_init();
    shell_run();
    while (1) __asm__ volatile("hlt");
}
