/* Kitty kernel — PS/2 Mouse driver + cursor overlay */
#include <stdint.h>

#define PS2_DATA   0x60
#define PS2_STATUS 0x64
#define PS2_CMD    0x64

extern void serial_print_str(const char* s);

static inline uint8_t inb(uint16_t port) {
    uint8_t r; __asm__ volatile("inb %1, %0" : "=a"(r) : "Nd"(port)); return r;
}
static inline void outb(uint16_t port, uint8_t val) {
    __asm__ volatile("outb %0, %1" : : "a"(val), "Nd"(port));
}

/* Mouse state */
static volatile int mouse_x = 400;
static volatile int mouse_y = 300;
static volatile uint8_t mouse_buttons = 0;
static volatile int mouse_cycle = 0;
static volatile int8_t mouse_buf[3];
static int screen_w = 1024;
static int screen_h = 768;
static int g_mouse_visible = 0;

/* External fb API */
extern int  fb_is_active(void);
extern uint32_t fb_width(void);
extern uint32_t fb_height(void);
extern void fb_cursor_show(int x, int y);
extern void fb_cursor_hide(void);

/* ─── PS/2 helpers ─── */
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
    serial_print_str("[mouse] init start");
    mouse_wait_write();
    outb(PS2_CMD, 0xA8);
    serial_print_str("[mouse] A8 sent");

    mouse_wait_write();
    outb(PS2_CMD, 0x20);
    mouse_wait_read();
    uint8_t cfg = inb(PS2_DATA);
    cfg |= 0x02;
    cfg &= ~0x20;
    mouse_wait_write();
    outb(PS2_CMD, 0x60);
    mouse_wait_write();
    outb(PS2_DATA, cfg);

    mouse_write(0xF6);
    mouse_read();
    mouse_write(0xF4);
    mouse_read();

    if (fb_is_active()) {
        screen_w = (int)fb_width();
        screen_h = (int)fb_height();
        mouse_x = screen_w / 2;
        mouse_y = screen_h / 2;
    }
    serial_print_str("[mouse] init done");
}

/* ─── IRQ12 handler ─── */
static int mouse_irq_count = 0;

void mouse_handler(void) {
    /* Đọc hết mọi byte có sẵn trong FIFO */
    while (1) {
        uint8_t status = inb(PS2_STATUS);
        if (!(status & 0x01)) break;   /* OBF clear = hết data */
        if (!(status & 0x20)) break;   /* không phải từ mouse */

        int8_t b = (int8_t)inb(PS2_DATA);
        mouse_irq_count++;

        switch (mouse_cycle) {
            case 0:
                mouse_buf[0] = b;
                if (!(b & 0x08)) break;
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

                int new_x = mouse_x + (int)dx;
                int new_y = mouse_y - (int)dy;

                if (new_x < 0) new_x = 0;
                if (new_y < 0) new_y = 0;
                if (new_x > screen_w - 1) new_x = screen_w - 1;
                if (new_y > screen_h - 1) new_y = screen_h - 1;

                mouse_buttons = flags & 0x07;

                /* Log tọa độ: "dx,dy->x,y" */
                {
                    static int log_count = 0;
                    log_count++;
                    if (log_count <= 10 || log_count % 20 == 0) {
                        char b[40];
                        int o = 0;
                        b[o++] = '[';
                        /* dx */
                        int v = (int)dx;
                        if (v < 0) { b[o++] = '-'; v = -v; }
                        b[o++] = '0' + (v/10)%10;
                        b[o++] = '0' + v%10;
                        b[o++] = ',';
                        /* dy */
                        v = (int)dy;
                        if (v < 0) { b[o++] = '-'; v = -v; }
                        b[o++] = '0' + (v/10)%10;
                        b[o++] = '0' + v%10;
                        b[o++] = '-'; b[o++] = '>';
                        /* x */
                        v = new_x;
                        b[o++] = '0' + (v/100)%10;
                        b[o++] = '0' + (v/10)%10;
                        b[o++] = '0' + v%10;
                        b[o++] = ',';
                        /* y */
                        v = new_y;
                        b[o++] = '0' + (v/100)%10;
                        b[o++] = '0' + (v/10)%10;
                        b[o++] = '0' + v%10;
                        b[o++] = ']'; b[o] = 0;
                        serial_print_str(b);
                    }
                }

                if (g_mouse_visible && (new_x != mouse_x || new_y != mouse_y)) {
                    fb_cursor_hide();
                    mouse_x = new_x;
                    mouse_y = new_y;
                    fb_cursor_show(mouse_x, mouse_y);
                } else {
                    mouse_x = new_x;
                    mouse_y = new_y;
                }
                break;
            }
        }
    }
}

/* Public */
void mouse_show(void) {
    if (!fb_is_active()) return;
    g_mouse_visible = 1;
    fb_cursor_show(mouse_x, mouse_y);
}

void mouse_hide(void) {
    if (!g_mouse_visible) return;
    g_mouse_visible = 0;
    fb_cursor_hide();
}

int mouse_is_visible(void) { return g_mouse_visible; }

int mouse_get_x(void) { return mouse_x; }
int mouse_get_y(void) { return mouse_y; }
uint8_t mouse_get_buttons(void) { return mouse_buttons; }
