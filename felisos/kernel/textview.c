/* Kitty — Text viewer */
#include <stdint.h>

extern int  fb_is_active(void);
extern uint32_t fb_width(void);
extern uint32_t fb_height(void);
extern void fb_rect(uint32_t x, uint32_t y, uint32_t w, uint32_t h, uint32_t color);
extern void fb_puts_at_color(const char* s, int x, int y, uint32_t fg, uint32_t bg);
extern void fb_puts_scale(const char* s, int x, int y, uint32_t fg, uint32_t bg, int scale);
extern void fb_cursor_forget(void);
extern void fb_clear_all(void);
extern void fb_draw_panel(void);
extern void fb_draw_dock(void);
extern const char* fs_read(const char* name, int* size_out);

#define TV_MAX_LINE 200

typedef struct {
    int x, y, w, h;
    int visible;
    char filename[64];
    char lines[64][TV_MAX_LINE];
    int line_count;
    int scroll;
    int max_rows;
} TextView;

static TextView g_tv = {0};

static void tv_load(const char* fname) {
    g_tv.line_count = 0;
    g_tv.scroll = 0;

    int i = 0;
    while (fname && fname[i] && i < 63) {
        g_tv.filename[i] = fname[i];
        i++;
    }
    g_tv.filename[i] = 0;

    int sz = 0;
    const char* data = fs_read(fname, &sz);
    if (!data || sz == 0) {
        g_tv.lines[0][0] = '(';
        g_tv.lines[0][1] = 'e';
        g_tv.lines[0][2] = 'm';
        g_tv.lines[0][3] = 'p';
        g_tv.lines[0][4] = 't';
        g_tv.lines[0][5] = 'y';
        g_tv.lines[0][6] = ')';
        g_tv.lines[0][7] = 0;
        g_tv.line_count = 1;
        return;
    }

    int li = 0, ci = 0;
    for (int k = 0; k < sz && li < 64; k++) {
        char ch = data[k];
        if (ch == '\n') {
            g_tv.lines[li][ci] = 0;
            li++; ci = 0;
        } else if (ch == '\r') {
            /* skip */
        } else {
            if (ci < TV_MAX_LINE - 1) g_tv.lines[li][ci++] = ch;
        }
    }
    if (ci > 0 && li < 64) { g_tv.lines[li][ci] = 0; li++; }
    g_tv.line_count = li > 0 ? li : 1;
}

static void tv_draw(void) {
    if (!fb_is_active() || !g_tv.visible) return;

    int x = g_tv.x, y = g_tv.y, w = g_tv.w, h = g_tv.h;

    fb_rect(x + 6, y + 6, w, h, 0x00101010);
    fb_rect(x, y, w, h, 0x001A1A1A);
    for (int gy = 0; gy < 34; gy++) {
        uint32_t col = (gy < 8) ? 0x005B9DE5 : (gy < 22 ? 0x003A6EA5 : 0x00245888);
        fb_rect(x, y + gy, w, 1, col);
    }

    fb_puts_scale(g_tv.filename, x + 14, y + 6, 0x00FFFFFF, 0x00555555, 2);

    /* 3 nút */
    fb_rect(x + w - 28, y + 8, 22, 22, 0x00CC3333);
    fb_rect(x + w - 56, y + 8, 22, 22, 0x00CCAA33);
    fb_rect(x + w - 84, y + 8, 22, 22, 0x0033AA33);

    /* Border */
    fb_rect(x, y, w, 2, 0x00BBBBBB);
    fb_rect(x, y + h - 2, w, 2, 0x00BBBBBB);
    fb_rect(x, y, 2, h, 0x00BBBBBB);
    fb_rect(x + w - 2, y, 2, h, 0x00BBBBBB);

    int cy_start = y + 44;
    int row_h = 28;   /* cao hơn */
    int rows = (h - 54) / row_h;
    g_tv.max_rows = rows;

    for (int i = 0; i < rows && (i + g_tv.scroll) < g_tv.line_count; i++) {
        int li = i + g_tv.scroll;
        int cy = cy_start + i * row_h;
        fb_puts_scale(g_tv.lines[li], x + 14, cy + 4,
                      0x00FFFFFF, 0x001A1A1A, 2);  /* scale 2 */
    }

    /* Scrollbar */
    if (g_tv.line_count > rows) {
        fb_rect(x + w - 12, cy_start, 6, rows * row_h, 0x00303030);
        int thumb_h = (rows * rows * row_h) / g_tv.line_count;
        if (thumb_h < 20) thumb_h = 20;
        int max_scroll = g_tv.line_count - rows;
        int thumb_y = cy_start;
        if (max_scroll > 0)
            thumb_y += (g_tv.scroll * (rows * row_h - thumb_h)) / max_scroll;
        fb_rect(x + w - 12, thumb_y, 6, thumb_h, 0x00888888);
    }
}

void textview_open(const char* fname) {
    int fw = (int)fb_width();
    int fh = (int)fb_height();

    g_tv.visible = 0;
    g_tv.x = 220;
    g_tv.y = 70;
    g_tv.w = fw - 240;
    g_tv.h = fh - 110;
    g_tv.visible = 1;
    g_tv.scroll = 0;

    tv_load(fname);
    tv_draw();
}

int textview_is_visible(void) { return g_tv.visible; }
void textview_redraw_public(void) { tv_draw(); }

static void tv_close_redraw(void) {
    fb_cursor_forget();
    fb_clear_all();
    fb_draw_panel();
    fb_draw_dock();
    g_tv.visible = 0;

    extern int filemgr_is_visible(void);
    extern void filemgr_open(void);
    if (filemgr_is_visible()) filemgr_open();
}

int textview_handle_key(char c) {
    if (!g_tv.visible) return 0;
    int uc = (unsigned char)c;

    if (uc == 27) { tv_close_redraw(); return 1; }
    if (uc == 128) {
        if (g_tv.scroll > 0) g_tv.scroll--;
        tv_draw(); return 1;
    }
    if (uc == 129) {
        if (g_tv.scroll < g_tv.line_count - g_tv.max_rows) g_tv.scroll++;
        tv_draw(); return 1;
    }
    return 0;
}

int textview_handle_click(int mx, int my) {
    if (!g_tv.visible) return 0;

    int x = g_tv.x, y = g_tv.y, w = g_tv.w, h = g_tv.h;

    if (mx < x || mx > x + w || my < y || my > y + h) {
        tv_close_redraw();
        return 1;
    }

    /* Title bar — 3 nút */
    if (my >= y + 2 && my <= y + 36) {
        int right = x + w;
        int dist = right - mx;

        /* X — close (8..28) */
        if (dist >= 8 && dist < 28) {
            tv_close_redraw();
            return 1;
        }
        /* - — minimize (36..56) */
        if (dist >= 36 && dist < 56) {
            tv_close_redraw();
            return 1;
        }
        /* + — maximize toggle (64..84) */
        if (dist >= 64 && dist < 84) {
            extern uint32_t fb_width(void);
            extern uint32_t fb_height(void);
            int fw = (int)fb_width();
            int fh = (int)fb_height();
            if (g_tv.x == 220) {
                /* maximize */
                g_tv.x = 140;
                g_tv.y = 32;
                g_tv.w = fw - 150;
                g_tv.h = fh - 40;
            } else {
                /* restore */
                g_tv.x = 220;
                g_tv.y = 70;
                g_tv.w = fw - 240;
                g_tv.h = fh - 110;
            }
            tv_draw();
            return 1;
        }
    }
    return 1;
}
