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
#define DOCK_WIDTH   160
#define DOCK_BG      0x00151515
#define PANEL_FG     0x00EEEEEE  /* gần trắng */
static int text_area_y0 = 0;
static int text_area_x0 = 0;   /* dòng text bắt đầu từ đây */


/* Forward decls */
void fb_clear(void);
void fb_draw_panel(void);
void fb_draw_dock(void);
void fb_clear_all(void);
void fb_puts_at(const char* s, int x, int y, uint32_t color);
void fb_puts_at_color(const char* s, int x, int y, uint32_t fg, uint32_t bg);
void fb_char_at_scale(char ch, int x, int y, uint32_t fg, uint32_t bg, int scale);
void fb_char_at_scale_xy(char ch, int x, int y, uint32_t fg, uint32_t bg, int sx, int sy);
void fb_puts_scale_xy(const char* s, int x, int y, uint32_t fg, uint32_t bg, int sx, int sy);
void fb_puts_scale(const char* s, int x, int y, uint32_t fg, uint32_t bg, int scale);
void fb_puts_panel(const char* s, int x, int y, uint32_t color);
void fb_cursor_forget(void);
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
static void _fb_putc_inner(char c) {
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

void fb_putc(char c) {
    extern int mouse_is_visible(void);
    extern void mouse_hide(void);
    extern void mouse_show(void);
    int mvis = 0;
    if (fb_on) {
        mvis = mouse_is_visible();
        if (mvis) mouse_hide();
    }
    _fb_putc_inner(c);
    if (mvis) mouse_show();
}

void fb_puts(const char* s) {
    while (s && *s) fb_putc(*s++);
}

/* Vẽ top panel Ubuntu 10.10 style */

/* In chữ lên panel — không ảnh hưởng cursor chính */
void fb_puts_panel(const char* s, int x, int y, uint32_t color) {
    if (!fb_on) return;
    int cur = x;
    uint32_t cw = 8 * font_scale;
    while (s && *s) {
        fb_char_at(*s++, cur, y, color, PANEL_BG);
        cur += cw;
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

void fb_cursor_forget(void) {
    /* Quên cursor mà không restore background cũ.
       Dùng sau khi clear màn hình. */
    cursor_visible = 0;
}

void fb_cursor_hide(void) {
    if (!fb_on || !cursor_visible) return;
    cursor_restore();
    cursor_visible = 0;
}


/* In chu tai (x, y) voi mau fg + bg */
/* Vẽ ký tự với scale tùy ý */
void fb_char_at_scale_xy(char ch, int x, int y, uint32_t fg, uint32_t bg,
                           int sx, int sy) {
    if (!fb_on) return;
    if (ch < 32 || ch > 127) ch = '?';
    const unsigned char* g = font8x8[ch - 32];
    for (int row = 0; row < 8; row++) {
        unsigned char bits = g[row];
        for (int col = 0; col < 8; col++) {
            uint32_t color = (bits & (0x80 >> col)) ? fg : bg;
            for (int dy = 0; dy < sy; dy++)
                for (int dx = 0; dx < sx; dx++)
                    fb_pixel(x + col*sx + dx, y + row*sy + dy, color);
        }
    }
}

void fb_puts_scale_xy(const char* s, int x, int y, uint32_t fg, uint32_t bg,
                      int sx, int sy) {
    if (!fb_on) return;
    int cur = x;
    while (s && *s) {
        fb_char_at_scale_xy(*s++, cur, y, fg, bg, sx, sy);
        cur += 8 * sx;
    }
}

void fb_char_at_scale(char ch, int x, int y, uint32_t fg, uint32_t bg, int scale) {
    if (!fb_on) return;
    if (ch < 32 || ch > 127) ch = '?';
    const unsigned char* g = font8x8[ch - 32];
    for (int row = 0; row < 8; row++) {
        unsigned char bits = g[row];
        for (int col = 0; col < 8; col++) {
            uint32_t color = (bits & (0x80 >> col)) ? fg : bg;
            for (int dy = 0; dy < scale; dy++)
                for (int dx = 0; dx < scale; dx++)
                    fb_pixel(x + col*scale + dx, y + row*scale + dy, color);
        }
    }
}

/* Chuỗi có scale */
void fb_puts_scale(const char* s, int x, int y, uint32_t fg, uint32_t bg, int scale) {
    if (!fb_on) return;
    int cur = x;
    while (s && *s) {
        fb_char_at_scale(*s++, cur, y, fg, bg, scale);
        cur += 8 * scale;
    }
}

void fb_puts_at_color(const char* s, int x, int y, uint32_t fg, uint32_t bg) {
    if (!fb_on) return;
    int cur = x;
    while (s && *s) {
        fb_char_at(*s++, cur, y, fg, bg);
        cur += 8;
    }
}

void fb_puts_at(const char* s, int x, int y, uint32_t color) {
    fb_puts_at_color(s, x, y, color, 0x000000);
}




/* ═══ WinXP Luna theme ═══ */
#define TASKBAR_H 32
#define TASKBAR_TOP_BLUE 0x00245EDF
#define TASKBAR_MID_BLUE 0x003A6EA5
#define START_GREEN_TOP  0x0057A843
#define START_GREEN_BOT  0x003D7A2E
#define TITLE_BLUE_TOP   0x005B9DE5
#define TITLE_BLUE_BOT   0x003A6EA5
#define XP_PANEL_BG      0x00ECE9D8




/* ═══ WinXP Taskbar + Start menu ═══ */
#define TASKBAR_H 32
#define START_BTN_W 100
#define START_MENU_W 200

/* State: Start menu mở/đóng */
static int g_start_open = 0;
/* App nào đang mở trên taskbar */

extern int purrminal_is_visible(void);
extern int filemgr_is_visible(void);
extern int pawedit_is_visible(void);
extern int coming_soon_visible(void);

void fb_start_menu_toggle(void) { g_start_open = !g_start_open; }
void fb_start_menu_close(void) { g_start_open = 0; }
int  fb_start_menu_is_open(void) { return g_start_open; }

void fb_draw_panel(void) {
    /* XP không có panel trên */
    if (!fb_on) return;
}

/* Vẽ Start menu (popup trên taskbar) */
void fb_draw_start_menu(void) {
    if (!fb_on || !g_start_open) return;

    int mw = START_MENU_W;
    int mh = 260;
    int mx = 4;
    int my = fb_h - TASKBAR_H - mh;

    /* Shadow */
    fb_rect(mx + 4, my + 4, mw, mh, 0x00101010);

    /* Menu body — trắng kem */
    fb_rect(mx, my, mw, mh, 0x00FFFFFF);

    /* Header — gradient xanh XP */
    for (int yy = 0; yy < 40; yy++) {
        uint32_t col = (yy < 12) ? 0x0060A8E8 : 0x003A6EA5;
        fb_rect(mx, my + yy, mw, 1, col);
    }

    /* Tên user */
    extern void fb_puts_at_color(const char* s, int x, int y, uint32_t fg, uint32_t bg);
    fb_puts_at_color("kitty", mx + 44, my + 14, 0x00FFFFFF, 0x003A6EA5);

    /* Avatar — icon user */
    fb_rect(mx + 12, my + 8, 24, 24, 0x00FFFFFF);
    fb_rect(mx + 16, my + 12, 16, 16, 0x00E8A040);

    /* Menu items */
    const char* items[] = {"Purrminal", "Files", "PawEditor", "Catting",
                           "Login", "About", "Shutdown"};
    int item_h = 28;
    int items_y = my + 46;

    for (int i = 0; i < 7; i++) {
        int iy = items_y + i * item_h;

        /* Separator trước Shutdown */
        if (i == 6) {
            fb_rect(mx + 8, iy - 2, mw - 16, 1, 0x00CCCCCC);
        }

        /* Icon nhỏ */
        fb_rect(mx + 12, iy + 6, 18, 18, 0x00FF8800);
        fb_rect(mx + 14, iy + 8, 14, 14, 0x00FFFFFF);

        /* Text */
        fb_puts_at_color(items[i], mx + 40, iy + 8, 0x00000000, 0x00FFFFFF);
    }

    /* Border */
    fb_rect(mx, my, mw, 2, 0x003A6EA5);
    fb_rect(mx, my + mh - 2, mw, 2, 0x003A6EA5);
    fb_rect(mx, my, 2, mh, 0x003A6EA5);
    fb_rect(mx + mw - 2, my, 2, mh, 0x003A6EA5);
}

/* Click vào Start menu — trả về 1 nếu handled */
int fb_start_menu_click(int mx, int my) {
    if (!g_start_open) return 0;

    int mw = START_MENU_W;
    int mh = 260;
    int sx = 4;
    int sy = fb_h - TASKBAR_H - mh;

    /* Ngoài menu? */
    if (mx < sx || mx > sx + mw || my < sy || my > sy + mh) {
        g_start_open = 0;
        return 0;
    }

    /* Item click? */
    int items_y = sy + 46;
    int item_h = 28;
    for (int i = 0; i < 7; i++) {
        int iy = items_y + i * item_h;
        if (my >= iy && my < iy + item_h) {
            g_start_open = 0;

            extern void purrminal_open(void);
            extern void filemgr_open(void);
            extern void pawedit_open(const char*);
            extern void coming_soon_open(const char*);
            extern int fs_create(const char*, int);

            switch (i) {
                case 0: purrminal_open(); break;
                case 1: filemgr_open(); break;
                case 2: fs_create("untitled.txt", 0); pawedit_open("untitled.txt"); break;
                case 3: coming_soon_open("Catting"); break;
                case 4: coming_soon_open("Login"); break;
                case 5: coming_soon_open("About"); break;
                case 6: coming_soon_open("Shutdown"); break;
            }

            /* App tự vẽ, chỉ cần đóng menu */
            g_start_open = 0;
            return 1;
        }
    }
    return 1;
}

/* Vẽ taskbar XP */
void fb_draw_wallpaper(void) {
    if (!fb_on) return;
    int top_h = fb_h - TASKBAR_H;
    int half = top_h / 2;
    for (int y = 0; y < top_h; y++) {
        uint32_t r, g, b;
        if (y < half) {
            r = 0x40 + ((y * 0x30) / half);
            g = 0x70 + ((y * 0x30) / half);
            b = 0xC0 - ((y * 0x40) / half);
        } else {
            int yy = y - half;
            r = 0x50 + ((yy * 0x20) / half);
            g = 0x90 + ((yy * 0x20) / half);
            b = 0x40 + ((yy * 0x10) / half);
        }
        fb_rect(0, y, fb_w, 1, (r << 16) | (g << 8) | b);
    }
}

void fb_draw_dock(void) {
    if (!fb_on) return;

    /* ═══ Wallpaper Bliss ═══ */
    for (uint32_t y = 0; y < fb_h - TASKBAR_H; y++) {
        for (uint32_t x = 0; x < fb_w; x++) {
            uint32_t r, g, b;
            if (y < (fb_h - TASKBAR_H) / 2) {
                r = 0x40 + ((y * 0x30) / ((fb_h - TASKBAR_H) / 2));
                g = 0x70 + ((y * 0x30) / ((fb_h - TASKBAR_H) / 2));
                b = 0xC0 - ((y * 0x40) / ((fb_h - TASKBAR_H) / 2));
            } else {
                uint32_t yy = y - (fb_h - TASKBAR_H) / 2;
                r = 0x50 + ((yy * 0x20) / ((fb_h - TASKBAR_H) / 2));
                g = 0x90 + ((yy * 0x20) / ((fb_h - TASKBAR_H) / 2));
                b = 0x40 + ((yy * 0x10) / ((fb_h - TASKBAR_H) / 2));
            }
            fb_pixel(x, y, (r << 16) | (g << 8) | b);
        }
    }

    /* ═══ Taskbar dưới ═══ */
    int ty = fb_h - TASKBAR_H;

    for (int yy = 0; yy < TASKBAR_H; yy++) {
        uint32_t col;
        if (yy < 4)       col = 0x002860DC;
        else if (yy < 8)  col = 0x00245EDF;
        else if (yy < 20) col = 0x003A6EA5;
        else if (yy < 28) col = 0x002358B0;
        else              col = 0x001A4680;
        fb_rect(0, ty + yy, fb_w, 1, col);
    }
    fb_rect(0, ty, fb_w, 1, 0x0060A0FF);

    /* ═══ Start button — không có logo Windows, chỉ chữ "Felis" ═══ */
    int sx = 4, sw = START_BTN_W, sh = TASKBAR_H - 6;
    int sy = ty + 3;

    for (int yy = 0; yy < sh; yy++) {
        uint32_t col;
        if (yy < 4)        col = 0x0070C860;
        else if (yy < sh/2) col = 0x0057A843;
        else if (yy < sh-4) col = 0x003D7A2E;
        else               col = 0x002A5010;
        fb_rect(sx + 2, sy + yy, sw - 4, 1, col);
    }
    /* Bo góc */
    fb_rect(sx, sy + 4, 1, sh - 8, 0x00505050);
    fb_rect(sx + 1, sy + 2, 1, sh - 4, 0x00505050);
    fb_rect(sx + sw - 1, sy + 4, 1, sh - 8, 0x00505050);
    fb_rect(sx + sw - 2, sy + 2, 1, sh - 4, 0x00505050);

    /* Chữ "Felis" to rõ */
    extern void fb_puts_scale_xy(const char* s, int x, int y, uint32_t fg, uint32_t bg, int sx, int sy);
    fb_puts_scale_xy("Felis", sx + 22, sy + 6, 0x00FFFFFF, 0x0057A843, 1, 2);

    /* ═══ Taskbar items — chỉ hiện app đang mở ═══ */
    int bx = sx + sw + 8;
    int btn_h = TASKBAR_H - 8;
    int by = ty + 4;

    const char* labels[] = {"Purrminal", "Files", "PawEditor", "Catting"};
    int visible[] = {
        purrminal_is_visible(),
        filemgr_is_visible(),
        pawedit_is_visible(),
        0
    };

    for (int i = 0; i < 4; i++) {
        if (!visible[i]) continue;

        int bw = 100;
        for (int yy = 0; yy < btn_h; yy++) {
            uint32_t col;
            if (yy < 2) col = 0x0050A0E8;
            else if (yy < btn_h - 2) col = 0x002A5FA5;
            else col = 0x001F4578;
            fb_rect(bx + 1, by + yy, bw - 2, 1, col);
        }
        fb_rect(bx, by, bw, 1, 0x0060A8F0);
        fb_rect(bx, by + btn_h - 1, bw, 1, 0x00103058);
        fb_rect(bx, by, 1, btn_h, 0x0060A8F0);
        fb_rect(bx + bw - 1, by, 1, btn_h, 0x00103058);

        fb_puts_at_color(labels[i], bx + 8, by + 4, 0x00FFFFFF, 0x002A5FA5);
        bx += bw + 4;
    }

    /* ═══ System tray phải ═══ */
    int tray_x = (int)fb_w - 90;
    for (int yy = 0; yy < btn_h; yy++) {
        uint32_t col = (yy < btn_h/2) ? 0x002560B0 : 0x00184078;
        fb_rect(tray_x, by + yy, 80, 1, col);
    }
    fb_puts_at_color("12:00", tray_x + 22, by + 4, 0x00FFFFFF, 0x002560B0);

    /* Vẽ Start menu nếu đang mở */
    if (g_start_open) fb_draw_start_menu();

    text_area_y0 = 4;
    text_area_x0 = 4;
    cur_x = text_area_x0;
    cur_y = text_area_y0;
}

void fb_clear_all(void) {
    if (!fb_on) return;
    /* Wallpaper xanh gradient dọc */
    for (uint32_t y = 0; y < fb_h; y++) {
        for (uint32_t x = 0; x < fb_w; x++) {
            uint32_t b = 0x87 + ((y * 30) / fb_h);
            if (b > 0xFF) b = 0xFF;
            uint32_t color = (0x20 << 16) | (0x4A << 8) | b;
            fb_pixel(x, y, color);
        }
    }
    cur_x = 0;
    cur_y = 0;
}


