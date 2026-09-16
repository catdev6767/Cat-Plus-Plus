/* Kitty kernel — PS/2 Mouse driver */
#include <stdint.h>

#define PS2_DATA   0x60
#define PS2_STATUS 0x64
#define PS2_CMD    0x64

static inline uint8_t inb(uint16_t port) {
    uint8_t r; __asm__ volatile("inb %1, %0" : "=a"(r) : "Nd"(port)); return r;
}
static inline void outb(uint16_t port, uint8_t val) {
    __asm__ volatile("outb %0, %1" : : "a"(val), "Nd"(port));
}
static inline void io_wait(void) { outb(0x80, 0); }

/* Mouse state */
static volatile int mouse_x = 400;
static volatile int mouse_y = 300;
static volatile uint8_t mouse_buttons = 0;
static volatile int mouse_cycle = 0;
static volatile int8_t mouse_buf[3];
static int screen_w = 800;
static int screen_h = 600;

/* External fb API */
extern int  fb_is_active(void);
extern uint32_t fb_width(void);
extern uint32_t fb_height(void);
extern void fb_cursor_draw(int x, int y);
extern void fb_cursor_move(int old_x, int old_y, int new_x, int new_y);

/* ─── PS/2 mouse command helpers ─── */
static void mouse_wait_write(void) {
    for (int i = 0; i < 100000; i++)
        if (!(inb(PS2_STATUS) & 2)) return;
}
static void mouse_wait_read(void) {
    for (int i = 0; i < 100000; i++)
        if (inb(PS2_STATUS) & 1) return;
}
static void mouse_write(uint8_t b) {
    mouse_wait_write();
    outb(PS2_CMD, 0xD4);
    mouse_wait_write();
    outb(PS2_DATA, b);
}
static uint8_t mouse_read(void) {
    mouse_wait_read();
    return inb(PS2_DATA);
}

void mouse_init(void) {
    /* Enable auxiliary device (mouse) */
    mouse_wait_write();
    outb(PS2_CMD, 0xA8);

    /* Read config byte */
    mouse_wait_write();
    outb(PS2_CMD, 0x20);
    mouse_wait_read();
    uint8_t cfg = inb(PS2_DATA);
    cfg |= 0x02;   /* enable IRQ12 */
    cfg &= ~0x20;  /* enable mouse clock */
    mouse_wait_write();
    outb(PS2_CMD, 0x60);
    mouse_wait_write();
    outb(PS2_DATA, cfg);

    /* Set defaults */
    mouse_write(0xF6);
    mouse_read();

    /* Enable data reporting */
    mouse_write(0xF4);
    mouse_read();

    /* Get screen size from fb if available */
    if (fb_is_active()) {
        screen_w = (int)fb_width();
        screen_h = (int)fb_height();
        mouse_x = screen_w / 2;
        mouse_y = screen_h / 2;
    }
    fb_cursor_draw(mouse_x, mouse_y);
}

/* ─── IRQ12 handler — đọc 3 byte ─── */
void mouse_handler(void) {
    uint8_t status = inb(PS2_STATUS);
    if (!(status & 0x20)) return;   /* không phải từ mouse */

    int8_t b = (int8_t)inb(PS2_DATA);

    switch (mouse_cycle) {
        case 0:
            mouse_buf[0] = b;
            if (!(b & 0x08)) break;   /* bit 3 luôn = 1 */
            mouse_cycle = 1;
            break;
        case 1:
            mouse_buf[1] = b;
            mouse_cycle = 2;
            break;
        case 2: {
            mouse_buf[2] = b;
            mouse_cycle = 0;

            uint8_t flags = (uint8_t)mouse_buf[0];
            int8_t dx = mouse_buf[1];
            int8_t dy = mouse_buf[2];

            if (flags & 0x40) { /* X overflow */ }
            else if (flags & 0x10) mouse_x += (int)dx - 256;  /* negative */
            else mouse_x += (int)dx;

            if (flags & 0x80) { /* Y overflow */ }
            else if (flags & 0x20) mouse_y -= ((int)dy - 256);
            else mouse_y -= (int)dy;

            /* Clamp */
            if (mouse_x < 0) mouse_x = 0;
            if (mouse_y < 0) mouse_y = 0;
            if (mouse_x > screen_w - 1) mouse_x = screen_w - 1;
            if (mouse_y > screen_h - 1) mouse_y = screen_h - 1;

            mouse_buttons = flags & 0x07;

            int new_x = mouse_x;
            int new_y = mouse_y;
            if (dx != 0 || dy != 0) {
                fb_cursor_move(mouse_x - dx, mouse_y + dy, new_x, new_y);
            }
            break;
        }
    }
}

int mouse_get_x(void) { return mouse_x; }
int mouse_get_y(void) { return mouse_y; }
uint8_t mouse_get_buttons(void) { return mouse_buttons; }
