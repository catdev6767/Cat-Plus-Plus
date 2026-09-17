/* Kitty — Window manager + Purrminal interactive terminal */
#include <stdint.h>

extern int  fb_is_active(void);
extern uint32_t fb_width(void);
extern uint32_t fb_height(void);
extern void fb_rect(uint32_t x, uint32_t y, uint32_t w, uint32_t h, uint32_t color);
extern void fb_char_at(char ch, uint32_t x, uint32_t y, uint32_t fg, uint32_t bg);
extern void fb_puts_at_color(const char* s, int x, int y, uint32_t fg, uint32_t bg);
extern void fb_clear_all(void);
extern void fb_draw_panel(void);
extern void fb_draw_dock(void);
extern int  mouse_is_visible(void);
extern void mouse_hide(void);
extern void mouse_show(void);
extern int shell_execute(char* cmdline);
extern void (*g_out_hook)(char);
extern void cmd_clear_internal(void);
extern void cmd_help_internal(void);

static void purrminal_redraw(void);

#define WIN_CHAR_W 16
#define WIN_CHAR_H 20

typedef struct {
    int x, y, w, h;
    int norm_x, norm_y, norm_w, norm_h;  /* lưu kích thước thường để restore */
    const char* title;
    int cur_row, cur_col;
    int max_rows, max_cols;
    int active;
    int visible;
    int maximized;
} Window;

static Window g_purr = { 0 };
static char g_line[256];
static int  g_line_len = 0;

/* ═══ Vẽ khung ═══ */
void window_draw(Window* w) {
    if (!fb_is_active() || !w->visible) return;

    fb_rect(w->x + 6, w->y + 6, w->w, w->h, 0x00101010);
    fb_rect(w->x, w->y, w->w, w->h, 0x001A1A1A);
    fb_rect(w->x, w->y, w->w, 34, 0x00555555);

    /* Title scale 1.5 */
    fb_puts_at_color(w->title, w->x + 14, w->y + 9, 0x00FFFFFF, 0x00555555);

    /* Nút — to hơn, dễ click */
    fb_rect(w->x + w->w - 32, w->y + 9, 20, 20, 0x00CC3333);  /* close */
    fb_rect(w->x + w->w - 60, w->y + 9, 20, 20, 0x00CCAA33);  /* minimize */
    fb_rect(w->x + w->w - 88, w->y + 9, 20, 20, 0x0033AA33);  /* maximize */

    /* Border — dày 2px */
    fb_rect(w->x, w->y, w->w, 2, 0x00BBBBBB);
    fb_rect(w->x, w->y + w->h - 2, w->w, 2, 0x00BBBBBB);
    fb_rect(w->x, w->y, 2, w->h, 0x00BBBBBB);
    fb_rect(w->x + w->w - 2, w->y, 2, w->h, 0x00BBBBBB);
    fb_rect(w->x, w->y + 32, w->w, 2, 0x00333333);
}

/* ═══ In ký tự ═══ */
void window_putc(Window* w, char c) {
    if (!fb_is_active() || !w->visible) return;

    int cx = w->x + 12;
    int cy = w->y + 44;

    if (c == '\n') {
        w->cur_col = 0;
        w->cur_row++;
    } else if (c == '\r') {
        w->cur_col = 0;
    } else if (c == '\b') {
        if (w->cur_col > 0) {
            w->cur_col--;
            fb_char_at(' ',
                cx + w->cur_col * WIN_CHAR_W,
                cy + w->cur_row * WIN_CHAR_H,
                0x00FFFFFF, 0x001A1A1A);
        }
    } else if (c >= 32 && c < 127) {
        fb_char_at(c,
            cx + w->cur_col * WIN_CHAR_W,
            cy + w->cur_row * WIN_CHAR_H,
            0x00FFFFFF, 0x001A1A1A);
        w->cur_col++;
        if (w->cur_col >= w->max_cols) {
            w->cur_col = 0;
            w->cur_row++;
        }
    }

    if (w->cur_row >= w->max_rows) {
        fb_rect(cx - 4, cy - 4, w->w - 12, w->h - 48, 0x001A1A1A);
        w->cur_row = 0;
        w->cur_col = 0;
    }
}

void window_puts(Window* w, const char* s) {
    while (s && *s) window_putc(w, *s++);
}

void window_clear(Window* w) {
    if (!fb_is_active() || !w->visible) return;
    fb_rect(w->x + 4, w->y + 38, w->w - 8, w->h - 44, 0x001A1A1A);
    w->cur_row = 0;
    w->cur_col = 0;
}

/* ═══ Prompt ═══ */
static void purr_prompt(void) {
    window_puts(&g_purr, "purr:/$ ");
}

/* ═══ Output hook — ghi vào window ═══ */
static void win_hook(char c) {
    window_putc(&g_purr, c);
}

/* ═══ Chạy lệnh từ Purrminal ═══ */
static void purr_exec(const char* cmd) {
    if (!cmd || !*cmd) {
        purr_prompt();
        return;
    }

    /* Copy vì shell_execute modify */
    static char buf[256];
    int i = 0;
    while (cmd[i] && i < 255) { buf[i] = cmd[i]; i++; }
    buf[i] = 0;

    /* Handle clear riêng */
    if (i == 5 && buf[0]=='c'&&buf[1]=='l'&&buf[2]=='e'&&buf[3]=='a'&&buf[4]=='r') {
        window_clear(&g_purr);
        purr_prompt();
        return;
    }

    /* Redirect output vào window */
    g_out_hook = win_hook;
    int rc = shell_execute(buf);
    g_out_hook = 0;
    (void)rc;

    purr_prompt();
}

/* ═══ Keyboard input ═══ */
int purrminal_handle_key(char c) {
    if (!g_purr.active || !g_purr.visible) return 0;

    if (c == '\n') {
        g_line[g_line_len] = 0;
        window_putc(&g_purr, '\n');
        purr_exec(g_line);
        g_line_len = 0;
    } else if (c == '\b') {
        if (g_line_len > 0) {
            g_line_len--;
            window_putc(&g_purr, '\b');
        }
    } else if (c >= 32 && c < 127) {
        if (g_line_len < 255) {
            g_line[g_line_len++] = c;
            window_putc(&g_purr, c);
        }
    }
    return 1;
}

/* ═══ Click ═══ */
extern void serial_print_str(const char* s);

int purrminal_handle_click(int mx, int my) {
    Window* w = &g_purr;
    if (!w->visible) return 0;

    /* Trong title bar? */
    if (my >= w->y + 4 && my <= w->y + 30) {
        /* Close */
        if (mx >= w->x + w->w - 32 && mx <= w->x + w->w - 12) {
            w->visible = 0;
            w->active = 0;
            return 1;
        }
        /* Minimize */
        if (mx >= w->x + w->w - 60 && mx <= w->x + w->w - 40) {
            w->visible = 0;
            w->active = 0;
            return 1;
        }
        /* Maximize */
        if (mx >= w->x + w->w - 88 && mx <= w->x + w->w - 68) {
            if (w->maximized) {
                w->x = w->norm_x; w->y = w->norm_y;
                w->w = w->norm_w; w->h = w->norm_h;
                w->maximized = 0;
            } else {
                w->norm_x = w->x; w->norm_y = w->y;
                w->norm_w = w->w; w->norm_h = w->h;
                int fw = (int)fb_width(), fh = (int)fb_height();
                w->x = 70; w->y = 32;
                w->w = fw - 80; w->h = fh - 50;
                w->maximized = 1;
            }
            w->max_cols = (w->w - 24) / WIN_CHAR_W;
            w->max_rows = (w->h - 56) / WIN_CHAR_H;
            window_draw(w);
            window_clear(w);
            window_puts(w, "FelisOS Purrminal v0.2\n");
            purr_prompt();
            return 1;
        }
    }

    /* Click trong body → focus */
    if (mx >= w->x && mx <= w->x + w->w &&
        my >= w->y && my <= w->y + w->h) {
        w->active = 1;
        return 1;
    }

    return 0;
}

/* ═══ Init ═══ */
/* Redraw toàn desktop + cửa sổ (gọi khi resize) */
static void purrminal_redraw(void) {
    int mvis = mouse_is_visible();
    if (mvis) mouse_hide();

    fb_clear_all();
    fb_draw_panel();
    fb_draw_dock();

    window_draw(&g_purr);
    window_clear(&g_purr);

    window_puts(&g_purr, "FelisOS Purrminal v0.2\n");
    purr_prompt();

    if (mvis) mouse_show();
}

void purrminal_open(void) {
    int fw = (int)fb_width();
    int fh = (int)fb_height();

    g_purr.x = fw / 4;
    g_purr.y = 80;
    g_purr.w = fw / 2;
    g_purr.h = fh - 200;
    g_purr.norm_x = g_purr.x;
    g_purr.norm_y = g_purr.y;
    g_purr.norm_w = g_purr.w;
    g_purr.norm_h = g_purr.h;
    g_purr.title = "Purrminal";
    g_purr.cur_row = 0;
    g_purr.cur_col = 0;
    g_purr.max_cols = (g_purr.w - 24) / WIN_CHAR_W;
    g_purr.max_rows = (g_purr.h - 56) / WIN_CHAR_H;
    g_purr.active = 1;
    g_purr.visible = 1;
    g_purr.maximized = 0;

    window_draw(&g_purr);
    window_clear(&g_purr);

    window_puts(&g_purr, "FelisOS Purrminal v0.2\n");
    window_puts(&g_purr, "Click nut X de dong, - de thu nho, + de phong to\n");
    window_puts(&g_purr, "Go 'help' de xem lenh\n\n");
    purr_prompt();
}
