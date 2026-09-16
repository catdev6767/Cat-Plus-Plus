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
static uint32_t fg_color = 0x00FFFFFF;  /* trắng */
static uint32_t bg_color = 0x00300A24;  /* tím Ubuntu 10.10 */
static uint32_t font_scale = 2;  /* scale 8x8 -> 16x16 */

/* ═══ GUI panel ═══ */
#define PANEL_HEIGHT 24
#define PANEL_BG     0x001A1A1A  /* xám đậm */
#define PANEL_FG     0x00EEEEEE  /* gần trắng */
static int text_area_y0 = 0;   /* dòng text bắt đầu từ đây */


/* Forward decls */
void fb_clear(void);
void fb_draw_panel(void);
void fb_puts_panel(const char* s, int x, int y, uint32_t color);
static void shell_cursor_update(void);
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

    /* Clear toàn bộ trước */
    for (uint32_t y = 0; y < fb_h; y++)
        for (uint32_t x = 0; x < fb_w; x++)
            fb_pixel(x, y, bg_color);

    /* Vẽ panel + reserve text area */
    text_area_y0 = PANEL_HEIGHT + 4;
    fb_draw_panel();
    cur_x = 0;
    cur_y = text_area_y0;
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
    uint32_t sc = font_scale;
    for (int row = 0; row < 8; row++) {
        unsigned char bits = g[row];
        for (int col = 0; col < 8; col++) {
            uint32_t color = (bits & (0x80 >> col)) ? fg : bg;
            for (uint32_t dy = 0; dy < sc; dy++)
                for (uint32_t dx = 0; dx < sc; dx++)
                    fb_pixel(x + col*sc + dx, y + row*sc + dy, color);
        }
    }
}

/* ═══ In ký tự với wrap + scroll ═══ */
void fb_putc(char c) {
    if (!fb_on) return;
    /* Không cho text ghi đè panel */
    if ((int)cur_y < text_area_y0) cur_y = text_area_y0;
    uint32_t sc = font_scale;
    uint32_t cw = 8 * sc;   /* char width  */
    uint32_t chh = 8 * sc;  /* char height */

    if (c == '\n') {
        cur_x = 0;
        cur_y += chh;
    } else if (c == '\r') {
        cur_x = 0;
    } else if (c == '\b') {
        if (cur_x >= cw) cur_x -= cw;
    } else if (c == '\t') {
        cur_x = (cur_x + cw*4) & ~((cw*4) - 1);
    } else {
        fb_char_at(c, cur_x, cur_y, fg_color, bg_color);
        cur_x += cw;
        if (cur_x + cw > fb_w) { cur_x = 0; cur_y += chh; }
    }

    /* Scroll */
    if (cur_y + chh > fb_h) {
        uint32_t shift = chh;
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
    /* shell_cursor_update(); tắt để test */
}

void fb_puts(const char* s) {
    while (s && *s) fb_putc(*s++);
}

/* Vẽ top panel Ubuntu 10.10 style */
void fb_draw_panel(void) {
    if (!fb_on) return;

    /* Nền panel */
    fb_rect(0, 0, fb_w, PANEL_HEIGHT, PANEL_BG);

    /* Menu bên trái */
    fb_puts_panel("Applications", 12, 4, PANEL_FG);
    fb_puts_panel("Places",       110, 4, PANEL_FG);
    fb_puts_panel("System",       170, 4, PANEL_FG);

    /* Bên phải — giả lập */
    fb_puts_panel("felis@den", fb_w - 130, 4, PANEL_FG);
    fb_puts_panel("[12:00]",   fb_w - 60,  4, PANEL_FG);

    /* Đường kẻ dưới panel */
    fb_rect(0, PANEL_HEIGHT - 1, fb_w, 1, 0x00555555);

    /* Text bắt đầu ngay dưới panel */
    text_area_y0 = PANEL_HEIGHT + 8;
}

/* In chữ lên panel — không ảnh hưởng cursor chính */
void fb_puts_panel(const char* s, int x, int y, uint32_t color) {
    if (!fb_on) return;
    int cur = x;
    while (s && *s) {
        fb_char_at(*s++, cur, y, color, PANEL_BG);
        cur += 8;  /* scale=1 cho panel */
    }
}

void fb_clear(void) {
    if (!fb_on) return;
    /* Clear từ dưới panel trở xuống */
    int y0 = text_area_y0 > 0 ? text_area_y0 : 0;
    for (uint32_t y = y0; y < fb_h; y++)
        for (uint32_t x = 0; x < fb_w; x++)
            fb_pixel(x, y, bg_color);
    cur_x = 0;
    cur_y = (y0 > 0) ? (uint32_t)y0 : 0;
}

void fb_set_colors(uint32_t fg, uint32_t bg) {
    fg_color = fg;
    bg_color = bg;
}


/* ═══ Shell cursor (dấu _ nhấp nháy) ═══ */
static int shell_cur_visible = 0;
static int shell_cur_x = 0;
static int shell_cur_y = 0;
static uint32_t shell_cur_bg[8][2];  /* 8 pixel ngang, 2 pixel dọc */

static void shell_cursor_save(void) {
    for (int j = 0; j < 2; j++)
        for (int i = 0; i < 8; i++) {
            uint32_t px = 0;
            uint32_t xx = shell_cur_x + i, yy = shell_cur_y + j;
            if (xx < fb_w && yy < fb_h) {
                if (fb_bpp == 32) {
                    px = *(uint32_t*)(fb_ptr + yy * fb_pitch + xx * 4);
                } else {
                    uint8_t* p = fb_ptr + yy * fb_pitch + xx * 3;
                    px = (p[2] << 16) | (p[1] << 8) | p[0];
                }
            }
            shell_cur_bg[j][i] = px;
        }
}

static void shell_cursor_restore(void) {
    for (int j = 0; j < 2; j++)
        for (int i = 0; i < 8; i++)
            fb_pixel(shell_cur_x + i, shell_cur_y + j, shell_cur_bg[j][i]);
}

void fb_shell_cursor_hide(void) {
    if (shell_cur_visible) {
        shell_cursor_restore();
        shell_cur_visible = 0;
    }
}

void fb_shell_cursor_show(void) {
    if (!fb_on) return;
    shell_cur_x = cur_x;
    shell_cur_y = cur_y + 6;
    if (shell_cur_x + 8 > (int)fb_w) return;
    if (shell_cur_y + 2 > (int)fb_h) return;
    shell_cursor_save();
    for (int j = 0; j < 2; j++)
        for (int i = 0; i < 8; i++)
            fb_pixel(shell_cur_x + i, shell_cur_y + j, 0x00FFFFFF);
    shell_cur_visible = 1;
}

/* Gọi cuối fb_putc — cập nhật shell cursor */
static void shell_cursor_update(void) {
    if (shell_cur_visible) {
        shell_cursor_restore();
        shell_cur_visible = 0;
    }
    fb_shell_cursor_show();
}


/* ═══ Mouse cursor 12x12 arrow ═══ */
static const uint8_t cursor_arrow[12] = {
    0x80, 0xC0, 0xE0, 0xF0, 0xF8, 0xFC,
    0xFE, 0xF0, 0xD8, 0x8C, 0x04, 0x00,
};

static uint32_t cursor_bg[12][12];
static int cursor_visible = 0;
static int cursor_x = 0, cursor_y = 0;

static void cursor_save(void) {
    for (int j = 0; j < 12; j++)
        for (int i = 0; i < 12; i++) {
            uint32_t px = 0;
            uint32_t xx = cursor_x + i, yy = cursor_y + j;
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

static void cursor_restore(void) {
    for (int j = 0; j < 12; j++)
        for (int i = 0; i < 12; i++)
            fb_pixel(cursor_x + i, cursor_y + j, cursor_bg[j][i]);
}

static void cursor_draw(void) {
    for (int j = 0; j < 12; j++) {
        uint8_t bits = cursor_arrow[j];
        for (int i = 0; i < 12; i++) {
            if (bits & (0x80 >> i)) {
                int edge = (i == 0 || j == 0);
                uint32_t col = edge ? 0x00000000 : 0x00FFFFFF;
                fb_pixel(cursor_x + i, cursor_y + j, col);
            }
        }
    }
}

void fb_cursor_show(int x, int y) {
    if (!fb_on) return;
    if (x + 12 > (int)fb_w) x = fb_w - 12;
    if (y + 12 > (int)fb_h) y = fb_h - 12;
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    cursor_x = x;
    cursor_y = y;
    cursor_save();
    cursor_draw();
    cursor_visible = 1;
}

void fb_cursor_hide(void) {
    if (!fb_on || !cursor_visible) return;
    cursor_restore();
    cursor_visible = 0;
}
