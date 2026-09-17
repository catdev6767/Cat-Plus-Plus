/* Kitty — App menu (Launcher) */
#include <stdint.h>

extern int  fb_is_active(void);
extern uint32_t fb_width(void);
extern uint32_t fb_height(void);
extern void fb_rect(uint32_t x, uint32_t y, uint32_t w, uint32_t h, uint32_t color);
extern void fb_char_at(char ch, uint32_t x, uint32_t y, uint32_t fg, uint32_t bg);
extern void fb_puts_at_color(const char* s, int x, int y, uint32_t fg, uint32_t bg);
extern void fb_puts_scale(const char* s, int x, int y, uint32_t fg, uint32_t bg, int scale);
extern void fb_draw_panel(void);
extern void fb_draw_dock(void);
extern void fb_clear_all(void);
extern int  tty_get(void);
extern void tty_switch(int n);
extern void shell_run(void);

/* ═══ Logo 24x24 bitmap (3 byte/row = 24 bit) ═══ */
typedef struct {
    const uint8_t rows[24][3];
} Logo24;

/* ═══ App definitions ═══ */
typedef struct {
    const char* name;
    const char* desc;
    int has_logo;
    Logo24 logo;
    int (*launch)(void);
} App;

/* Logo terminal: khung vuông + dấu > _ */
static const Logo24 logo_purrminal = {{
    {0x00,0x00,0x00},{0x00,0x00,0x00},
    {0x7F,0xFF,0xFE},{0x40,0x00,0x02},{0x40,0x00,0x02},
    {0x40,0x00,0x02},{0x40,0x00,0x02},{0x40,0x00,0x02},
    {0x40,0x00,0x02},{0x40,0x00,0x02},{0x40,0x00,0x02},
    {0x40,0x00,0x02},{0x40,0x00,0x02},{0x40,0x00,0x02},
    {0x40,0x00,0x02},{0x40,0x00,0x02},{0x40,0x00,0x02},
    {0x40,0x00,0x02},{0x40,0x00,0x02},{0x40,0x00,0x02},
    {0x40,0x00,0x02},{0x40,0x00,0x02},
    {0x7F,0xFF,0xFE},{0x00,0x00,0x00},
}};

/* Logo file-manager: ngăn kéo */
static const Logo24 logo_filemgr = {{
    {0x00,0x00,0x00},{0x00,0x00,0x00},
    {0x1F,0x00,0x00},{0x3F,0x80,0x00},{0x60,0xC0,0x00},
    {0x40,0x40,0x00},{0x7F,0xFF,0xFE},{0x40,0x00,0x02},
    {0x40,0x00,0x02},{0x40,0x00,0x02},{0x40,0x00,0x02},
    {0x40,0x00,0x02},{0x40,0x00,0x02},{0x40,0x00,0x02},
    {0x40,0x00,0x02},{0x40,0x00,0x02},{0x40,0x00,0x02},
    {0x40,0x00,0x02},{0x40,0x00,0x02},{0x40,0x00,0x02},
    {0x40,0x00,0x02},{0x40,0x00,0x02},
    {0x7F,0xFF,0xFE},{0x00,0x00,0x00},
}};

/* Logo editor: bút chì */
static const Logo24 logo_pawedit = {{
    {0x00,0x00,0x00},{0x00,0x00,0x00},
    {0x00,0x07,0x80},{0x00,0x0F,0xC0},{0x00,0x1C,0xE0},
    {0x00,0x38,0x70},{0x00,0x70,0x38},{0x00,0xE0,0x1C},
    {0x01,0xC0,0x0E},{0x03,0x80,0x07},{0x07,0x00,0x07},
    {0x0E,0x00,0x0E},{0x1C,0x00,0x1C},{0x38,0x00,0x38},
    {0x70,0x00,0x70},{0x60,0x00,0xE0},{0x30,0x01,0xC0},
    {0x18,0x03,0x80},{0x0C,0x07,0x00},{0x06,0x0E,0x00},
    {0x03,0x1C,0x00},{0x01,0xF8,0x00},
    {0x00,0xF0,0x00},{0x00,0x00,0x00},
}};

/* Logo catting: bánh răng */
static const Logo24 logo_catting = {{
    {0x00,0x00,0x00},{0x00,0x00,0x00},
    {0x00,0x18,0x00},{0x06,0x18,0x60},{0x06,0x3C,0x60},
    {0x0F,0x3C,0xF0},{0x1F,0xFF,0xF8},{0x3F,0xFF,0xFC},
    {0x3F,0xC3,0xFC},{0x3F,0x81,0xFC},{0x3F,0x00,0xFC},
    {0x3F,0x00,0xFC},{0x3F,0x00,0xFC},{0x3F,0x81,0xFC},
    {0x3F,0xC3,0xFC},{0x3F,0xFF,0xFC},{0x1F,0xFF,0xF8},
    {0x0F,0x3C,0xF0},{0x06,0x3C,0x60},{0x06,0x18,0x60},
    {0x00,0x18,0x00},{0x00,0x00,0x00},
    {0x00,0x00,0x00},{0x00,0x00,0x00},
}};

/* Logo login: ổ khóa */
static const Logo24 logo_login = {{
    {0x00,0x00,0x00},{0x00,0x00,0x00},
    {0x00,0x3C,0x00},{0x00,0x7E,0x00},{0x00,0xC3,0x00},
    {0x00,0xC3,0x00},{0x00,0xC3,0x00},{0x00,0xC3,0x00},
    {0x00,0xFF,0x00},{0x03,0xFF,0xC0},{0x07,0xFF,0xE0},
    {0x0F,0xFF,0xF0},{0x0F,0xFF,0xF0},{0x0F,0xE7,0xF0},
    {0x0F,0xC3,0xF0},{0x0F,0xE7,0xF0},{0x0F,0xFF,0xF0},
    {0x0F,0xFF,0xF0},{0x0F,0xFF,0xF0},{0x07,0xFF,0xE0},
    {0x03,0xFF,0xC0},{0x00,0x00,0x00},
    {0x00,0x00,0x00},{0x00,0x00,0x00},
}};

/* Logo about: dấu ? */
static const Logo24 logo_about = {{
    {0x00,0x00,0x00},{0x00,0x00,0x00},
    {0x07,0xFF,0x80},{0x0F,0xFF,0xC0},{0x1C,0x01,0xE0},
    {0x18,0x00,0x60},{0x18,0x00,0x60},{0x00,0x00,0x60},
    {0x00,0x00,0x60},{0x00,0x00,0xE0},{0x00,0x01,0xC0},
    {0x00,0x07,0x80},{0x00,0x0F,0x00},{0x00,0x1E,0x00},
    {0x00,0x38,0x00},{0x00,0x30,0x00},{0x00,0x30,0x00},
    {0x00,0x30,0x00},{0x00,0x00,0x00},{0x00,0x30,0x00},
    {0x00,0x30,0x00},{0x00,0x00,0x00},
    {0x00,0x00,0x00},{0x00,0x00,0x00},
}};

/* ═══ Apps list ═══ */
static App g_apps[] = {
    { "Purrminal",  "Terminal",     1, logo_purrminal, 0 },
    { "FileMgr",    "Quan li file", 1, logo_filemgr,   0 },
    { "PawEditor",  "Soan thao",    1, logo_pawedit,   0 },
    { "Catting",    "Cai dat",      1, logo_catting,   0 },
    { "Login",      "Dang nhap",    1, logo_login,     0 },
    { "About",      "Gioi thieu",   1, logo_about,     0 },
};
static const int g_app_count = 6;


/* ═══ State ═══ */
static int g_selected = 0;
static int g_active = 0;   /* menu có đang mở không */
static int g_layout = 0;   /* 0=grid, 1=list */

/* ═══ Vẽ 1 logo 24x24 với scale 2x ═══ */
static void draw_logo(const Logo24* L, int x, int y, uint32_t color, int scale) {
    extern void fb_rect(uint32_t x, uint32_t y, uint32_t w, uint32_t h, uint32_t color);
    for (int r = 0; r < 24; r++) {
        for (int cc = 0; cc < 24; cc++) {
            int byte_idx = cc / 8;
            int bit = 7 - (cc % 8);
            int on = (L->rows[r][byte_idx] >> bit) & 1;
            if (!on) continue;
            fb_rect(x + cc*scale, y + r*scale, scale, scale, color);
        }
    }
}

/* ═══ Grid layout 3 cột × 2 hàng ═══ */
static void draw_grid(void) {
    int fw = (int)fb_width();
    int fh = (int)fb_height();

    fb_clear_all();
    fb_draw_panel();

    /* Title to */
    fb_puts_scale("FelisOS Launcher",
                  fw / 2 - 8*14*2/2, 50, 0x00FFFFFF, 0x00204A87, 2);

    int cols = 3;
    int rows = 2;
    int icon_size = 48;
    int cell_w = 240;
    int cell_h = 200;
    int start_x = (fw - cols * cell_w) / 2;
    int start_y = 130;

    for (int i = 0; i < g_app_count; i++) {
        int r = i / cols;
        int c = i % cols;
        if (r >= rows) break;

        int cx = start_x + c * cell_w + (cell_w - icon_size) / 2;
        int cy = start_y + r * cell_h;

        /* Highlight cell */
        if (i == g_selected) {
            fb_rect(cx - 40, cy - 25, cell_w - 20, cell_h - 40, 0x003366AA);
            /* Viền sáng */
            fb_rect(cx - 40, cy - 25, cell_w - 20, 3, 0x0055AAFF);
            fb_rect(cx - 40, cy + cell_h - 68, cell_w - 20, 3, 0x0055AAFF);
        }

        /* Logo */
        if (g_apps[i].has_logo) {
            draw_logo(&g_apps[i].logo, cx, cy, 0x00FFFFFF, 2);
        }

        /* Tên app — font scale 2, to rõ */
        fb_puts_scale(g_apps[i].name,
                      cx - 30, cy + icon_size + 12,
                      0x00FFFFFF,
                      i == g_selected ? 0x003366AA : 0x00204A87,
                      2);

        /* Mô tả — scale 1, nhỏ hơn */
        fb_puts_at_color(g_apps[i].desc,
                         cx - 30, cy + icon_size + 42,
                         0x00CCCCCC,
                         i == g_selected ? 0x003366AA : 0x00204A87);
    }

    /* Footer */
    fb_puts_at_color("Arrow: chon | Enter: mo | ESC: dong | Tab: doi layout",
                     fw / 2 - 260, fh - 60, 0x00FFFFFF, 0x00204A87);
}

/* ═══ List layout ═══ */
static void draw_list(void) {
    int fw = (int)fb_width();
    int fh = (int)fb_height();

    fb_clear_all();
    fb_draw_panel();

    fb_puts_scale("FelisOS Launcher",
                  fw / 2 - 8*14*2/2, 50, 0x00FFFFFF, 0x00204A87, 2);

    int start_y = 130;
    for (int i = 0; i < g_app_count; i++) {
        int y = start_y + i * 70;
        if (i == g_selected) {
            fb_rect(60, y - 10, fw - 120, 60, 0x003366AA);
            fb_rect(60, y - 10, fw - 120, 3, 0x0055AAFF);
        }
        fb_puts_scale(g_apps[i].name, 90, y, 0x00FFFFFF,
                      i == g_selected ? 0x003366AA : 0x00204A87, 2);
        fb_puts_at_color(g_apps[i].desc, 450, y + 8, 0x00CCCCCC,
                         i == g_selected ? 0x003366AA : 0x00204A87);
    }

    fb_puts_at_color("Up/Down: chon | Enter: mo | ESC: dong | Tab: doi layout",
                     fw / 2 - 260, fh - 60, 0x00FFFFFF, 0x00204A87);
}

/* ═══ Vẽ menu ═══ */
void appmenu_draw(void) {
    if (g_layout == 0) draw_grid();
    else draw_list();
}

/* ═══ Mở menu ═══ */
void appmenu_open(void) {
    g_selected = 0;
    g_active = 1;
    appmenu_draw();
}

void appmenu_close(void) {
    g_active = 0;
}

int appmenu_is_active(void) { return g_active; }

/* ═══ Xử lý phím ═══ */
int appmenu_handle_key(char c) {
    if (!g_active) return 0;

    int cols = 3;

    if (c == 27) {  /* ESC */
        appmenu_close();
        return 1;
    }
    if (c == '\t') {
        g_layout = 1 - g_layout;
        appmenu_draw();
        return 1;
    }
    if (c == '\n') {
        /* Chạy app */
        if (g_selected == 0) {
            /* Purrminal → switch TTY 1 (shell mode) */
            appmenu_close();
            tty_switch(1);
        }
        /* Các app khác chưa làm */
        return 1;
    }

    /* Arrow keys — dùng KEY_UP/DOWN/LEFT/RIGHT = 128..131 */
    unsigned char uc = (unsigned char)c;
    if (uc == 130) {  /* LEFT */
        if (g_selected > 0) g_selected--;
        appmenu_draw();
        return 1;
    }
    if (uc == 131) {  /* RIGHT */
        if (g_selected < g_app_count - 1) g_selected++;
        appmenu_draw();
        return 1;
    }
    if (uc == 128) {  /* UP */
        if (g_selected >= cols) g_selected -= cols;
        appmenu_draw();
        return 1;
    }
    if (uc == 129) {  /* DOWN */
        if (g_selected + cols < g_app_count) g_selected += cols;
        appmenu_draw();
        return 1;
    }

    return 0;
}
