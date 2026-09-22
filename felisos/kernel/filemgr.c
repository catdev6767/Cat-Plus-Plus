/* Kitty — File Manager (rewrite gọn) */
#include <stdint.h>

extern int  fb_is_active(void);
extern uint32_t fb_width(void);
extern uint32_t fb_height(void);
extern void fb_rect(uint32_t x, uint32_t y, uint32_t w, uint32_t h, uint32_t color);
extern void fb_puts_at_color(const char* s, int x, int y, uint32_t fg, uint32_t bg);
extern void fb_char_at(char ch, uint32_t x, uint32_t y, uint32_t fg, uint32_t bg);
extern void fb_puts_scale_xy(const char* s, int x, int y, uint32_t fg, uint32_t bg, int sx, int sy);
extern void fb_cursor_forget(void);
extern void fb_draw_wallpaper(void);
extern void fb_draw_panel(void);
extern void fb_draw_dock(void);
extern void serial_print_str(const char* s);

extern int fs_list_children(int parent, int* out, int max);
extern const char* fs_get_name(int i);
extern int fs_is_dir(int i);
extern int fs_file_size(int i);
extern int fs_get_parent(int i);
extern void fs_path_of(int idx, char* out, int max);
extern int fs_create_at(int parent, const char* name, int is_dir);
extern int fs_delete(const char* name);
extern const char* fs_read(const char* name, int* size_out);
extern int fs_write(const char* name, const char* data, int size);
extern void pawedit_open(const char* fname);
extern void coming_soon_open(const char* name);

#define FM_MAX 64
#define FM_ROW_H 40

typedef struct {
    int x, y, w, h, visible;
    int cwd;                        /* -1 = root */
    int children[FM_MAX];
    int count;
    int sel;                        /* 0 = "..", 1.. = children */
    int scroll, max_rows;
    int last_click;
    char clip_name[64];
    char clip_data[512];
    int  clip_size, has_clip;
} FileMgr;

static FileMgr g_fm = {0};

/* ═══ Extension ═══ */
static int ext_is(const char* n, const char* e) {
    if (!n || !e) return 0;
    int nl=0, el=0;
    while (n[nl]) nl++;
    while (e[el]) el++;
    if (nl < el) return 0;
    for (int i = 0; i < el; i++)
        if (n[nl-el+i] != e[i]) return 0;
    return 1;
}

/* ═══ Refresh ═══ */
static void fm_refresh(void) {
    g_fm.count = fs_list_children(g_fm.cwd, g_fm.children, FM_MAX);
    if (g_fm.sel > g_fm.count) g_fm.sel = 0;
    if (g_fm.scroll > g_fm.count) g_fm.scroll = 0;
}

/* ═══ Draw ═══ */
static void fm_draw(void) {
    if (!fb_is_active() || !g_fm.visible) return;

    int x = g_fm.x, y = g_fm.y, w = g_fm.w, h = g_fm.h;

    /* Shadow */
    fb_rect(x+6, y+6, w, h, 0x00101010);
    /* Body */
    fb_rect(x, y, w, h, 0x00FFFFFF);
    /* Title XP */
    for (int gy = 0; gy < 30; gy++) {
        uint32_t col = (gy < 8) ? 0x005B9DE5 : (gy < 22 ? 0x003A6EA5 : 0x00245888);
        fb_rect(x, y+gy, w, 1, col);
    }
    fb_puts_scale_xy("File Manager", x+14, y+6, 0x00FFFFFF, 0x003A6EA5, 1, 2);

    /* Nút XP */
    fb_rect(x+w-28, y+8, 20, 20, 0x00C0392B);  /* X */
    fb_rect(x+w-56, y+8, 20, 20, 0x00E8A040);  /* - */
    fb_rect(x+w-84, y+8, 20, 20, 0x0038A03A);  /* + */

    /* Border */
    fb_rect(x, y, w, 2, 0x00BBBBBB);
    fb_rect(x, y+h-2, w, 2, 0x00BBBBBB);
    fb_rect(x, y, 2, h, 0x00BBBBBB);
    fb_rect(x+w-2, y, 2, h, 0x00BBBBBB);

    /* Path bar */
    fb_rect(x+4, y+34, w-8, 30, 0x00ECE9D8);
    char path[200];
    fs_path_of(g_fm.cwd, path, sizeof(path));
    fb_puts_scale_xy(path, x+10, y+36, 0x00000000, 0x00ECE9D8, 1, 2);

    /* List */
    int ly = y + 70;
    int rows = (h - 64 - 24) / FM_ROW_H;
    g_fm.max_rows = rows;

    int total = g_fm.count + (g_fm.cwd >= 0 ? 1 : 0);

    for (int i = 0; i < rows; i++) {
        int idx = g_fm.scroll + i;
        if (idx >= total) break;

        int cy = ly + i * FM_ROW_H;
        int is_sel = (idx == g_fm.sel);

        if (is_sel) fb_rect(x+4, cy, w-8, FM_ROW_H, 0x003366CC);

        /* Item info */
        const char* name = 0;
        int is_dir = 0, size = 0;

        if (idx == 0 && g_fm.cwd >= 0) {
            name = "..";
            is_dir = 1;
        } else {
            int pos = idx - (g_fm.cwd >= 0 ? 1 : 0);
            if (pos < 0 || pos >= g_fm.count) continue;
            int fi = g_fm.children[pos];
            name = fs_get_name(fi);
            is_dir = fs_is_dir(fi);
            size = fs_file_size(fi);
        }

        /* Icon */
        if (is_dir) {
            fb_rect(x+10, cy+10, 20, 18, 0x00E8A040);
            fb_rect(x+14, cy+6, 10, 6, 0x00E8A040);
        } else {
            fb_rect(x+12, cy+8, 16, 22, 0x00F0F0F0);
            fb_rect(x+12, cy+8, 16, 1, 0x00888888);
            fb_rect(x+12, cy+29, 16, 1, 0x00888888);
        }

        /* Name */
        fb_puts_scale_xy(name, x+42, cy+10, 0x00000000,
                         is_sel ? 0x003366CC : 0x00FFFFFF, 1, 2);

        /* Size */
        if (!is_dir) {
            char sb[16];
            int o = 0;
            if (size >= 1000) sb[o++] = '0' + (size/1000)%10;
            if (size >= 100)  sb[o++] = '0' + (size/100)%10;
            if (size >= 10)   sb[o++] = '0' + (size/10)%10;
            sb[o++] = '0' + size%10;
            sb[o++] = 'B'; sb[o] = 0;
            fb_puts_at_color(sb, x+w-70, cy+14, 0x00888888,
                             is_sel ? 0x003366CC : 0x00FFFFFF);
        }
    }

    /* Status bar */
    fb_rect(x+2, y+h-22, w-4, 20, 0x00ECE9D8);
    fb_puts_at_color("^N:New ^C:Copy ^V:Paste Del:Xoa ESC:Dong",
                     x+8, y+h-16, 0x00000000, 0x00ECE9D8);
}

/* ═══ Full path của item ═══ */
static void fm_path(int pos, char* out) {
    char base[160];
    fs_path_of(g_fm.cwd, base, sizeof(base));
    int o = 0;
    if (base[0] == '/' && base[1] == 0) out[o++] = '/';
    else {
        int i = 0;
        while (base[i] && o < 190) out[o++] = base[i++];
        if (o > 0 && out[o-1] != '/') out[o++] = '/';
    }
    const char* n = fs_get_name(g_fm.children[pos]);
    int i = 0;
    while (n && n[i] && o < 199) out[o++] = n[i++];
    out[o] = 0;
}

/* ═══ Copy current item ═══ */
static void fm_copy(void) {
    int pos = g_fm.sel - (g_fm.cwd >= 0 ? 1 : 0);
    if (pos < 0 || pos >= g_fm.count) return;
    int fi = g_fm.children[pos];
    if (fs_is_dir(fi)) return;

    char path[200];
    fm_path(pos, path);
    int sz = 0;
    const char* data = fs_read(path, &sz);
    if (!data || sz <= 0) return;

    int n = 0;
    const char* nm = fs_get_name(fi);
    while (nm[n] && n < 63) { g_fm.clip_name[n] = nm[n]; n++; }
    g_fm.clip_name[n] = 0;

    int cp = sz < 511 ? sz : 511;
    for (int i = 0; i < cp; i++) g_fm.clip_data[i] = data[i];
    g_fm.clip_size = cp;
    g_fm.has_clip = 1;
    serial_print_str("[fm] copied\n");
}

/* ═══ Paste ═══ */
static void fm_paste(void) {
    if (!g_fm.has_clip) return;

    /* Tên mới: copy_<name> */
    char newname[80];
    int o = 0;
    const char* pfx = "copy_";
    while (*pfx) newname[o++] = *pfx++;
    int i = 0;
    while (g_fm.clip_name[i] && o < 78) newname[o++] = g_fm.clip_name[i++];
    newname[o] = 0;

    fs_create_at(g_fm.cwd, newname, 0);

    /* Ghi nội dung */
    char base[160], path[220];
    fs_path_of(g_fm.cwd, base, sizeof(base));
    o = 0;
    if (base[0] == '/' && base[1] == 0) path[o++] = '/';
    else {
        i = 0;
        while (base[i] && o < 200) path[o++] = base[i++];
        if (o > 0 && path[o-1] != '/') path[o++] = '/';
    }
    i = 0;
    while (newname[i] && o < 219) path[o++] = newname[i++];
    path[o] = 0;

    fs_write(path, g_fm.clip_data, g_fm.clip_size);
    g_fm.has_clip = 0;
    fm_refresh();
    fm_draw();
    serial_print_str("[fm] pasted\n");
}

/* ═══ New folder ═══ */
static void fm_new_folder(void) {
    for (int n = 1; n < 100; n++) {
        char name[32];
        int o = 0;
        const char* p = "new";
        while (*p) name[o++] = *p++;
        if (n >= 10) name[o++] = '0' + (n/10)%10;
        name[o++] = '0' + n%10;
        name[o] = 0;

        int exists = 0;
        for (int i = 0; i < g_fm.count; i++) {
            const char* cn = fs_get_name(g_fm.children[i]);
            int k = 0, ok = 1;
            while (name[k] || cn[k]) {
                if (name[k] != cn[k]) { ok = 0; break; }
                k++;
            }
            if (ok) { exists = 1; break; }
        }
        if (exists) continue;

        if (fs_create_at(g_fm.cwd, name, 1) >= 0) {
            fm_refresh();
            fm_draw();
            return;
        }
    }
}

/* ═══ Delete ═══ */
static void fm_delete(void) {
    if (g_fm.cwd >= 0 && g_fm.sel == 0) return;
    int pos = g_fm.sel - (g_fm.cwd >= 0 ? 1 : 0);
    if (pos < 0 || pos >= g_fm.count) return;

    char path[200];
    fm_path(pos, path);
    fs_delete(path);
    if (g_fm.sel > 0) g_fm.sel--;
    g_fm.last_click = -1;
    fm_refresh();
    fm_draw();
}

/* ═══ Open ═══ */
void filemgr_open(void) {
    int fw = (int)fb_width();
    int fh = (int)fb_height();

    if (g_fm.visible) { fm_draw(); return; }

    g_fm.w = fw - 200;
    g_fm.h = fh - 120;
    g_fm.x = (fw - g_fm.w) / 2;
    g_fm.y = (fh - 32 - g_fm.h) / 2;
    g_fm.visible = 1;
    g_fm.cwd = -1;
    g_fm.sel = 0;
    g_fm.scroll = 0;
    g_fm.last_click = -1;
    g_fm.has_clip = 0;
    fm_refresh();
    fm_draw();
}

void filemgr_close(void) {
    g_fm.visible = 0;
}

int filemgr_is_visible(void) { return g_fm.visible; }
void filemgr_redraw_public(void) { fm_draw(); }

/* ═══ Key handler ═══ */
int filemgr_handle_key(char c) {
    if (!g_fm.visible) return 0;
    int uc = (unsigned char)c;
    int total = g_fm.count + (g_fm.cwd >= 0 ? 1 : 0);

    serial_print_str("[fm] key\n");

    if (uc == 27) {
        /* ESC — đóng */
        g_fm.visible = 0;
        fb_cursor_forget();
        fb_draw_wallpaper();
        fb_draw_panel();
        fb_draw_dock();
        return 1;
    }
    if (uc == 0x0E) { fm_new_folder(); return 1; }  /* Ctrl+N */
    if (uc == 0x03) { fm_copy(); return 1; }        /* Ctrl+C */
    if (uc == 0x16) { fm_paste(); return 1; }       /* Ctrl+V */
    if (uc == 127 || uc == 134) { fm_delete(); return 1; }  /* Del */

    if (uc == 128) {  /* UP */
        if (g_fm.sel > 0) g_fm.sel--;
        if (g_fm.sel < g_fm.scroll) g_fm.scroll = g_fm.sel;
        fm_draw();
        return 1;
    }
    if (uc == 129) {  /* DOWN */
        if (g_fm.sel < total - 1) g_fm.sel++;
        if (g_fm.sel >= g_fm.scroll + g_fm.max_rows)
            g_fm.scroll = g_fm.sel - g_fm.max_rows + 1;
        fm_draw();
        return 1;
    }
    if (uc == 10 || uc == 13) {  /* Enter */
        if (g_fm.sel == 0 && g_fm.cwd >= 0) {
            g_fm.cwd = fs_get_parent(g_fm.cwd);
            g_fm.sel = 0; g_fm.scroll = 0; g_fm.last_click = -1;
            fm_refresh(); fm_draw();
        } else {
            int pos = g_fm.sel - (g_fm.cwd >= 0 ? 1 : 0);
            if (pos >= 0 && pos < g_fm.count) {
                int fi = g_fm.children[pos];
                if (fs_is_dir(fi)) {
                    g_fm.cwd = fi;
                    g_fm.sel = 0; g_fm.scroll = 0; g_fm.last_click = -1;
                    fm_refresh(); fm_draw();
                } else {
                    const char* n = fs_get_name(fi);
                    if (ext_is(n, ".catpp")) coming_soon_open(n);
                    else {
                        char path[200];
                        fm_path(pos, path);
                        pawedit_open(path);
                    }
                }
            }
        }
        return 1;
    }
    return 0;
}

/* ═══ Click handler ═══ */
int filemgr_handle_click(int mx, int my) {
    if (!g_fm.visible) return 0;

    int x = g_fm.x, y = g_fm.y, w = g_fm.w, h = g_fm.h;

    /* Ngoài → đóng */
    if (mx < x || mx > x+w || my < y || my > y+h) {
        g_fm.visible = 0;
        fb_cursor_forget();
        fb_draw_wallpaper();
        fb_draw_panel();
        fb_draw_dock();
        return 1;
    }

    /* Title bar */
    if (my >= y+2 && my <= y+32) {
        int dist = (x+w) - mx;
        if (dist >= 8 && dist < 28) {
            g_fm.visible = 0;
            fb_cursor_forget();
            fb_draw_wallpaper();
            fb_draw_panel();
            fb_draw_dock();
            return 1;
        }
        if (dist >= 36 && dist < 56) {
            g_fm.visible = 0;
            fb_cursor_forget();
            fb_draw_wallpaper();
            fb_draw_panel();
            fb_draw_dock();
            return 1;
        }
        if (dist >= 64 && dist < 84) { return 1; }
        return 1;
    }

    /* Click item */
    int ly = y + 70;
    if (my >= ly && my < y + h - 24) {
        int row = (my - ly) / FM_ROW_H;
        int idx = g_fm.scroll + row;
        int total = g_fm.count + (g_fm.cwd >= 0 ? 1 : 0);
        if (idx < 0 || idx >= total) return 1;

        if (idx == g_fm.last_click) {
            /* Double-click → mở */
            g_fm.last_click = -1;
            g_fm.sel = idx;
            fm_draw();

            if (idx == 0 && g_fm.cwd >= 0) {
                g_fm.cwd = fs_get_parent(g_fm.cwd);
                g_fm.sel = 0; g_fm.scroll = 0;
                fm_refresh(); fm_draw();
            } else {
                int pos = idx - (g_fm.cwd >= 0 ? 1 : 0);
                if (pos >= 0 && pos < g_fm.count) {
                    int fi = g_fm.children[pos];
                    if (fs_is_dir(fi)) {
                        g_fm.cwd = fi;
                        g_fm.sel = 0; g_fm.scroll = 0;
                        fm_refresh(); fm_draw();
                    } else {
                        const char* n = fs_get_name(fi);
                        if (ext_is(n, ".catpp")) coming_soon_open(n);
                        else {
                            char path[200];
                            fm_path(pos, path);
                            pawedit_open(path);
                        }
                    }
                }
            }
        } else {
            /* Click lần 1 → chọn */
            g_fm.sel = idx;
            g_fm.last_click = idx;
            fm_draw();
        }
        return 1;
    }
    return 1;
}
