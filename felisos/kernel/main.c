#include "catpp_rt.h"

__attribute__((section(".multiboot")))
const unsigned long multiboot_header[] = {
    0x1BADB002,         /* magic */
    0x6,                /* flags: align(1) + mem info(2) + video(4) */
    0xE4524FF8,         /* checksum = -(0x1BADB002 + 0x6) */
    /* Fields khi flag bit 2 = 1 */
    0, 0, 0, 0, 0,      /* header_addr, load, load_end, bss_end, entry (không dùng cho ELF) */
    0,                  /* mode_type: 0 = linear graphics */
    1024, 768, 32,      /* width, height, depth */
};

extern void shell_run(void);
extern void idt_init(void);
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
extern void fb_draw_panel(void);
extern void mouse_init(void);
extern void mouse_show(void);
extern volatile int g_pending_click;
extern volatile int g_click_x;
extern volatile int g_click_y;
extern int purrminal_handle_click(int mx, int my);
extern void purrminal_open(void);
extern void mouse_hide(void);

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
    idt_init();   /* BẮT BUỘC — enable IDT + STI + unmask IRQ */

    extern void fb_clear_all(void);
    extern void fb_draw_dock(void);
    extern void mouse_show(void);
    extern void mouse_hide(void);
    extern int tty_get(void);
    extern void tty_switch(int n);

    if (magic == 0x2BADB002) {
        struct mb_info* mbi = (struct mb_info*)mbi_addr;
        int has_fb = (mbi->flags & (1 << 12)) != 0
                     && mbi->framebuffer_addr != 0
                     && mbi->framebuffer_width > 0
                     && mbi->framebuffer_height > 0
                     && (mbi->framebuffer_bpp == 24 || mbi->framebuffer_bpp == 32)
                     && (mbi->framebuffer_type == 0 || mbi->framebuffer_type == 1);
        if (has_fb) {
            fb_init(mbi->framebuffer_addr, mbi->framebuffer_pitch,
                    mbi->framebuffer_width, mbi->framebuffer_height,
                    mbi->framebuffer_bpp);
            mouse_init();
        }
    }

    commands_init();

    /* Boot vào GUI mode */
    fb_clear_all();
    fb_draw_panel();
    fb_draw_dock();
    purrminal_open();
    mouse_show();

    while (1) {
        if (tty_get() == 1) {
            mouse_hide();
            shell_run();
            mouse_show();
            tty_switch(0);
        }
        __asm__ volatile("hlt");
    }
}
