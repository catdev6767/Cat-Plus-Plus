/* Kitty kernel — TTY manager */
#include <stdint.h>

extern void fb_clear_all(void);
extern void fb_draw_panel(void);
extern void fb_draw_dock(void);

volatile int g_tty = 0;  /* 0=GUI, 1=Shell, 2=Debug */

int tty_get(void) { return g_tty; }

void tty_switch(int n) {
    if (n == g_tty) return;
    if (n < 0) n = 0;
    if (n > 2) n = 2;
    g_tty = n;

    fb_clear_all();

    if (n == 0) {
        fb_draw_panel();
        fb_draw_dock();
    }
}
