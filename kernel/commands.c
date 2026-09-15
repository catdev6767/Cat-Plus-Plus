/* Felis OS — Shell commands */
#include "catpp_rt.h"
#include "utils.h"

extern void catpp_putc(char c);
extern void catpp_print_str(const char* s);
extern void catpp_print(long v);

extern int fs_create(const char* name, int is_dir);
extern int fs_delete(const char* name);
extern const char* fs_read(const char* name, int* size_out);
extern int fs_write(const char* name, const char* data, int size);
extern int fs_append(const char* name, const char* data, int size);
extern int fs_count_files(void);
extern const char* fs_get_name(int i);
extern int fs_is_dir(int i);
extern int fs_file_size(int i);
extern int fs_get_parent(int i);
extern int fs_list_children(int parent, int* out, int max);
extern int fs_resolve(int cwd, const char* path);
extern void fs_path_of(int idx, char* out, int max);
extern void fs_join(char* out, const char* base, const char* name, int max);
extern int fs_create_at(int parent, const char* name, int is_dir);
extern void fs_init(void);

extern void hist_dump(void);
extern unsigned long strlen(const char* s);
extern char* strcpy(char* d, const char* s);
extern char* strcat(char* d, const char* s);
extern int strcmp(const char* a, const char* b);
extern int strncmp(const char* a, const char* b, unsigned long n);
extern char* strtok(char* s, const char* delim);

/* ═══ REDIRECT + PIPE ═══ */
extern void (*g_out_hook)(char);

static char g_redir_buf[4096];
static int  g_redir_len = 0;
static char* g_pipe_input = 0;
static int   g_pipe_input_size = 0;
static int   g_use_pipe_in = 0;

static void redir_hook(char ch) {
    if (g_redir_len < 4095) g_redir_buf[g_redir_len++] = ch;
    g_redir_buf[g_redir_len] = 0;
}

static void redir_begin(void) {
    g_redir_len = 0;
    g_redir_buf[0] = 0;
    g_out_hook = redir_hook;
}

static void redir_end(void) {
    g_out_hook = 0;
}

static int my_atoi(const char* s) {
    int n = 0;
    while (*s >= '0' && *s <= '9') n = n * 10 + (*s++ - '0');
    return n;
}

static int is_digit_str(const char* s) {
    if (!s || !*s) return 0;
    while (*s) { if (*s < '0' || *s > '9') return 0; s++; }
    return 1;
}

/* ═══ CWD ═══ */
static int g_cwd = -1;   /* -1 = root */

void cmd_pwd(void) {
    char buf[256];
    fs_path_of(g_cwd, buf, sizeof(buf));
    catpp_print_str(buf);
}

static void cmd_cd(char* arg) {
    if (!arg || !*arg || (arg[0] == '~' && !arg[1])) {
        g_cwd = -1; return;
    }
    int idx = fs_resolve(g_cwd, arg);
    if (idx == -2) { catpp_print_str("Khong tim thay"); return; }
    if (idx >= 0 && !fs_is_dir(idx)) {
        catpp_print_str("Khong phai thu muc"); return;
    }
    g_cwd = idx;
}

/* ═══ HELP ═══ */
static void cmd_help(void) {
    catpp_print_str("Felis OS Shell v0.2");
    catpp_print_str("Commands:");
    catpp_print_str("  help              Hien thi tro giup");
    catpp_print_str("  clear             Xoa man hinh");
    catpp_print_str("  info              Thong tin he thong");
    catpp_print_str("  uname             Ten he thong");
    catpp_print_str("  whoami            Ten nguoi dung");
    catpp_print_str("  date              Ngay gio");
    catpp_print_str("  uptime            Thoi gian chay");
    catpp_print_str("  mem               Thong tin bo nho");
    catpp_print_str("  echo TEXT         In TEXT");
    catpp_print_str("  history           Xem lich su lenh");
    catpp_print_str("  ls                Liet ke file");
    catpp_print_str("  cd DIR            Doi thu muc");
    catpp_print_str("  pwd               In thu muc hien tai");
    catpp_print_str("  cat FILE          Doc file");
    catpp_print_str("  touch FILE        Tao file rong");
    catpp_print_str("  mkdir DIR         Tao thu muc");
    catpp_print_str("  rm FILE           Xoa file");
    catpp_print_str("  rmdir DIR         Xoa thu muc");
    catpp_print_str("  write FILE TEXT   Ghi vao file");
    catpp_print_str("  append FILE TEXT  Them vao file");
    catpp_print_str("  wc FILE           Dem tu/ky tu");
    catpp_print_str("  sleep N           Doi N giay (uoc le)");
    catpp_print_str("  reboot            Khoi dong lai");
    catpp_print_str("  halt              Dung CPU");
    catpp_print_str("  exit              Thoat shell");
}

/* ═══ SYSTEM ═══ */
void cmd_clear(void) {
    volatile unsigned short* vga = (volatile unsigned short*)0xB8000;
    for (int i = 0; i < 80 * 25; i++) vga[i] = (0x0F << 8) | ' ';
}

static void cmd_info(void) {
    catpp_print_str("Felis OS v0.2");
    catpp_print_str("Kernel: C freestanding");
    catpp_print_str("CPU: i386 32-bit");
    catpp_print_str("Shell: full line editor");
    catpp_print_str("FS: RAM (64 files, 2KB each)");
}

static void cmd_uname(void) { catpp_print_str("Felis"); }
static void cmd_whoami(void) { catpp_print_str("cat"); }

static void cmd_date(void) {
    /* Đọc CMOS real-time clock */
    extern unsigned char inb(unsigned short);
    extern void outb(unsigned short, unsigned char);
    (void)inb; (void)outb;
    catpp_print_str("Date: khong ho tro RTC");
}

static void cmd_uptime(void) {
    catpp_print_str("Uptime: chua ho tro timer");
}

static void cmd_mem(void) {
    catpp_print_str("Memory: 128 MB total");
    catpp_print_str("Used: ~50 KB (kernel)");
}

static void cmd_echo(char* arg) { catpp_print_str(arg); }

/* ═══ FS ═══ */
static void cmd_ls(void) {
    int children[128];
    int n = fs_list_children(g_cwd, children, 128);
    if (n == 0) { catpp_print_str("(empty)"); return; }
    for (int k = 0; k < n; k++) {
        int i = children[k];
        const char* name = fs_get_name(i);
        if (!name) continue;
        char buf[160];
        strcpy(buf, fs_is_dir(i) ? "[DIR]  " : "       ");
        strcat(buf, name);
        if (!fs_is_dir(i)) {
            strcat(buf, " (");
            int sz = fs_file_size(i);
            char num[16]; int j = 15; num[15] = 0;
            if (sz == 0) num[--j] = '0';
            while (sz > 0) { num[--j] = '0' + (sz % 10); sz /= 10; }
            strcat(buf, &num[j]);
            strcat(buf, " B)");
        }
        catpp_print_str(buf);
    }
}

static void cmd_cat(char* arg) {
    if (!arg || !*arg) { catpp_print_str("Dung: cat FILE"); return; }
    int idx = fs_resolve(g_cwd, arg);
    if (idx < 0) { catpp_print_str("File khong ton tai"); return; }
    int sz = fs_file_size(idx);
    const char* data = fs_read(arg, &sz);
    if (!data) { catpp_print_str("File khong ton tai"); return; }
    if (sz == 0) { catpp_print_str("(empty)"); return; }
    /* In từng dòng */
    char buf[300];
    int j = 0;
    for (int i = 0; i < sz; i++) {
        char c = data[i];
        if (c == '\n') {
            buf[j] = 0;
            catpp_print_str(buf);
            j = 0;
        } else if (j < 299) {
            buf[j++] = c;
        }
    }
    if (j > 0) { buf[j] = 0; catpp_print_str(buf); }
}

static void cmd_touch(char* arg) {
    if (!arg || !*arg) { catpp_print_str("Dung: touch FILE"); return; }
    if (fs_create_at(g_cwd, arg, 0) < 0) catpp_print_str("Loi tao file");
}


static void cmd_mkdir(char* arg) {
    if (!arg || !*arg) { catpp_print_str("Dung: mkdir DIR"); return; }
    if (fs_create_at(g_cwd, arg, 1) < 0) catpp_print_str("Loi tao thu muc");
}

static void cmd_rm(char* arg) {
    if (!arg || !*arg) { catpp_print_str("Dung: rm FILE"); return; }
    if (fs_delete(arg) < 0) catpp_print_str("File khong ton tai");
}

static void cmd_write(char* arg) {
    if (!arg || !*arg) { catpp_print_str("Dung: write FILE TEXT"); return; }
    char* space = 0;
    for (char* p = arg; *p; p++) if (*p == ' ') { space = p; break; }
    if (!space) { catpp_print_str("Thieu noi dung"); return; }
    *space = 0;
    char* text = space + 1;
    fs_write(arg, text, strlen(text));
}

static void cmd_append(char* arg) {
    if (!arg || !*arg) { catpp_print_str("Dung: append FILE TEXT"); return; }
    char* space = 0;
    for (char* p = arg; *p; p++) if (*p == ' ') { space = p; break; }
    if (!space) { catpp_print_str("Thieu noi dung"); return; }
    *space = 0;
    char* text = space + 1;
    fs_append(arg, text, strlen(text));
    fs_append(arg, "\n", 1);
}

static void cmd_wc(char* arg) {
    if (!arg || !*arg) { catpp_print_str("Dung: wc FILE"); return; }
    int sz;
    const char* data = fs_read(arg, &sz);
    if (!data) { catpp_print_str("File khong ton tai"); return; }
    int lines = 0, words = 0, in_word = 0;
    for (int i = 0; i < sz; i++) {
        char c = data[i];
        if (c == '\n') lines++;
        if (c == ' ' || c == '\n' || c == '\t') in_word = 0;
        else if (!in_word) { in_word = 1; words++; }
    }
    char buf[64];
    strcpy(buf, "Lines: ");
    /* Number */
    { char n[16]; int j = 15; n[15] = 0; int v = lines;
      if (v==0) n[--j]='0';
      while (v>0) { n[--j]='0'+(v%10); v/=10; }
      strcat(buf, &n[j]); }
    strcat(buf, " Words: ");
    { char n[16]; int j = 15; n[15] = 0; int v = words;
      if (v==0) n[--j]='0';
      while (v>0) { n[--j]='0'+(v%10); v/=10; }
      strcat(buf, &n[j]); }
    strcat(buf, " Chars: ");
    { char n[16]; int j = 15; n[15] = 0; int v = sz;
      if (v==0) n[--j]='0';
      while (v>0) { n[--j]='0'+(v%10); v/=10; }
      strcat(buf, &n[j]); }
    catpp_print_str(buf);
}

static void cmd_history(void) { hist_dump(); }

static void cmd_sleep(char* arg) {
    if (!arg || !*arg) return;
    int n = 0;
    for (char* p = arg; *p >= '0' && *p <= '9'; p++) n = n*10 + (*p - '0');
    /* Busy wait — ước lệ */
    for (volatile long i = 0; i < (long)n * 50000000L; i++);
}

static void cmd_reboot(void) {
    __asm__ volatile("mov $0xFE, %al; outb %al, $0x64");
}

static void cmd_halt(void) {
    catpp_print_str("Halted.");
    __asm__ volatile("cli; hlt");
}

/* ═══ COMMAND TABLE ═══ */
const char* shell_commands[] = {
    "help","clear","info","uname","whoami","date","uptime","mem",
    "echo","history",
    "ls","cd","pwd","cat","touch","mkdir","rm","rmdir",
    "write","append","wc","sleep","reboot","halt","exit", 0
};

static void cmd_head(char* arg);
static void cmd_tail(char* arg);
static void cmd_grep(char* arg);

static int parse_redirect_pipe(char* cmdline);

int shell_execute(char* cmdline) {
    while (*cmdline == ' ') cmdline++;
    int len = strlen(cmdline);
    while (len > 0 && cmdline[len-1] == ' ') cmdline[--len] = 0;
    if (len == 0) return 0;

    /* Check redirect + pipe trước */
    if (parse_redirect_pipe(cmdline)) return 0;

    char* arg = cmdline;
    while (*arg && *arg != ' ') arg++;
    if (*arg) { *arg = 0; arg++; while (*arg == ' ') arg++; }

    if (strcmp(cmdline, "help") == 0)    { cmd_help();    return 0; }
    if (strcmp(cmdline, "clear") == 0)   { cmd_clear();   return 0; }
    if (strcmp(cmdline, "info") == 0)    { cmd_info();    return 0; }
    if (strcmp(cmdline, "uname") == 0)   { cmd_uname();   return 0; }
    if (strcmp(cmdline, "whoami") == 0)  { cmd_whoami();  return 0; }
    if (strcmp(cmdline, "date") == 0)    { cmd_date();    return 0; }
    if (strcmp(cmdline, "uptime") == 0)  { cmd_uptime();  return 0; }
    if (strcmp(cmdline, "mem") == 0)     { cmd_mem();     return 0; }
    if (strcmp(cmdline, "echo") == 0)    { cmd_echo(arg); return 0; }
    if (strcmp(cmdline, "history") == 0) { cmd_history(); return 0; }
    if (strcmp(cmdline, "ls") == 0)      { cmd_ls();      return 0; }
    if (strcmp(cmdline, "cd") == 0)      { cmd_cd(arg);   return 0; }
    if (strcmp(cmdline, "pwd") == 0)     { cmd_pwd();     return 0; }
    if (strcmp(cmdline, "cat") == 0)     { cmd_cat(arg);  return 0; }
    if (strcmp(cmdline, "touch") == 0)   { cmd_touch(arg);return 0; }
    if (strcmp(cmdline, "mkdir") == 0)   { cmd_mkdir(arg);return 0; }
    if (strcmp(cmdline, "rm") == 0)      { cmd_rm(arg);   return 0; }
    if (strcmp(cmdline, "rmdir") == 0)   { cmd_rm(arg);   return 0; }
    if (strcmp(cmdline, "write") == 0)   { cmd_write(arg);return 0; }
    if (strcmp(cmdline, "append") == 0)  { cmd_append(arg);return 0; }
    if (strcmp(cmdline, "wc") == 0)      { cmd_wc(arg);   return 0; }
    if (strcmp(cmdline, "head") == 0)    { cmd_head(arg); return 0; }
    if (strcmp(cmdline, "tail") == 0)    { cmd_tail(arg); return 0; }
    if (strcmp(cmdline, "grep") == 0)    { cmd_grep(arg); return 0; }
    if (strcmp(cmdline, "sleep") == 0)   { cmd_sleep(arg);return 0; }
    if (strcmp(cmdline, "reboot") == 0)  { cmd_reboot();  return 0; }
    if (strcmp(cmdline, "halt") == 0)    { cmd_halt();    return 0; }
    if (strcmp(cmdline, "exit") == 0)    { cmd_halt();    return 0; }

    catpp_print_str("Lenh khong ton tai. Go 'help'.");
    return -1;
}

/* Prompt */
int shell_get_prompt(char* buf) {
    char path[200];
    fs_path_of(g_cwd, path, sizeof(path));
    if (path[0] == '/' && path[1] == 0) {
        strcpy(buf, "felis:/");
    } else {
        strcpy(buf, "felis:");
        strcat(buf, path);
    }
    return 0;
}

/* ═══ parse_redirect_pipe ═══ */
static int parse_redirect_pipe(char* cmdline) {
    /* Tìm pipe '|' */
    char* pipe_pos = 0;
    for (char* p = cmdline; *p; p++) {
        if (*p == '|') { pipe_pos = p; break; }
    }
    if (pipe_pos) {
        *pipe_pos = 0;
        char* cmd1 = cmdline;
        char* cmd2 = pipe_pos + 1;
        while (*cmd1 == ' ') cmd1++;
        while (*cmd2 == ' ') cmd2++;
        char* e = cmd1 + strlen(cmd1);
        while (e > cmd1 && *(e-1) == ' ') *--e = 0;
        e = cmd2 + strlen(cmd2);
        while (e > cmd2 && *(e-1) == ' ') *--e = 0;

        redir_begin();
        shell_execute(cmd1);
        redir_end();

        /* Lưu kết quả vào pipe input */
        g_pipe_input = g_redir_buf;
        g_pipe_input_size = g_redir_len;
        g_use_pipe_in = 1;

        shell_execute(cmd2);

        g_use_pipe_in = 0;
        g_pipe_input = 0;
        return 1;
    }

    /* Tìm '>' hoặc '>>' */
    char* redir = 0;
    int is_append = 0;
    for (char* p = cmdline; *p; p++) {
        if (*p == '>' && *(p+1) == '>') { redir = p; is_append = 1; break; }
        if (*p == '>') { redir = p; is_append = 0; break; }
    }
    if (redir) {
        *redir = 0;
        char* fname = redir + (is_append ? 2 : 1);
        while (*fname == ' ') fname++;
        char* e = fname + strlen(fname);
        while (e > fname && *(e-1) == ' ') *--e = 0;

        char* cmd = cmdline;
        while (*cmd == ' ') cmd++;
        e = cmd + strlen(cmd);
        while (e > cmd && *(e-1) == ' ') *--e = 0;

        redir_begin();
        shell_execute(cmd);
        redir_end();

        if (is_append) fs_append(fname, g_redir_buf, g_redir_len);
        else fs_write(fname, g_redir_buf, g_redir_len);
        return 1;
    }

    return 0;
}

/* ═══ head/tail/grep ═══ */
static const char* get_input_data(int* size_out) {
    if (g_use_pipe_in && g_pipe_input) {
        *size_out = g_pipe_input_size;
        return g_pipe_input;
    }
    return 0;
}

static void cmd_head(char* arg) {
    int n = 10;
    if (arg && is_digit_str(arg)) n = my_atoi(arg);

    int size = 0;
    const char* data = get_input_data(&size);
    if (!data) { catpp_print_str("head: can pipe hoac file"); return; }

    int lines = 0;
    for (int i = 0; i < size && lines < n; i++) {
        char ch = data[i];
        char b[2]; b[0] = ch; b[1] = 0;
        /* catpp_putc để giữ nguyên */
        catpp_putc(ch);
        if (ch == '\n') lines++;
    }
}

static void cmd_tail(char* arg) {
    int n = 10;
    if (arg && is_digit_str(arg)) n = my_atoi(arg);

    int size = 0;
    const char* data = get_input_data(&size);
    if (!data) { catpp_print_str("tail: can pipe hoac file"); return; }

    /* Đếm tổng dòng */
    int total = 0;
    for (int i = 0; i < size; i++) if (data[i] == '\n') total++;
    int start_line = total - n;
    if (start_line < 0) start_line = 0;

    int cur = 0;
    for (int i = 0; i < size; i++) {
        if (cur >= start_line) catpp_putc(data[i]);
        if (data[i] == '\n') cur++;
    }
}

static void cmd_grep(char* arg) {
    if (!arg || !*arg) { catpp_print_str("grep: thieu pattern"); return; }

    int size = 0;
    const char* data = get_input_data(&size);
    if (!data) { catpp_print_str("grep: can pipe"); return; }

    int plen = strlen(arg);
    int i = 0;
    while (i < size) {
        int j = i;
        while (j < size && data[j] != '\n') j++;
        /* Dòng từ i đến j */
        int line_len = j - i;
        int match = 0;
        for (int k = 0; k + plen <= line_len; k++) {
            int ok = 1;
            for (int m = 0; m < plen; m++) {
                if (data[i + k + m] != arg[m]) { ok = 0; break; }
            }
            if (ok) { match = 1; break; }
        }
        if (match) {
            for (int k = i; k < j; k++) catpp_putc(data[k]);
            catpp_putc('\n');
        }
        i = j + 1;
    }
}

/* Public init */
void commands_init(void) {
    fs_init();
}
