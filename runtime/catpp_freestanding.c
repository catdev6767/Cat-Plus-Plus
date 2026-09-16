/* Cat++ Runtime — freestanding (kernel) implementation.
   Ghi trực tiếp vào VGA text mode + serial port.
*/
#include "catpp_rt.h"
#include <stddef.h>

#define VGA_WIDTH  80
#define VGA_HEIGHT 25
#define VGA_MEM    ((volatile uint16_t*)0xB8000)

/* Framebuffer API (kernel/fb.c) */
extern int  fb_is_active(void);
extern void fb_putc(char c);
extern void fb_clear(void);

/* ═══ VGA ═══ */
static size_t   vga_row = 0;
static size_t   vga_col = 0;
static uint8_t  vga_color = 0x0F;  /* trắng trên đen */

static inline uint16_t vga_entry(char c, uint8_t color) {
    return (uint16_t)c | ((uint16_t)color << 8);
}

static void vga_clear(void) {
    if (fb_is_active()) { fb_clear(); vga_row = 0; vga_col = 0; return; }
    /* fb disabled */
    for (size_t y = 0; y < VGA_HEIGHT; y++)
        for (size_t x = 0; x < VGA_WIDTH; x++)
            VGA_MEM[y * VGA_WIDTH + x] = vga_entry(' ', vga_color);
    vga_row = 0; vga_col = 0;
}

static void vga_scroll(void) {
    for (size_t y = 1; y < VGA_HEIGHT; y++)
        for (size_t x = 0; x < VGA_WIDTH; x++)
            VGA_MEM[(y-1)*VGA_WIDTH + x] = VGA_MEM[y*VGA_WIDTH + x];
    for (size_t x = 0; x < VGA_WIDTH; x++)
        VGA_MEM[(VGA_HEIGHT-1)*VGA_WIDTH + x] = vga_entry(' ', vga_color);
    vga_row = VGA_HEIGHT - 1;
}

static void vga_putc(char c) {
    if (c == '\n') {
        vga_col = 0;
        if (++vga_row >= VGA_HEIGHT) vga_scroll();
        return;
    }
    if (c == '\r') { vga_col = 0; return; }
    if (c == '\t') { vga_col = (vga_col + 8) & ~7; return; }
    if (c == '\b') {
        /* Backspace — di chuyển con trỏ lùi, KHÔNG in ký tự */
        if (vga_col > 0) vga_col--;
        return;
    }
    if (c < 32) return;  /* Bỏ qua các ký tự điều khiển khác */
    VGA_MEM[vga_row * VGA_WIDTH + vga_col] = vga_entry(c, vga_color);
    if (++vga_col >= VGA_WIDTH) {
        vga_col = 0;
        if (++vga_row >= VGA_HEIGHT) vga_scroll();
    }
}

/* ═══ Serial (COM1) — cho QEMU debug ═══ */
#define COM1 0x3F8

static inline void outb(uint16_t port, uint8_t val) {
    __asm__ volatile("outb %0, %1" : : "a"(val), "Nd"(port));
}

static inline uint8_t inb(uint16_t port) {
    uint8_t r;
    __asm__ volatile("inb %1, %0" : "=a"(r) : "Nd"(port));
    return r;
}

static void serial_init(void) {
    outb(COM1 + 1, 0x00);  /* disable interrupts */
    outb(COM1 + 3, 0x80);  /* enable DLAB */
    outb(COM1 + 0, 0x03);  /* divisor lo (38400) */
    outb(COM1 + 1, 0x00);  /* divisor hi */
    outb(COM1 + 3, 0x03);  /* 8N1 */
    outb(COM1 + 2, 0xC7);  /* enable FIFO */
    outb(COM1 + 4, 0x0B);  /* IRQs enabled, RTS/DSR */
}

static void serial_putc(char c) {
    while (!(inb(COM1 + 5) & 0x20));
    outb(COM1, c);
}

/* Print chỉ ra serial — không dùng cho màn hình */
void serial_print_str(const char* s) {
    while (*s) serial_putc(*s++);
}


/* ═══ Public API ═══ */
void catpp_init(void) {
    serial_init();
    vga_clear();
}

void (*g_out_hook)(char) = 0;

void catpp_putc(char c) {
    if (g_out_hook) { g_out_hook(c); return; }
    if (fb_is_active()) fb_putc(c);
    else vga_putc(c);
    serial_putc(c);
}

void catpp_print_str(const char* s) {
    if (!s) {
        catpp_putc('('); catpp_putc('n'); catpp_putc('u'); catpp_putc('l'); catpp_putc('l'); catpp_putc(')');
        catpp_putc('\n');
        return;
    }
    while (*s) {
        catpp_putc(*s);
        s++;
    }
    catpp_putc('\n');
}

void catpp_print(long v) {
    char buf[32];
    int neg = 0;
    int i = 30;
    buf[31] = '\0';
    if (v < 0) { neg = 1; v = -v; }
    if (v == 0) { buf[--i] = '0'; }
    else {
        while (v > 0) {
            buf[--i] = '0' + (v % 10);
            v /= 10;
        }
    }
    if (neg) buf[--i] = '-';
    catpp_print_str(&buf[i]);
}

long catpp_len(void* arr) {
    return 0;  /* TODO: cần metadata */
}

int catpp_in(long v, void* arr) {
    return 0;  /* TODO */
}

/* ═══ Memory (bump allocator cho đến khi có heap thật) ═══ */
static uint8_t* heap_ptr = (uint8_t*)0x100000;  /* 1MB */
static uint8_t* heap_end = (uint8_t*)0x400000;  /* 4MB */

void* catpp_alloc(size_t n) {
    if (heap_ptr + n > heap_end) return NULL;
    void* p = heap_ptr;
    heap_ptr += n;
    return p;
}

void catpp_free(void* p) {
    (void)p;  /* no-op */
}

void catpp_memset(void* p, int c, size_t n) {
    uint8_t* b = (uint8_t*)p;
    for (size_t i = 0; i < n; i++) b[i] = (uint8_t)c;
}

void catpp_memcpy(void* d, const void* s, size_t n) {
    uint8_t* dd = (uint8_t*)d;
    const uint8_t* ss = (const uint8_t*)s;
    for (size_t i = 0; i < n; i++) dd[i] = ss[i];
}

size_t catpp_strlen(const char* s) {
    size_t n = 0;
    while (s[n]) n++;
    return n;
}

int catpp_strcmp(const char* a, const char* b) {
    while (*a && *a == *b) { a++; b++; }
    return (int)(uint8_t)*a - (int)(uint8_t)*b;
}

const char* catpp_str(long v) {
    static char buf[32];
    int neg = 0;
    int i = 30;
    buf[31] = '\0';
    if (v < 0) { neg = 1; v = -v; }
    if (v == 0) { buf[--i] = '0'; }
    else while (v > 0) { buf[--i] = '0' + (v % 10); v /= 10; }
    if (neg) buf[--i] = '-';
    return &buf[i];
}


/* ═══ Compiler runtime helpers ═══ */
void* memcpy(void* dest, const void* src, unsigned long n) {
    unsigned char* d = (unsigned char*)dest;
    const unsigned char* s = (const unsigned char*)src;
    for (unsigned long i = 0; i < n; i++) d[i] = s[i];
    return dest;
}

void* memset(void* dest, int c, unsigned long n) {
    unsigned char* d = (unsigned char*)dest;
    for (unsigned long i = 0; i < n; i++) d[i] = (unsigned char)c;
    return dest;
}

int memcmp(const void* a, const void* b, unsigned long n) {
    const unsigned char* x = (const unsigned char*)a;
    const unsigned char* y = (const unsigned char*)b;
    for (unsigned long i = 0; i < n; i++) {
        if (x[i] != y[i]) return x[i] - y[i];
    }
    return 0;
}
