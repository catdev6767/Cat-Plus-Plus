/* Kitty OS — Shell với line editor */
#include "catpp_rt.h"
#include "utils.h"

extern void idt_init(void);
extern unsigned char keyboard_getchar_raw(void);
extern void catpp_putc(char c);
extern void catpp_print_str(const char* s);
extern int shell_execute(char* cmdline);
extern int shell_get_prompt(char* buf);

#define KEY_UP      128
#define KEY_DOWN    129
#define KEY_LEFT    130
#define KEY_RIGHT   131
#define KEY_HOME    132
#define KEY_END     133
#define KEY_DELETE  134

#define LINE_MAX 256
#define HIST_MAX 32

static char line[LINE_MAX];
static int line_len = 0, cursor = 0;
static char history[HIST_MAX][LINE_MAX];
static int hist_count = 0, hist_pos = -1;
static char hist_saved[LINE_MAX];

static void redraw(void) {
    int saved = cursor;    /* Lưu vị trí cursor */
    /* Về đầu dòng */
    int n = cursor;
    while (n > 0) { catpp_putc('\b'); n--; }
    /* In lại dòng */
    for (int i = 0; i < line_len; i++) catpp_putc(line[i]);
    /* In 1 space để xóa ký tự thừa (nếu dòng ngắn hơn trước) */
    catpp_putc(' ');
    /* Quay lại đầu dòng */
    int total = line_len + 1;
    while (total > 0) { catpp_putc('\b'); total--; }
    /* Tới vị trí cursor */
    for (int i = 0; i < saved; i++) catpp_putc(line[i]);
}

static void insert_char(char c) {
    if (line_len >= LINE_MAX - 1) return;
    for (int i = line_len; i > cursor; i--) line[i] = line[i-1];
    line[cursor] = c; cursor++; line_len++; line[line_len] = 0;
    redraw();
}

static void do_backspace(void) {
    if (cursor == 0) return;
    for (int i = cursor - 1; i < line_len - 1; i++) line[i] = line[i+1];
    cursor--; line_len--; line[line_len] = 0;
    redraw();
}

static void do_delete(void) {
    if (cursor >= line_len) return;
    for (int i = cursor; i < line_len - 1; i++) line[i] = line[i+1];
    line_len--; line[line_len] = 0;
    redraw();
}

static void move_left(void) {
    if (cursor > 0) { cursor--; catpp_putc('\b'); }
}

static void move_right(void) {
    if (cursor < line_len) { catpp_putc(line[cursor]); cursor++; }
}

static void move_home(void) {
    while (cursor > 0) { cursor--; catpp_putc('\b'); }
}

static void move_end(void) {
    while (cursor < line_len) { catpp_putc(line[cursor]); cursor++; }
}

static void clear_line_visual(void) {
    while (cursor > 0) { catpp_putc('\b'); cursor--; }
    for (int i = 0; i < line_len; i++) catpp_putc(' ');
    for (int i = 0; i < line_len; i++) catpp_putc('\b');
    line_len = 0; cursor = 0; line[0] = 0;
}

static void set_line(const char* s) {
    clear_line_visual();
    int i = 0;
    while (s[i] && i < LINE_MAX - 1) { line[i] = s[i]; i++; }
    line[i] = 0; line_len = i; cursor = i;
    for (int j = 0; j < line_len; j++) catpp_putc(line[j]);
}

/* Tab completion */
extern const char* shell_commands[];

static void tab_complete(void) {
    char match[LINE_MAX];
    int count = 0;
    for (int i = 0; shell_commands[i]; i++) {
        int ok = 1;
        for (int j = 0; j < line_len; j++) {
            if (line[j] != shell_commands[i][j]) { ok = 0; break; }
        }
        if (ok) {
            if (count == 0) {
                int k = 0;
                while (shell_commands[i][k]) { match[k] = shell_commands[i][k]; k++; }
                match[k] = 0;
            } else {
                int k = 0;
                while (match[k] && shell_commands[i][k] && match[k] == shell_commands[i][k]) k++;
                match[k] = 0;
            }
            count++;
        }
    }
    if (count == 1) { set_line(match); insert_char(' '); }
    else if (count > 1 && match[0]) set_line(match);
}

static void add_history(const char* cmd) {
    if (cmd[0] == 0) return;
    if (hist_count > 0 && str_eq(history[hist_count-1], cmd)) return;
    if (hist_count < HIST_MAX) {
        int i = 0;
        while (cmd[i] && i < LINE_MAX - 1) { history[hist_count][i] = cmd[i]; i++; }
        history[hist_count][i] = 0;
        hist_count++;
    } else {
        for (int j = 0; j < HIST_MAX - 1; j++) {
            int k = 0;
            while (history[j+1][k]) { history[j][k] = history[j+1][k]; k++; }
            history[j][k] = 0;
        }
        int i = 0;
        while (cmd[i] && i < LINE_MAX - 1) { history[HIST_MAX-1][i] = cmd[i]; i++; }
        history[HIST_MAX-1][i] = 0;
    }
}

void hist_dump(void) {
    char buf[8];
    for (int i = 0; i < hist_count; i++) {
        int n = i + 1, j = 7; buf[7] = 0;
        while (n > 0) { buf[--j] = '0' + (n % 10); n /= 10; }
        catpp_print_str(&buf[j]);
        catpp_print_str(history[i]);
    }
}

static void hist_prev(void) {
    if (hist_count == 0) return;
    if (hist_pos == -1) {
        for (int i = 0; i <= line_len; i++) hist_saved[i] = line[i];
        hist_pos = hist_count - 1;
    } else if (hist_pos > 0) hist_pos--;
    else return;
    set_line(history[hist_pos]);
}

static void hist_next(void) {
    if (hist_pos == -1) return;
    if (hist_pos < hist_count - 1) { hist_pos++; set_line(history[hist_pos]); }
    else { hist_pos = -1; set_line(hist_saved); }
}

static void print_prompt(void) {
    char buf[256];
    shell_get_prompt(buf);
    int i = 0;
    while (buf[i]) catpp_putc(buf[i++]);
    catpp_putc(' ');
    catpp_putc('$');
    catpp_putc(' ');
}

static void read_line(void) {
    line_len = 0; cursor = 0; line[0] = 0; hist_pos = -1;
    while (1) {
        unsigned char c = keyboard_getchar_raw();
        if (c == '\n' || c == '\r') {
            line[line_len] = 0;
            catpp_putc('\n');
            add_history(line);
            return;
        }
        if (c == '\b') { do_backspace(); continue; }
        if (c == KEY_DELETE) { do_delete(); continue; }
        if (c == KEY_LEFT) { move_left(); continue; }
        if (c == KEY_RIGHT) { move_right(); continue; }
        if (c == KEY_HOME) { move_home(); continue; }
        if (c == KEY_END) { move_end(); continue; }
        if (c == KEY_UP) { hist_prev(); continue; }
        if (c == KEY_DOWN) { hist_next(); continue; }
        if (c == '\t') { tab_complete(); continue; }
        if (c == 27) { continue; }  /* Escape — bỏ qua */
        if (c >= 32 && c < 128) insert_char((char)c);
    }
}

void shell_run(void) {
    idt_init();
    extern void cmd_clear(void);
    cmd_clear();
    catpp_print_str("Kitty OS v0.2");
    catpp_print_str("Type 'help' for commands.");
    catpp_print_str("");
    while (1) {
        print_prompt();
        read_line();
        if (line_len == 0) continue;
        shell_execute(line);
    }
}
