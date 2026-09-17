/* FelisOS — Full keyboard driver */
#include "catpp_rt.h"
extern int purrminal_handle_key(char c);
extern int appmenu_handle_key(char c);
extern int appmenu_is_active(void);
extern int appmenu_is_active(void);

#define KBD_DATA 0x60

static inline uint8_t inb(uint16_t port) {
    uint8_t r;
    __asm__ volatile("inb %1, %0" : "=a"(r) : "Nd"(port));
    return r;
}

/* Special keys = 128+ */
#define KEY_UP      128
#define KEY_DOWN    129
#define KEY_LEFT    130
#define KEY_RIGHT   131
#define KEY_HOME    132
#define KEY_END     133
#define KEY_DELETE  134

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
static volatile int shift = 0, caps = 0, extended = 0;

void keyboard_handler(void) {
    uint8_t sc = inb(KBD_DATA);

    if (sc == 0xE0) { extended = 1; return; }

    if (sc & 0x80) {
        uint8_t rel = sc & 0x7F;
        if (rel == 0x2A || rel == 0x36) shift = 0;
        extended = 0;
        return;
    }

    if (sc == 0x2A || sc == 0x36) { shift = 1; extended = 0; return; }
    if (sc == 0x3A) { caps = !caps; extended = 0; return; }

    if (extended) {
        unsigned char k = 0;
        switch (sc) {
            case 0x48: k = KEY_UP; break;
            case 0x50: k = KEY_DOWN; break;
            case 0x4B: k = KEY_LEFT; break;
            case 0x4D: k = KEY_RIGHT; break;
            case 0x47: k = KEY_HOME; break;
            case 0x4F: k = KEY_END; break;
            case 0x53: k = KEY_DELETE; break;
        }
        extended = 0;
        if (k) {
            int n = (kbuf_head + 1) % KBUF_SIZE;
            if (n != kbuf_tail) { kbuf[kbuf_head] = k; kbuf_head = n; }
        }
        return;
    }

    if (sc < 128) {
        char c = shift ? map_upper[sc] : map_lower[sc];
        if (caps && map_lower[sc] >= 'a' && map_lower[sc] <= 'z')
            c = shift ? map_lower[sc] : map_upper[sc];
        if (c) {
            extern int tty_get(void);
            extern volatile int g_pending_click;
            extern volatile int g_click_x;
            extern volatile int g_click_y;
            extern int mouse_get_x(void);
            extern int mouse_get_y(void);
            if (tty_get() == 0) {
                if (appmenu_is_active()) {
                    appmenu_handle_key(c);
                } else if (c == 10) {
                    g_click_x = mouse_get_x();
                    g_click_y = mouse_get_y();
                    g_pending_click = 1;
                } else {
                    purrminal_handle_key(c);
                }
            } else {
                int n = (kbuf_head + 1) % KBUF_SIZE;
                if (n != kbuf_tail) { kbuf[kbuf_head] = (unsigned char)c; kbuf_head = n; }
            }
        }
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
