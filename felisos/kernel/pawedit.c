/* Kitty — PawEditor text editor */
#include <stdint.h>

extern int  fb_is_active(void);
extern uint32_t fb_width(void);
extern uint32_t fb_height(void);
extern void fb_rect(uint32_t x, uint32_t y, uint32_t w, uint32_t h, uint32_t color);
extern void fb_puts_at_color(const char* s, int x, int y, uint32_t fg, uint32_t bg);
extern void fb_puts_scale(const char* s, int x, int y, uint32_t fg, uint32_t bg, int scale);
extern void fb_puts_scale_xy(const char* s, int x, int y, uint32_t fg, uint32_t bg, int sx, int sy);
extern void fb_puts_scale_xy(const char* s, int x, int y, uint32_t fg, uint32_t bg, int sx, int sy);
extern void fb_char_at(char ch, uint32_t x, uint32_t y, uint32_t fg, uint32_t bg);
extern void fb_cursor_forget(void);
extern void fb_clear_all(void);
extern void fb_draw_panel(void);
extern void fb_draw_dock(void);
extern const char* fs_read(const char* name, int* size_out);
extern int fs_write(const char* name, const char* data, int size);

#define PE_MAX_LINE 80
#define PE_MAX_ROWS 64

typedef struct {
    int x, y, w, h;
    int visible;
    char filename[64];
    char lines[PE_MAX_ROWS][PE_MAX_LINE];
    int line_lens[PE_MAX_ROWS];
    int line_count;
    int cur_row;
    int cur_col;
    int scroll;
    int max_visible_rows;
    int dirty;
    int mode;          /* 0=edit, 1=save_as, 2=exit_confirm */
    char prompt[64];   /* tên file đang nhập */
    int prompt_len;
} PawEditor;

static PawEditor g_pe = {0};

/* ═══ Load ═══ */
static void pe_load(const char* fname) {
    g_pe.line_count = 0;
    g_pe.cur_row = 0;
    g_pe.cur_col = 0;
    g_pe.scroll = 0;
    g_pe.dirty = 0;

    int i = 0;
    while (fname && fname[i] && i < 63) { g_pe.filename[i] = fname[i]; i++; }
    g_pe.filename[i] = 0;

    int sz = 0;
    const char* data = fs_read(fname, &sz);
    if (!data || sz == 0) {
        g_pe.lines[0][0] = 0;
        g_pe.line_lens[0] = 0;
        g_pe.line_count = 1;
        return;
    }

    int li = 0, ci = 0;
    for (int k = 0; k < sz && li < PE_MAX_ROWS; k++) {
        char ch = data[k];
        if (ch == '\n') {
            g_pe.lines[li][ci] = 0;
            g_pe.line_lens[li] = ci;
            li++; ci = 0;
        } else if (ch == '\r') {
            /* skip */
        } else {
            if (ci < PE_MAX_LINE - 1) g_pe.lines[li][ci++] = ch;
        }
    }
    if (ci > 0 && li < PE_MAX_ROWS) {
        g_pe.lines[li][ci] = 0;
        g_pe.line_lens[li] = ci;
        li++;
    }
    g_pe.line_count = li > 0 ? li : 1;
    if (g_pe.line_count == 0) g_pe.line_count = 1;
}

/* ═══ Save ═══ */
static void pe_save(void) {
    static char buf[64 * 100];
    int o = 0;
    for (int i = 0; i < g_pe.line_count && o < (int)sizeof(buf) - 2; i++) {
        for (int j = 0; j < g_pe.line_lens[i] && o < (int)sizeof(buf) - 2; j++) {
            buf[o++] = g_pe.lines[i][j];
        }
        buf[o++] = '\n';
    }
    buf[o] = 0;
    fs_write(g_pe.filename, buf, o);
    g_pe.dirty = 0;
}

/* ═══ Draw ═══ */
static void pe_draw(void) {
    if (!fb_is_active() || !g_pe.visible) return;

    int x = g_pe.x, y = g_pe.y, w = g_pe.w, h = g_pe.h;

    /* Shadow + body */
    fb_rect(x + 6, y + 6, w, h, 0x00101010);
    fb_rect(x, y, w, h, 0x00101010);
    for (int gy = 0; gy < 34; gy++) {
        uint32_t col = (gy < 8) ? 0x005B9DE5 : (gy < 22 ? 0x003A6EA5 : 0x00245888);
        fb_rect(x, y + gy, w, 1, col);
    }

    /* Title + filename + dirty */
    char title[80];
    int o = 0;
    const char* p = g_pe.filename;
    while (*p && o < 70) title[o++] = *p++;
    if (g_pe.dirty && o < 72) { title[o++] = ' '; title[o++] = '*'; }
    title[o] = 0;
    fb_puts_scale_xy(title, x + 14, y + 8, 0x00FFFFFF, 0x00555555, 1, 2);

    /* 3 nút */
    fb_rect(x + w - 28, y + 8, 22, 22, 0x00CC3333);
    fb_rect(x + w - 56, y + 8, 22, 22, 0x00CCAA33);
    fb_rect(x + w - 84, y + 8, 22, 22, 0x0033AA33);

    /* Border */
    fb_rect(x, y, w, 2, 0x00BBBBBB);
    fb_rect(x, y + h - 2, w, 2, 0x00BBBBBB);
    fb_rect(x, y, 2, h, 0x00BBBBBB);
    fb_rect(x + w - 2, y, 2, h, 0x00BBBBBB);

    /* Content area */
    int cx_start = x + 44;
    int cy_start = y + 48;
    int row_h = 22;
    int rows = (h - 60) / row_h;
    g_pe.max_visible_rows = rows;

    /* Auto scroll */
    if (g_pe.cur_row < g_pe.scroll) g_pe.scroll = g_pe.cur_row;
    if (g_pe.cur_row >= g_pe.scroll + rows) g_pe.scroll = g_pe.cur_row - rows + 1;

    for (int i = 0; i < rows && (i + g_pe.scroll) < g_pe.line_count; i++) {
        int li = i + g_pe.scroll;
        int cy = cy_start + i * row_h;

        /* Hiển thị số dòng */
        char ln[8]; int lo = 0;
        int n = li + 1;
        if (n >= 100) ln[lo++] = '0' + (n/100)%10;
        if (n >= 10)  ln[lo++] = '0' + (n/10)%10;
        ln[lo++] = '0' + n%10;
        ln[lo] = 0;
        fb_puts_at_color(ln, x + 6, cy + 8, 0x00AAAAAA, 0x00101010);

        /* Vạch phân cách số dòng | nội dung */
        fb_rect(x + 36, cy, 1, row_h, 0x00333333);
        /* Nội dung dòng — scale 2 */
        fb_puts_scale_xy(g_pe.lines[li], cx_start, cy + 6, 0x00FFFFFF, 0x00101010, 1, 2);
    }

    /* Nếu vùng edit chưa vẽ dòng (dòng mới) — vẫn vẽ cursor */
    for (int i = g_pe.line_count - g_pe.scroll; i < rows && i >= 0; i++) {
        int cy = cy_start + i * row_h;
        fb_rect(x + 36, cy, 1, row_h, 0x00333333);
    }

    /* Cursor */
    if (g_pe.cur_row >= g_pe.scroll && g_pe.cur_row < g_pe.scroll + rows) {
        int vy = cy_start + (g_pe.cur_row - g_pe.scroll) * row_h + 6;
        int vx = cx_start + g_pe.cur_col * 8;
        /* Vẽ dấu gạch dưới vàng sáng */
        fb_rect(vx, vy + 17, 8, 3, 0x00FFDD00);
    }

        /* Status bar — WinXP style gọn */
    int sy = y + h - 46;
    fb_rect(x + 2, sy, w - 4, 44, 0x00ECE9D8);

    /* Dòng 1: Ln, Col */
    char st[32]; int oo = 0;
    st[oo++]='L'; st[oo++]='n'; st[oo++]=' ';
    int r = g_pe.cur_row + 1;
    if (r >= 10) st[oo++] = '0' + (r/10)%10;
    st[oo++] = '0' + r%10;
    st[oo++] = ','; st[oo++]=' ';
    int col = g_pe.cur_col + 1;
    if (col >= 10) st[oo++] = '0' + (col/10)%10;
    st[oo++] = '0' + col%10;
    st[oo] = 0;
    fb_puts_at_color(st, x + 8, sy + 4, 0x00000000, 0x00ECE9D8);

    /* Shortcut bên phải dòng 1 */
    const char* hint = "^S:Luu ^O:LuuTen ^X:Thoat";
    int hl = 0; while (hint[hl]) hl++;
    fb_puts_at_color(hint, x + w - hl * 8 - 12, sy + 4, 0x00000000, 0x00ECE9D8);

    /* Dòng 2: prompt nếu có */
    if (g_pe.mode == 1) {
        fb_rect(x + 2, sy + 22, w - 4, 22, 0x003A6EA5);
        fb_puts_at_color("File Name: ", x + 8, sy + 26, 0x00FFFFFF, 0x003A6EA5);
        int px = x + 8 + 11 * 8;
        for (int i = 0; i < g_pe.prompt_len; i++) {
            extern void fb_char_at(char ch, uint32_t x, uint32_t y,
                                    uint32_t fg, uint32_t bg);
            fb_char_at(g_pe.prompt[i], px + i * 8, sy + 26, 0x00FFFFFF, 0x003A6EA5);
        }
    } else if (g_pe.mode == 2) {
        fb_rect(x + 2, sy + 22, w - 4, 22, 0x00C00000);
        fb_puts_at_color("Luu thay doi? (y/n/c)", x + 8, sy + 26,
                         0x00FFFFFF, 0x00C00000);
    }

}

/* ═══ Open ═══ */
void pawedit_open(const char* fname) {
    int fw = (int)fb_width();
    int fh = (int)fb_height();

    g_pe.x = 180;
    g_pe.y = 50;
    g_pe.w = fw - 200;
    g_pe.h = fh - 90;
    g_pe.visible = 1;

    pe_load(fname);
    pe_draw();
}

int pawedit_is_visible(void) { return g_pe.visible; }
void pawedit_close(void) { g_pe.visible = 0; }
void pawedit_redraw_public(void) { pe_draw(); }

static void pe_close_redraw(void) {
    fb_cursor_forget();
    fb_clear_all();
    fb_draw_panel();
    fb_draw_dock();
    g_pe.visible = 0;

    extern int filemgr_is_visible(void);
    extern void filemgr_open(void);
    if (filemgr_is_visible()) filemgr_open();
}

/* ═══ Key ═══ */
int pawedit_handle_key(char c) {
    if (!g_pe.visible) return 0;
    int uc = (unsigned char)c;

    /* ESC — thoát, hỏi lưu nếu dirty */
    if (uc == 27) {
        if (g_pe.dirty) {
            g_pe.mode = 2;
            pe_draw();
        } else {
            pe_close_redraw();
        }
        return 1;
    }

    /* Nếu đang ở prompt mode — xử lý trước */
    if (g_pe.mode == 1) {
        /* Save As prompt */
        if (uc == 27) {  /* ESC — cancel */
            g_pe.mode = 0;
            pe_draw();
            return 1;
        }
        if (uc == 10 || uc == 13) {  /* Enter — confirm */
            if (g_pe.prompt_len > 0) {
                /* Đổi tên file */
                int i = 0;
                while (i < g_pe.prompt_len && i < 63) {
                    g_pe.filename[i] = g_pe.prompt[i];
                    i++;
                }
                g_pe.filename[i] = 0;
                pe_save();
            }
            g_pe.mode = 0;
            pe_draw();
            return 1;
        }
        if (uc == 8) {  /* Backspace */
            if (g_pe.prompt_len > 0) {
                g_pe.prompt_len--;
                pe_draw();
            }
            return 1;
        }
        if (uc >= 32 && uc < 127) {
            if (g_pe.prompt_len < 63) {
                g_pe.prompt[g_pe.prompt_len++] = c;
                pe_draw();
            }
            return 1;
        }
        return 1;
    }

    if (g_pe.mode == 2) {
        /* Exit confirm */
        if (uc == 'y' || uc == 'Y') {
            pe_save();
            pe_close_redraw();
            return 1;
        }
        if (uc == 'n' || uc == 'N') {
            g_pe.mode = 0;
            pe_close_redraw();
            return 1;
        }
        if (uc == 27 || uc == 'c' || uc == 'C') {
            g_pe.mode = 0;
            pe_draw();
            return 1;
        }
        return 1;
    }

    /* Ctrl+S = 0x13 — save nhanh */
    if (uc == 0x13) { pe_save(); pe_draw(); return 1; }

    /* Ctrl+O = 0x0F — Save As */
    if (uc == 0x0F) {
        g_pe.mode = 1;
        g_pe.prompt_len = 0;
        /* Copy tên hiện tại vào prompt */
        int i = 0;
        while (g_pe.filename[i] && i < 63) {
            g_pe.prompt[i] = g_pe.filename[i];
            i++;
        }
        g_pe.prompt_len = i;
        pe_draw();
        return 1;
    }

    /* Ctrl+X = 0x18 — Exit (nano style) */
    if (uc == 0x18) {
        if (g_pe.dirty) {
            g_pe.mode = 2;  /* hỏi lưu */
            pe_draw();
        } else {
            pe_close_redraw();
        }
        return 1;
    }

    /* Enter */
    if (uc == 10 || uc == 13) {
        if (g_pe.line_count < PE_MAX_ROWS) {
            /* Tách dòng tại vị trí cursor */
            int tail_len = g_pe.line_lens[g_pe.cur_row] - g_pe.cur_col;
            /* Dịch các dòng sau xuống */
            for (int i = g_pe.line_count; i > g_pe.cur_row + 1; i--) {
                for (int j = 0; j < PE_MAX_LINE; j++)
                    g_pe.lines[i][j] = g_pe.lines[i-1][j];
                g_pe.line_lens[i] = g_pe.line_lens[i-1];
            }
            /* Nội dung dòng mới */
            for (int j = 0; j < tail_len; j++)
                g_pe.lines[g_pe.cur_row+1][j] = g_pe.lines[g_pe.cur_row][g_pe.cur_col + j];
            g_pe.lines[g_pe.cur_row+1][tail_len] = 0;
            g_pe.line_lens[g_pe.cur_row+1] = tail_len;
            /* Cắt dòng cũ */
            g_pe.lines[g_pe.cur_row][g_pe.cur_col] = 0;
            g_pe.line_lens[g_pe.cur_row] = g_pe.cur_col;
            g_pe.line_count++;
            g_pe.cur_row++;
            g_pe.cur_col = 0;
            g_pe.dirty = 1;
            pe_draw();
        }
        return 1;
    }

    /* Backspace */
    if (uc == 8) {
        if (g_pe.cur_col > 0) {
            int len = g_pe.line_lens[g_pe.cur_row];
            for (int j = g_pe.cur_col - 1; j < len - 1; j++)
                g_pe.lines[g_pe.cur_row][j] = g_pe.lines[g_pe.cur_row][j+1];
            g_pe.lines[g_pe.cur_row][len-1] = 0;
            g_pe.line_lens[g_pe.cur_row] = len - 1;
            g_pe.cur_col--;
        } else if (g_pe.cur_row > 0) {
            /* Ghép dòng với dòng trên */
            int up_len = g_pe.line_lens[g_pe.cur_row - 1];
            int cur_len = g_pe.line_lens[g_pe.cur_row];
            if (up_len + cur_len < PE_MAX_LINE - 1) {
                for (int j = 0; j < cur_len; j++)
                    g_pe.lines[g_pe.cur_row-1][up_len + j] = g_pe.lines[g_pe.cur_row][j];
                g_pe.lines[g_pe.cur_row-1][up_len + cur_len] = 0;
                g_pe.line_lens[g_pe.cur_row-1] = up_len + cur_len;
                /* Xóa dòng */
                for (int i = g_pe.cur_row; i < g_pe.line_count - 1; i++) {
                    for (int j = 0; j < PE_MAX_LINE; j++)
                        g_pe.lines[i][j] = g_pe.lines[i+1][j];
                    g_pe.line_lens[i] = g_pe.line_lens[i+1];
                }
                g_pe.line_count--;
                g_pe.cur_row--;
                g_pe.cur_col = up_len;
            }
        }
        g_pe.dirty = 1;
        pe_draw();
        return 1;
    }

    /* Arrow UP = 128 */
    if (uc == 128) {
        if (g_pe.cur_row > 0) {
            g_pe.cur_row--;
            if (g_pe.cur_col > g_pe.line_lens[g_pe.cur_row])
                g_pe.cur_col = g_pe.line_lens[g_pe.cur_row];
        }
        pe_draw();
        return 1;
    }
    /* DOWN = 129 */
    if (uc == 129) {
        if (g_pe.cur_row < g_pe.line_count - 1) {
            g_pe.cur_row++;
            if (g_pe.cur_col > g_pe.line_lens[g_pe.cur_row])
                g_pe.cur_col = g_pe.line_lens[g_pe.cur_row];
        }
        pe_draw();
        return 1;
    }
    /* LEFT = 130 */
    if (uc == 130) {
        if (g_pe.cur_col > 0) g_pe.cur_col--;
        else if (g_pe.cur_row > 0) {
            g_pe.cur_row--;
            g_pe.cur_col = g_pe.line_lens[g_pe.cur_row];
        }
        pe_draw();
        return 1;
    }
    /* RIGHT = 131 */
    if (uc == 131) {
        if (g_pe.cur_col < g_pe.line_lens[g_pe.cur_row]) g_pe.cur_col++;
        else if (g_pe.cur_row < g_pe.line_count - 1) {
            g_pe.cur_row++;
            g_pe.cur_col = 0;
        }
        pe_draw();
        return 1;
    }

    /* Ký tự thường */
    if (uc >= 32 && uc < 127) {
        int len = g_pe.line_lens[g_pe.cur_row];
        if (len < PE_MAX_LINE - 1) {
            for (int j = len; j > g_pe.cur_col; j--)
                g_pe.lines[g_pe.cur_row][j] = g_pe.lines[g_pe.cur_row][j-1];
            g_pe.lines[g_pe.cur_row][g_pe.cur_col] = c;
            g_pe.line_lens[g_pe.cur_row] = len + 1;
            g_pe.lines[g_pe.cur_row][len + 1] = 0;
            g_pe.cur_col++;
            g_pe.dirty = 1;
            pe_draw();
        }
        return 1;
    }

    return 0;
}

/* ═══ Click ═══ */
int pawedit_handle_click(int mx, int my) {
    if (!g_pe.visible) return 0;

    int x = g_pe.x, y = g_pe.y, w = g_pe.w, h = g_pe.h;

    if (mx < x || mx > x + w || my < y || my > y + h) {
        pe_close_redraw();
        return 1;
    }

    if (my >= y + 2 && my <= y + 36) {
        int right = x + w;
        int dist = right - mx;
        if (dist >= 8 && dist < 28) { pe_close_redraw(); return 1; }
        if (dist >= 36 && dist < 56) { pe_close_redraw(); return 1; }
        if (dist >= 64 && dist < 84) {
            extern uint32_t fb_width(void);
            extern uint32_t fb_height(void);
            int fw = (int)fb_width();
            int fh = (int)fb_height();
            if (g_pe.x == 180) {
                g_pe.x = 140; g_pe.y = 32;
                g_pe.w = fw - 150; g_pe.h = fh - 40;
            } else {
                g_pe.x = 180; g_pe.y = 50;
                g_pe.w = fw - 200; g_pe.h = fh - 90;
            }
            pe_draw();
            return 1;
        }
    }

    /* Click vào vùng text — set cursor */
    int cy_start = y + 48;
    int row_h = 22;
    if (my >= cy_start) {
        int row = (my - cy_start) / row_h;
        int li = g_pe.scroll + row;
        if (li >= 0 && li < g_pe.line_count) {
            g_pe.cur_row = li;
            /* Tính col từ x */
            int cx_start = x + 44;
            int col = (mx - cx_start) / 8;
            if (col < 0) col = 0;
            if (col > g_pe.line_lens[li]) col = g_pe.line_lens[li];
            g_pe.cur_col = col;
            pe_draw();
        }
    }
    return 1;
}
