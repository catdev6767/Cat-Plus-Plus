/* Kitty kernel — Framebuffer driver (32bpp linear) */
#include <stdint.h>
#include "font8x8.h"

static uint8_t*  fb_ptr   = 0;
static uint32_t  fb_pitch  = 0;  /* bytes per row */
static uint32_t  fb_bpp    = 0;
static uint32_t  fb_w     = 0;
static uint32_t  fb_h     = 0;
static int       fb_on    = 0;

/* Vị trí text con trỏ */
static uint32_t cur_x = 0;
static uint32_t cur_y = 0;

/* Màu mặc định (0x00RRGGBB) */
static uint32_t fg_color = 0x00FFFFFF;
static uint32_t bg_color = 0x00000000;

/* Forward decls */
void fb_clear(void);
void fb_pixel(uint32_t x, uint32_t y, uint32_t color);

void fb_init(uint64_t addr, uint32_t pitch, uint32_t width,
             uint32_t height, uint8_t bpp) {
    if (bpp != 24 && bpp != 32) return;
    if (addr == 0 || width == 0 || height == 0) return;
    fb_ptr = (uint8_t*)(uint32_t)addr;
    fb_pitch = pitch;
    fb_bpp = bpp;
    fb_w = width;
    fb_h = height;
    fb_on = 1;

    fb_clear();
}

int fb_is_active(void) { return fb_on; }
uint32_t fb_width(void)  { return fb_w; }
uint32_t fb_height(void) { return fb_h; }

/* ═══ Vẽ 1 pixel ═══ */
void fb_pixel(uint32_t x, uint32_t y, uint32_t color) {
    if (!fb_on || x >= fb_w || y >= fb_h) return;
    if (fb_bpp == 32) {
        uint32_t* p = (uint32_t*)(fb_ptr + y * fb_pitch + x * 4);
        *p = color;
    } else {  /* 24bpp — BGR */
        uint8_t* p = fb_ptr + y * fb_pitch + x * 3;
        p[0] = color & 0xFF;          /* B */
        p[1] = (color >> 8) & 0xFF;   /* G */
        p[2] = (color >> 16) & 0xFF;  /* R */
    }
}

/* ═══ Vẽ hình chữ nhật đặc ═══ */
void fb_rect(uint32_t x, uint32_t y, uint32_t w, uint32_t h, uint32_t color) {
    if (!fb_on) return;
    for (uint32_t j = 0; j < h; j++)
        for (uint32_t i = 0; i < w; i++)
            fb_pixel(x + i, y + j, color);
}

/* ═══ Vẽ 1 ký tự font 8x8 ═══ */
void fb_char_at(char ch, uint32_t x, uint32_t y, uint32_t fg, uint32_t bg) {
    if (!fb_on) return;
    if (ch < 32 || ch > 127) ch = '?';
    const unsigned char* g = font8x8[ch - 32];
    for (int row = 0; row < 8; row++) {
        unsigned char bits = g[row];
        for (int col = 0; col < 8; col++) {
            uint32_t color = (bits & (0x80 >> col)) ? fg : bg;
            fb_pixel(x + col, y + row, color);
        }
    }
}

/* ═══ In ký tự với wrap + scroll ═══ */
void fb_putc(char c) {
    if (!fb_on) return;

    if (c == '\n') {
        cur_x = 0;
        cur_y += 8;
    } else if (c == '\r') {
        cur_x = 0;
    } else if (c == '\b') {
        if (cur_x >= 8) cur_x -= 8;
        fb_rect(cur_x, cur_y, 8, 8, bg_color);
    } else if (c == '\t') {
        cur_x = (cur_x + 32) & ~31u;
    } else {
        fb_char_at(c, cur_x, cur_y, fg_color, bg_color);
        cur_x += 8;
        if (cur_x + 8 > fb_w) { cur_x = 0; cur_y += 8; }
    }

    /* Scroll */
    if (cur_y + 8 > fb_h) {
        uint32_t shift = 8;
        uint32_t bytes_per_row = fb_w * (fb_bpp / 8);
        for (uint32_t y = 0; y < fb_h - shift; y++) {
            uint8_t* dst = fb_ptr + y * fb_pitch;
            uint8_t* src = fb_ptr + (y + shift) * fb_pitch;
            for (uint32_t i = 0; i < bytes_per_row; i++)
                dst[i] = src[i];
        }
        for (uint32_t y = fb_h - shift; y < fb_h; y++)
            for (uint32_t x = 0; x < fb_w; x++)
                fb_pixel(x, y, bg_color);
        cur_y -= shift;
    }
}

void fb_puts(const char* s) {
    while (s && *s) fb_putc(*s++);
}

void fb_clear(void) {
    if (!fb_on) return;
    for (uint32_t y = 0; y < fb_h; y++)
        for (uint32_t x = 0; x < fb_w; x++)
            fb_pixel(x, y, bg_color);
    cur_x = 0; cur_y = 0;
}

void fb_set_colors(uint32_t fg, uint32_t bg) {
    fg_color = fg;
    bg_color = bg;
}


/* ═══ Mouse cursor 8x8 ═══ */
static const unsigned char cursor_bitmap[8] = {
    0x80,  /* X....... */
    0xC0,  /* XX...... */
    0xE0,  /* XXX..... */
    0xF0,  /* XXXX.... */
    0xF8,  /* XXXXX... */
    0xE0,  /* XXX..... */
    0xC0,  /* XX...... */
    0x80,  /* X....... */
};

/* Lưu background 8x8 pixel để restore khi cursor di chuyển */
static uint32_t cursor_bg[8][8];
static int cursor_last_x = -1;
static int cursor_last_y = -1;

/* Lưu vùng 8x8 vào buffer */
static void save_region(int x, int y) {
    for (int j = 0; j < 8; j++) {
        for (int i = 0; i < 8; i++) {
            uint32_t px = 0x00000000;
            uint32_t xx = x + i, yy = y + j;
            if (xx < fb_w && yy < fb_h) {
                if (fb_bpp == 32) {
                    px = *(uint32_t*)(fb_ptr + yy * fb_pitch + xx * 4);
                } else {
                    uint8_t* p = fb_ptr + yy * fb_pitch + xx * 3;
                    px = (p[2] << 16) | (p[1] << 8) | p[0];
                }
            }
            cursor_bg[j][i] = px;
        }
    }
}

/* Khôi phục vùng từ buffer */
static void restore_region(int x, int y) {
    for (int j = 0; j < 8; j++) {
        for (int i = 0; i < 8; i++) {
            fb_pixel(x + i, y + j, cursor_bg[j][i]);
        }
    }
}

/* Vẽ cursor tại (x, y) */
static void draw_cursor_pixels(int x, int y) {
    for (int j = 0; j < 8; j++) {
        unsigned char bits = cursor_bitmap[j];
        for (int i = 0; i < 8; i++) {
            if (bits & (0x80 >> i)) {
                /* Viền trắng, trong đen */
                int edge = (i == 0 || j == 0 || i == 7 || j == 7);
                uint32_t color = edge ? 0x00FFFFFF : 0x00000000;
                fb_pixel(x + i, y + j, color);
            }
        }
    }
}

void fb_cursor_draw(int x, int y) {
    if (!fb_on) return;
    if (x + 8 >= (int)fb_w) x = fb_w - 8;
    if (y + 8 >= (int)fb_h) y = fb_h - 8;
    save_region(x, y);
    draw_cursor_pixels(x, y);
    cursor_last_x = x;
    cursor_last_y = y;
}

void fb_cursor_move(int old_x, int old_y, int new_x, int new_y) {
    if (!fb_on) return;
    /* Restore vị trí cũ */
    if (cursor_last_x >= 0 && cursor_last_y >= 0)
        restore_region(cursor_last_x, cursor_last_y);
    /* Clamp */
    if (new_x < 0) new_x = 0;
    if (new_y < 0) new_y = 0;
    if (new_x + 8 >= (int)fb_w) new_x = fb_w - 9;
    if (new_y + 8 >= (int)fb_h) new_y = fb_h - 9;
    /* Save + vẽ vị trí mới */
    save_region(new_x, new_y);
    draw_cursor_pixels(new_x, new_y);
    cursor_last_x = new_x;
    cursor_last_y = new_y;
}
