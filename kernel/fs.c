/* Felis OS — RAM filesystem (flat, no subdirs yet) */
#include <stdint.h>

#define MAX_FILES    64
#define MAX_NAME     32
#define MAX_DATA     2048

typedef struct {
    char name[MAX_NAME];
    char data[MAX_DATA];
    int size;
    int used;
    int is_dir;
} FileEntry;

static FileEntry fs_files[MAX_FILES];
static int fs_count = 0;

static int s_eq(const char* a, const char* b) {
    while (*a && *a == *b) { a++; b++; }
    return *a == *b;
}

static void s_copy(char* d, const char* s, int max) {
    int i = 0;
    while (s[i] && i < max - 1) { d[i] = s[i]; i++; }
    d[i] = 0;
}

static int find_file(const char* name) {
    for (int i = 0; i < fs_count; i++) {
        if (fs_files[i].used && s_eq(fs_files[i].name, name)) return i;
    }
    return -1;
}

void fs_init(void) {
    for (int i = 0; i < MAX_FILES; i++) fs_files[i].used = 0;
    fs_count = 0;
    /* Tạo file mẫu */
    extern int fs_create(const char* name, int is_dir);
    fs_create("readme.txt", 0);
    int idx = find_file("readme.txt");
    const char* msg = "Welcome to Felis OS!\nThis is a RAM filesystem.";
    int i = 0;
    while (msg[i] && i < MAX_DATA - 1) { fs_files[idx].data[i] = msg[i]; i++; }
    fs_files[idx].data[i] = 0;
    fs_files[idx].size = i;
}

int fs_create(const char* name, int is_dir) {
    if (find_file(name) >= 0) return -1;
    if (fs_count >= MAX_FILES) return -1;
    s_copy(fs_files[fs_count].name, name, MAX_NAME);
    fs_files[fs_count].data[0] = 0;
    fs_files[fs_count].size = 0;
    fs_files[fs_count].used = 1;
    fs_files[fs_count].is_dir = is_dir;
    fs_count++;
    return 0;
}

int fs_delete(const char* name) {
    int idx = find_file(name);
    if (idx < 0) return -1;
    fs_files[idx].used = 0;
    return 0;
}

const char* fs_read(const char* name, int* size_out) {
    int idx = find_file(name);
    if (idx < 0) { if (size_out) *size_out = 0; return 0; }
    if (size_out) *size_out = fs_files[idx].size;
    return fs_files[idx].data;
}

int fs_write(const char* name, const char* data, int size) {
    int idx = find_file(name);
    if (idx < 0) {
        if (fs_create(name, 0) < 0) return -1;
        idx = find_file(name);
    }
    if (size >= MAX_DATA) size = MAX_DATA - 1;
    for (int i = 0; i < size; i++) fs_files[idx].data[i] = data[i];
    fs_files[idx].data[size] = 0;
    fs_files[idx].size = size;
    return 0;
}

int fs_append(const char* name, const char* data, int size) {
    int idx = find_file(name);
    if (idx < 0) return fs_write(name, data, size);
    int cur = fs_files[idx].size;
    if (cur + size >= MAX_DATA) size = MAX_DATA - 1 - cur;
    for (int i = 0; i < size; i++) fs_files[idx].data[cur + i] = data[i];
    fs_files[idx].size = cur + size;
    fs_files[idx].data[fs_files[idx].size] = 0;
    return 0;
}

int fs_count_files(void) { return fs_count; }

const char* fs_get_name(int i) {
    if (i < 0 || i >= fs_count) return 0;
    if (!fs_files[i].used) return 0;
    return fs_files[i].name;
}

int fs_is_dir(int i) {
    if (i < 0 || i >= fs_count) return 0;
    return fs_files[i].is_dir;
}

int fs_file_size(int i) {
    if (i < 0 || i >= fs_count) return 0;
    return fs_files[i].size;
}
