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
extern void fs_init(void);

extern void hist_dump(void);
extern unsigned long strlen(const char* s);
extern char* strcpy(char* d, const char* s);
extern char* strcat(char* d, const char* s);
extern int strcmp(const char* a, const char* b);
extern int strncmp(const char* a, const char* b, unsigned long n);
extern char* strtok(char* s, const char* delim);

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
    int total = fs_count_files();
    int shown = 0;
    for (int i = 0; i < total; i++) {
        const char* n = fs_get_name(i);
        if (!n) continue;
        char buf[128];
        strcpy(buf, fs_is_dir(i) ? "[DIR]  " : "       ");
        strcat(buf, n);
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
        shown++;
    }
    if (shown == 0) catpp_print_str("(empty)");
}

static void cmd_cat(char* arg) {
    if (!arg || !*arg) { catpp_print_str("Dung: cat FILE"); return; }
    int sz;
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
    if (fs_create(arg, 0) < 0) catpp_print_str("Loi tao file");
}

static void cmd_mkdir(char* arg) {
    if (!arg || !*arg) { catpp_print_str("Dung: mkdir DIR"); return; }
    if (fs_create(arg, 1) < 0) catpp_print_str("Loi tao thu muc");
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
    "echo","history","ls","cat","touch","mkdir","rm","rmdir",
    "write","append","wc","sleep","reboot","halt","exit", 0
};

int shell_execute(char* cmdline) {
    while (*cmdline == ' ') cmdline++;
    int len = strlen(cmdline);
    while (len > 0 && cmdline[len-1] == ' ') cmdline[--len] = 0;
    if (len == 0) return 0;

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
    if (strcmp(cmdline, "cat") == 0)     { cmd_cat(arg);  return 0; }
    if (strcmp(cmdline, "touch") == 0)   { cmd_touch(arg);return 0; }
    if (strcmp(cmdline, "mkdir") == 0)   { cmd_mkdir(arg);return 0; }
    if (strcmp(cmdline, "rm") == 0)      { cmd_rm(arg);   return 0; }
    if (strcmp(cmdline, "rmdir") == 0)   { cmd_rm(arg);   return 0; }
    if (strcmp(cmdline, "write") == 0)   { cmd_write(arg);return 0; }
    if (strcmp(cmdline, "append") == 0)  { cmd_append(arg);return 0; }
    if (strcmp(cmdline, "wc") == 0)      { cmd_wc(arg);   return 0; }
    if (strcmp(cmdline, "sleep") == 0)   { cmd_sleep(arg);return 0; }
    if (strcmp(cmdline, "reboot") == 0)  { cmd_reboot();  return 0; }
    if (strcmp(cmdline, "halt") == 0)    { cmd_halt();    return 0; }
    if (strcmp(cmdline, "exit") == 0)    { cmd_halt();    return 0; }

    catpp_print_str("Lenh khong ton tai. Go 'help'.");
    return -1;
}

/* Prompt */
int shell_get_prompt(char* buf) {
    strcpy(buf, "felis");
    return 0;
}

/* Public init */
void commands_init(void) {
    fs_init();
}
