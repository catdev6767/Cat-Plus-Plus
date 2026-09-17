/* Kitty — Window manager đơn giản + Purrminal window */
#include <stdint.h>

extern int  fb_is_active(void);
extern uint32_t fb_width(void);
extern uint32_t fb_height(void);
extern void fb_rect(uint32_t x, uint32_t y, uint32_t w, uint32_t h, uint32_t color);
extern void fb_putc(char c);
extern void fb_puts_at_color(const char* s, int x, int y, uint32_t fg, uint32_t bg);
extern void fb_char_at(char ch, uint32_t x, uint32_t y, uint32_t fg, uint32_t bg);

#define WIN_MAX_ROWS 20
#define WIN_MAX_COLS 70

typedef struct {
    int x, y, w, h;
    const char* title;
    int cur_row, cur_col;
    int active;
    int visible;
} Window;

static Window g_purr = { 0 };

/* ═══ Vẽ khung window ═══ */
void window_draw(Window* w) {
    if (!fb_is_active() || !w->visible) return;

    /* Shadow */
    fb_rect(w->x + 6, w->y + 6, w->w, w->h, 0x00101010);

    /* Body — đen */
    fb_rect(w->x, w->y, w->w, w->h, 0x001A1A1A);

    /* Title bar — xám đậm */
    fb_rect(w->x, w->y, w->w, 22, 0x004A4A4A);

    /* Title text */
    fb_puts_at_color(w->title, w->x + 10, w->y + 4, 0x00FFFFFF, 0x004A4A4A);

    /* Nút close — đỏ */
    fb_rect(w->x + w->w - 22, w->y + 5, 14, 14, 0x00CC3333);
    /* Nút minimize — vàng */
    fb_rect(w->x + w->w - 42, w->y + 5, 14, 14, 0x00CCAA33);
    /* Nút maximize — xanh */
    fb_rect(w->x + w->w - 62, w->y + 5, 14, 14, 0x0033AA33);

    /* Border */
    fb_rect(w->x, w->y, w->w, 1, 0x00888888);
    fb_rect(w->x, w->y + w->h - 1, w->w, 1, 0x00888888);
    fb_rect(w->x, w->y, 1, w->h, 0x00888888);
    fb_rect(w->x + w->w - 1, w->y, 1, w->h, 0x00888888);

    /* Viền dưới title bar */
    fb_rect(w->x, w->y + 22, w->w, 1, 0x00222222);
}

/* ═══ Ghi ký tự vào window content area ═══ */
void window_putc(Window* w, char c) {
    if (!fb_is_active() || !w->visible) return;

    int content_x = w->x + 6;
    int content_y = w->y + 26;
    int char_w = 8;
    int char_h = 10;
    int max_cols = (w->w - 12) / char_w;
    int max_rows = (w->h - 30) / char_h;

    if (max_cols > WIN_MAX_COLS) max_cols = WIN_MAX_COLS;
    if (max_rows > WIN_MAX_ROWS) max_rows = WIN_MAX_ROWS;

    if (c == '\n') {
        w->cur_col = 0;
        w->cur_row++;
    } else if (c == '\r') {
        w->cur_col = 0;
    } else if (c == '\b') {
        if (w->cur_col > 0) {
            w->cur_col--;
            fb_char_at(' ', content_x + w->cur_col * char_w,
                       content_y + w->cur_row * char_h,
                       0x00FFFFFF, 0x001A1A1A);
        }
    } else if (c >= 32 && c < 127) {
        fb_char_at(c,
                   content_x + w->cur_col * char_w,
                   content_y + w->cur_row * char_h,
                   0x00FFFFFF, 0x001A1A1A);
        w->cur_col++;
        if (w->cur_col >= max_cols) {
            w->cur_col = 0;
            w->cur_row++;
        }
    }

    /* Scroll nếu cần — xóa hết + vẽ lại từ đầu là đơn giản nhất,
       nhưng chưa có buffer, nên tạm bỏ qua */
    if (w->cur_row >= max_rows) {
        /* Xóa content area + reset */
        fb_rect(content_x - 2, content_y - 2,
                w->w - 8, w->h - 28, 0x001A1A1A);
        w->cur_row = 0;
        w->cur_col = 0;
    }
}

/* ═══ Xóa content ═══ */
void window_clear(Window* w) {
    if (!fb_is_active() || !w->visible) return;
    int content_x = w->x + 6;
    int content_y = w->y + 26;
    fb_rect(content_x - 4, content_y - 4,
            w->w - 8, w->h - 28, 0x001A1A1A);
    w->cur_row = 0;
    w->cur_col = 0;
}

/* ═══ Init Purrminal window ═══ */
Window* purrminal_get(void) { return &g_purr; }

void purrminal_open(void) {
    int fw = (int)fb_width();
    int fh = (int)fb_height();

    g_purr.x = fw / 4;
    g_purr.y = 80;
    g_purr.w = fw / 2;
    g_purr.h = fh - 200;
    g_purr.title = "Purrminal";
    g_purr.cur_row = 0;
    g_purr.cur_col = 0;
    g_purr.active = 1;
    g_purr.visible = 1;

    window_draw(&g_purr);
    window_clear(&g_purr);

    fb_puts_at_color("FelisOS Purrminal v0.1",
                     g_purr.x + 6, g_purr.y + 26, 0x00AAFFAA, 0x001A1A1A);
    g_purr.cur_row = 1;
    g_purr.cur_col = 0;
    fb_puts_at_color("Go 'help' de bat dau.",
                     g_purr.x + 6, g_purr.y + 36, 0x00CCCCCC, 0x001A1A1A);
    g_purr.cur_row = 2;
    g_purr.cur_col = 0;
    fb_puts_at_color("purr:/$ ",
                     g_purr.x + 6, g_purr.y + 46, 0x00FFAA00, 0x001A1A1A);
    g_purr.cur_col = 8;
}
