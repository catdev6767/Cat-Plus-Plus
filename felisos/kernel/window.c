/* Kitty — Window manager (single-window mode) */
#include <stdint.h>

extern int  fb_is_active(void);
extern uint32_t fb_width(void);
extern uint32_t fb_height(void);
extern void fb_rect(uint32_t x, uint32_t y, uint32_t w, uint32_t h, uint32_t color);
extern void fb_puts_at_color(const char* s, int x, int y, uint32_t fg, uint32_t bg);
extern void fb_char_at(char ch, uint32_t x, uint32_t y, uint32_t fg, uint32_t bg);
extern void fb_char_at_scale_xy(char ch, int x, int y, uint32_t fg, uint32_t bg, int sx, int sy);
extern void fb_cursor_forget(void);
extern void fb_draw_wallpaper(void);
extern void fb_draw_panel(void);
extern void fb_draw_dock(void);
extern int  fb_start_menu_click(int mx, int my);
extern void fb_start_menu_toggle(void);
extern int  fb_start_menu_is_open(void);
extern int  shell_execute(char* cmdline);
extern void (*g_out_hook)(char);
extern int  fs_create(const char* name, int is_dir);

extern int  filemgr_is_visible(void);
extern void filemgr_open(void);
extern void filemgr_close(void);
extern int  filemgr_handle_click(int mx, int my);
extern int  filemgr_handle_key(char c);

extern int  pawedit_is_visible(void);
extern void pawedit_open(const char* fname);
extern void pawedit_close(void);
extern int  pawedit_handle_click(int mx, int my);
extern int  pawedit_handle_key(char c);

extern int  textview_is_visible(void);
extern int  textview_handle_click(int mx, int my);
extern int  textview_handle_key(char c);

#define WIN_CHAR_W 16
#define WIN_CHAR_H 18

typedef struct {
    int x, y, w, h;
    const char* title;
    int cur_row, cur_col;
    int max_rows, max_cols;
    int visible;
} Window;

/* ═══ Purrminal ═══ */
static Window g_purr = {0};
static char   g_line[256];
static int    g_line_len = 0;

/* ═══ Coming ═══ */
static Window g_coming = {0};

/* ═══ Redraw desktop + windows ═══ */
void redraw_windows_after_menu(void);

static void redraw_desktop(void) {
    fb_cursor_forget();
    fb_draw_wallpaper();
    fb_draw_panel();
    fb_draw_dock();
    /* Vẽ window hiện tại lên trên */
    if (g_purr.visible) {
        extern void window_draw(Window*);
        extern void window_clear(Window*);
        extern void window_puts(Window*, const char*);
        window_draw(&g_purr);
        window_clear(&g_purr);
        window_puts(&g_purr, "FelisOS Purrminal v0.3\n");
        window_puts(&g_purr, "Go 'help' de xem lenh\n\n");
        window_puts(&g_purr, "kitty@felis:/$ ");
    } else if (filemgr_is_visible()) {
        /* FileMgr tự vẽ trong filemgr_open — gọi lại */
        extern void filemgr_redraw_public(void);
        filemgr_redraw_public();
    } else if (pawedit_is_visible()) {
        extern void pawedit_redraw_public(void);
        pawedit_redraw_public();
    }
}

/* Public — gọi từ keyboard khi đóng menu */
void redraw_windows_after_menu(void) {
    redraw_desktop();
}


/* ═══ Close all windows ═══ */
static void close_all_windows(void) {
    g_purr.visible = 0;
    g_coming.visible = 0;
    /* Các app khác tự đóng khi mở cái mới */
    if (filemgr_is_visible()) filemgr_close();
    if (pawedit_is_visible()) pawedit_close();
}

/* ═══ Window basic ═══ */
void window_draw(Window* w) {
    if (!fb_is_active() || !w->visible) return;
    fb_rect(w->x + 6, w->y + 6, w->w, w->h, 0x00101010);
    fb_rect(w->x, w->y, w->w, w->h, 0x00101010);
    for (int gy = 0; gy < 30; gy++) {
        uint32_t col = (gy < 8) ? 0x005B9DE5 : (gy < 22 ? 0x003A6EA5 : 0x00245888);
        fb_rect(w->x, w->y + gy, w->w, 1, col);
    }
    fb_puts_at_color(w->title, w->x + 14, w->y + 9, 0x00FFFFFF, 0x003A6EA5);
    fb_rect(w->x + w->w - 28, w->y + 8, 20, 20, 0x00C0392B);
    fb_rect(w->x + w->w - 56, w->y + 8, 20, 20, 0x00E8A040);
    fb_rect(w->x + w->w - 84, w->y + 8, 20, 20, 0x0038A03A);
    fb_rect(w->x, w->y, w->w, 2, 0x00BBBBBB);
    fb_rect(w->x, w->y + w->h - 2, w->w, 2, 0x00BBBBBB);
    fb_rect(w->x, w->y, 2, w->h, 0x00BBBBBB);
    fb_rect(w->x + w->w - 2, w->y, 2, w->h, 0x00BBBBBB);
}

void window_putc(Window* w, char c) {
    if (!fb_is_active() || !w->visible) return;
    int cx = w->x + 12;
    int cy = w->y + 42;

    if (c == '\n') {
        w->cur_col = 0;
        w->cur_row++;
    } else if (c == '\r') {
        w->cur_col = 0;
    } else if (c == '\b') {
        if (w->cur_col > 0) {
            w->cur_col--;
            fb_rect(cx + w->cur_col * WIN_CHAR_W, cy + w->cur_row * WIN_CHAR_H,
                    WIN_CHAR_W, WIN_CHAR_H, 0x00101010);
        }
    } else if (c >= 32 && c < 127) {
        fb_char_at_scale_xy(c, cx + w->cur_col * WIN_CHAR_W,
                            cy + w->cur_row * WIN_CHAR_H,
                            0x00FFFFFF, 0x00101010, 2, 2);
        w->cur_col++;
        if (w->cur_col >= w->max_cols) {
            w->cur_col = 0;
            w->cur_row++;
        }
    }
    if (w->cur_row >= w->max_rows) {
        fb_rect(w->x + 4, w->y + 38, w->w - 8, w->h - 42, 0x00101010);
        w->cur_row = 0;
        w->cur_col = 0;
    }
}

void window_puts(Window* w, const char* s) {
    while (s && *s) window_putc(w, *s++);
}

void window_clear(Window* w) {
    if (!fb_is_active() || !w->visible) return;
    fb_rect(w->x + 4, w->y + 38, w->w - 8, w->h - 42, 0x00101010);
    w->cur_row = 0;
    w->cur_col = 0;
}

/* ═══ Purrminal ═══ */
static void purr_hook(char c) { window_putc(&g_purr, c); }

void purrminal_open(void) {
    int fw = (int)fb_width();
    int fh = (int)fb_height();

    close_all_windows();

    g_purr.w = fw - 200;
    g_purr.h = fh - 120;
    g_purr.x = (fw - g_purr.w) / 2;
    g_purr.y = (fh - 32 - g_purr.h) / 2;
    g_purr.title = "Purrminal";
    g_purr.cur_row = 0;
    g_purr.cur_col = 0;
    g_purr.max_cols = (g_purr.w - 20) / WIN_CHAR_W;
    g_purr.max_rows = (g_purr.h - 50) / WIN_CHAR_H;
    g_purr.visible = 1;

    redraw_desktop();
    g_line_len = 0;
}

int purrminal_is_visible(void) { return g_purr.visible; }
void purrminal_redraw_public(void) { redraw_desktop(); }

static void purr_prompt(void) {
    window_puts(&g_purr, "kitty@felis:/$ ");
}

static void purr_exec(const char* cmd) {
    if (!cmd || !*cmd) { purr_prompt(); return; }
    static char buf[256];
    int i = 0;
    while (cmd[i] && i < 255) { buf[i] = cmd[i]; i++; }
    buf[i] = 0;
    if (i == 5 && buf[0]=='c'&&buf[1]=='l'&&buf[2]=='e'&&buf[3]=='a'&&buf[4]=='r') {
        window_clear(&g_purr);
        purr_prompt();
        return;
    }
    g_out_hook = purr_hook;
    shell_execute(buf);
    g_out_hook = 0;
    purr_prompt();
}

int purrminal_handle_key(char c) {
    if (!g_purr.visible) return 0;
    if (c == '\n') {
        g_line[g_line_len] = 0;
        window_putc(&g_purr, '\n');
        purr_exec(g_line);
        g_line_len = 0;
    } else if (c == '\b') {
        if (g_line_len > 0) { g_line_len--; window_putc(&g_purr, '\b'); }
    } else if (c >= 32 && c < 127) {
        if (g_line_len < 255) {
            g_line[g_line_len++] = c;
            window_putc(&g_purr, c);
        }
    }
    return 1;
}

/* ═══ Coming Soon ═══ */
void coming_soon_open(const char* name) {
    int fw = (int)fb_width();
    int fh = (int)fb_height();

    close_all_windows();

    g_coming.x = fw / 2 - 180;
    g_coming.y = fh / 2 - 80;
    g_coming.w = 360;
    g_coming.h = 180;
    g_coming.title = name;
    g_coming.visible = 1;

    redraw_desktop();
    /* Vẽ coming lên trên */
    window_draw(&g_coming);
    fb_rect(g_coming.x + 4, g_coming.y + 38, g_coming.w - 8, g_coming.h - 42, 0x00101010);
    fb_puts_at_color("Coming soon...", g_coming.x + 30, g_coming.y + 80,
                     0x00FFFFFF, 0x00101010);
    fb_puts_at_color("Ung dung nay chua lam.", g_coming.x + 30, g_coming.y + 110,
                     0x00CCCCCC, 0x00101010);
    fb_puts_at_color("Click X de dong.", g_coming.x + 30, g_coming.y + 140,
                     0x00CCCCCC, 0x00101010);
}

int coming_soon_visible(void) { return g_coming.visible; }

/* ═══ Main click router ═══ */
int purrminal_handle_click(int mx, int my) {
    int fh = (int)fb_height();

    /* 1. Start menu */
    if (fb_start_menu_is_open()) {
        int was_clicked = fb_start_menu_click(mx, my);
        if (was_clicked) return 1;
        /* Click ngoài menu → đóng */
        fb_start_menu_toggle();
        redraw_desktop();
        return 1;
    }

    /* 2. Start button */
    int ty = fh - 32;
    if (mx >= 4 && mx <= 104 && my >= ty + 3 && my <= ty + 29) {
        fb_start_menu_toggle();
        /* Vẽ menu lên trên desktop hiện tại */
        extern void fb_draw_start_menu(void);
        if (fb_start_menu_is_open()) fb_draw_start_menu();
        return 1;
    }

    /* 3. Taskbar buttons */
    if (my >= ty + 2) {
        int bx = 112;
        int visible[] = { purrminal_is_visible(), filemgr_is_visible(), pawedit_is_visible() };
        for (int i = 0; i < 3; i++) {
            if (!visible[i]) continue;
            if (mx >= bx && mx <= bx + 100) return 1;
            bx += 104;
        }
        return 0;
    }

    /* 4. Coming soon */
    if (g_coming.visible) {
        int cx0 = g_coming.x, cy0 = g_coming.y;
        int cw0 = g_coming.w;
        if (mx >= cx0 && mx <= cx0 + cw0 && my >= cy0 && my <= cy0 + 36) {
            int dist = (cx0 + cw0) - mx;
            if (dist >= 8 && dist < 28) {
                g_coming.visible = 0;
                redraw_desktop();
                return 1;
            }
        }
        return 1;
    }

    /* 5. App windows */
    if (filemgr_is_visible()) { filemgr_handle_click(mx, my); return 1; }
    if (pawedit_is_visible()) { pawedit_handle_click(mx, my); return 1; }
    if (textview_is_visible()) { textview_handle_click(mx, my); return 1; }

    /* 6. Purrminal title bar */
    Window* w = &g_purr;
    if (!w->visible) return 0;
    if (my >= w->y + 2 && my <= w->y + 32) {
        int right = w->x + w->w;
        int dist = right - mx;
        if (dist >= 8 && dist < 28) { g_purr.visible = 0; redraw_desktop(); return 1; }
        if (dist >= 36 && dist < 56) { g_purr.visible = 0; redraw_desktop(); return 1; }
        if (dist >= 64 && dist < 84) { /* maximize — bỏ qua */ return 1; }
    }
    return 1;
}
