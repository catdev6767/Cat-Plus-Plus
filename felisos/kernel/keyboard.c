/* Kitty — Keyboard driver with GUI queue */
#include "catpp_rt.h"

#define KBD_DATA 0x60

extern void tty_switch(int n);
extern int  tty_get(void);

static inline uint8_t inb(uint16_t port) {
    uint8_t r;
    __asm__ volatile("inb %1, %0" : "=a"(r) : "Nd"(port));
    return r;
}

#define KEY_UP      128
#define KEY_DOWN    129
#define KEY_LEFT    130
#define KEY_RIGHT   131
#define KEY_HOME    132
#define KEY_END     133
#define KEY_DELETE  134
#define KEY_PGUP    135
#define KEY_PGDN    136
#define KEY_F1      137
#define KEY_F2      138
#define KEY_F3      139
#define KEY_ESC     27

static const char map_lower[128] = {
    [0x01]=27,
    [0x02]='1',[0x03]='2',[0x04]='3',[0x05]='4',[0x06]='5',
    [0x07]='6',[0x08]='7',[0x09]='8',[0x0A]='9',[0x0B]='0',
    [0x0C]='-',[0x0D]='=',[0x0E]='\b',[0x0F]='\t',
    [0x10]='q',[0x11]='w',[0x12]='e',[0x13]='r',[0x14]='t',
    [0x15]='y',[0x16]='u',[0x17]='i',[0x18]='o',[0x19]='p',
    [0x1A]='[',[0x1B]=']',[0x1C]='\n',
    [0x1E]='a',[0x1F]='s',[0x20]='d',[0x21]='f',[0x22]='g',
    [0x23]='h',[0x24]='j',[0x25]='k',[0x26]='l',[0x27]=';',
    [0x28]='\'',[0x29]='`',[0x2B]='\\',
    [0x2C]='z',[0x2D]='x',[0x2E]='c',[0x2F]='v',[0x30]='b',
    [0x31]='n',[0x32]='m',[0x33]=',',[0x34]='.',[0x35]='/',
    [0x37]='*',[0x39]=' ',
};

static const char map_upper[128] = {
    [0x01]=27,
    [0x02]='!',[0x03]='@',[0x04]='#',[0x05]='$',[0x06]='%',
    [0x07]='^',[0x08]='&',[0x09]='*',[0x0A]='(',[0x0B]=')',
    [0x0C]='_',[0x0D]='+',[0x0E]='\b',[0x0F]='\t',
    [0x10]='Q',[0x11]='W',[0x12]='E',[0x13]='R',[0x14]='T',
    [0x15]='Y',[0x16]='U',[0x17]='I',[0x18]='O',[0x19]='P',
    [0x1A]='{',[0x1B]='}',[0x1C]='\n',
    [0x1E]='A',[0x1F]='S',[0x20]='D',[0x21]='F',[0x22]='G',
    [0x23]='H',[0x24]='J',[0x25]='K',[0x26]='L',[0x27]=':',
    [0x28]='"',[0x29]='~',[0x2B]='|',
    [0x2C]='Z',[0x2D]='X',[0x2E]='C',[0x2F]='V',[0x30]='B',
    [0x31]='N',[0x32]='M',[0x33]='<',[0x34]='>',[0x35]='?',
    [0x37]='*',[0x39]=' ',
};

#define KBUF_SIZE 256
static unsigned char kbuf[KBUF_SIZE];
static volatile int kbuf_head = 0, kbuf_tail = 0;
static volatile int shift = 0, caps = 0, ctrl = 0, alt = 0, extended = 0;

/* ═══ GUI key queue — 32 slot ═══ */
#define GUIQ_SIZE 32
volatile char g_gui_queue[GUIQ_SIZE];
volatile int  g_gui_qhead = 0;
volatile int  g_gui_qtail = 0;

int gui_key_has(void) { return g_gui_qhead != g_gui_qtail; }

char gui_key_pop(void) {
    if (g_gui_qhead == g_gui_qtail) return 0;
    char c = g_gui_queue[g_gui_qtail];
    g_gui_qtail = (g_gui_qtail + 1) % GUIQ_SIZE;
    return c;
}

static void gui_key_push(unsigned char k) {
    int n = (g_gui_qhead + 1) % GUIQ_SIZE;
    if (n == g_gui_qtail) return;  /* full — drop */
    g_gui_queue[g_gui_qhead] = (char)k;
    g_gui_qhead = n;
}

void keyboard_handler(void) {
    uint8_t sc = inb(KBD_DATA);

    /* Extended prefix */
    if (sc == 0xE0) { extended = 1; return; }

    /* Release */
    if (sc & 0x80) {
        uint8_t rel = sc & 0x7F;
        if (rel == 0x2A || rel == 0x36) shift = 0;
        if (rel == 0x1D) ctrl = 0;
        if (rel == 0x38) alt = 0;
        extended = 0;
        return;
    }

    /* Modifier press */
    if (sc == 0x2A || sc == 0x36) { shift = 1; extended = 0; return; }
    if (sc == 0x1D) { ctrl = 1; extended = 0; return; }
    if (sc == 0x38) { alt = 1; extended = 0; return; }
    if (sc == 0x3A) { caps = !caps; extended = 0; return; }

    /* TTY switch Ctrl+Alt+F1-F3 */
    if (ctrl && alt) {
        if (sc == 0x3B) { tty_switch(0); extended = 0; return; }
        if (sc == 0x3C) { tty_switch(1); extended = 0; return; }
        if (sc == 0x3D) { tty_switch(2); extended = 0; return; }
    }

    /* Extended keys (arrows, Del, Home, End, PgUp, PgDn) */
    if (extended) {
        /* Super key (Windows key) — toggle Start menu */
        if (sc == 0x5B || sc == 0x5C) {
            extern void fb_start_menu_toggle(void);
            extern int fb_start_menu_is_open(void);
            extern void fb_draw_start_menu(void);
            extern void fb_draw_wallpaper(void);
            extern void fb_draw_panel(void);
            extern void fb_draw_dock(void);
            extern void redraw_windows_after_menu(void);

            fb_start_menu_toggle();
            if (fb_start_menu_is_open()) {
                fb_draw_start_menu();
            } else {
                /* Đóng menu — vẽ lại desktop + windows */
                fb_draw_wallpaper();
                fb_draw_panel();
                fb_draw_dock();
                redraw_windows_after_menu();
            }
            extended = 0;
            return;
        }

        unsigned char k = 0;
        switch (sc) {
            case 0x48: k = KEY_UP; break;
            case 0x50: k = KEY_DOWN; break;
            case 0x4B: k = KEY_LEFT; break;
            case 0x4D: k = KEY_RIGHT; break;
            case 0x47: k = KEY_HOME; break;
            case 0x4F: k = KEY_END; break;
            case 0x53: k = KEY_DELETE; break;
            case 0x49: k = KEY_PGUP; break;
            case 0x51: k = KEY_PGDN; break;
        }
        extended = 0;
        if (!k) return;
        if (tty_get() == 0) {
            gui_key_push(k);
        } else {
            int n = (kbuf_head + 1) % KBUF_SIZE;
            if (n != kbuf_tail) { kbuf[kbuf_head] = k; kbuf_head = n; }
        }
        return;
    }

    /* Regular keys */
    if (sc >= 128) return;

    char c = shift ? map_upper[sc] : map_lower[sc];
    if (caps && map_lower[sc] >= 'a' && map_lower[sc] <= 'z')
        c = shift ? map_lower[sc] : map_upper[sc];
    if (!c) return;

    /* Ctrl+letter → control code */
    if (ctrl && c >= 'a' && c <= 'z') c = c - 'a' + 1;
    else if (ctrl && c >= 'A' && c <= 'Z') c = c - 'A' + 1;

    if (tty_get() == 0) {
        gui_key_push((unsigned char)c);
    } else {
        int n = (kbuf_head + 1) % KBUF_SIZE;
        if (n != kbuf_tail) { kbuf[kbuf_head] = (unsigned char)c; kbuf_head = n; }
    }
}

unsigned char keyboard_getchar_raw(void) {
    while (kbuf_head == kbuf_tail) __asm__ volatile("hlt");
    unsigned char c = kbuf[kbuf_tail];
    kbuf_tail = (kbuf_tail + 1) % KBUF_SIZE;
    return c;
}

char keyboard_getchar(void) { return (char)keyboard_getchar_raw(); }
int keyboard_has_key(void) { return kbuf_head != kbuf_tail; }
