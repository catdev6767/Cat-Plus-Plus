/* FelisOS — Filesystem với subdirectories */
#include <stdint.h>

#define MAX_FILES    128
#define MAX_NAME     32
#define MAX_DATA     2048
#define MAX_PATH     256

/* Forward declarations */
static int find_in_parent(int parent, const char* name);
int fs_create_at(int parent, const char* name, int is_dir);

typedef struct {
    char name[MAX_NAME];
    char data[MAX_DATA];
    int size;
    int used;
    int is_dir;
    int parent;    /* Index của thư mục cha, -1 = root */
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

static int s_len(const char* s) {
    int n = 0; while (s[n]) n++; return n;
}

void fs_init(void) {
    for (int i = 0; i < MAX_FILES; i++) fs_files[i].used = 0;
    fs_count = 0;
    /* Tạo file mẫu ở root */
    fs_create_at(-1, "readme.txt", 0);
    int idx = -1;
    for (int i = 0; i < fs_count; i++) {
        if (fs_files[i].used && s_eq(fs_files[i].name, "readme.txt")) {
            idx = i; break;
        }
    }
    if (idx >= 0) {
        const char* msg = "Welcome to FelisOS!\nRAM filesystem with subdirectories.";
        int i = 0;
        while (msg[i] && i < MAX_DATA - 1) { fs_files[idx].data[i] = msg[i]; i++; }
        fs_files[idx].data[i] = 0;
        fs_files[idx].size = i;
    }
}

/* Tìm file trong parent cụ thể */
static int find_in_parent(int parent, const char* name) {
    for (int i = 0; i < fs_count; i++) {
        if (fs_files[i].used && fs_files[i].parent == parent
            && s_eq(fs_files[i].name, name)) return i;
    }
    return -1;
}

/* Tìm file theo path tuyệt đối từ root */
int fs_find_path(const char* path) {
    if (!path || !*path) return -1;
    int cur = -1;  /* root */

    /* Nếu path bắt đầu bằng '/' thì từ root, ngược lại từ cwd — caller xử lý */
    const char* p = path;
    if (*p == '/') p++;

    char name[MAX_NAME];
    while (*p) {
        int i = 0;
        while (*p && *p != '/' && i < MAX_NAME - 1) name[i++] = *p++;
        name[i] = 0;
        if (*p == '/') p++;

        int idx = find_in_parent(cur, name);
        if (idx < 0) return -1;
        cur = idx;
    }
    return cur;
}

int fs_create_at(int parent, const char* name, int is_dir) {
    if (find_in_parent(parent, name) >= 0) return -1;
    if (fs_count >= MAX_FILES) return -1;
    s_copy(fs_files[fs_count].name, name, MAX_NAME);
    fs_files[fs_count].data[0] = 0;
    fs_files[fs_count].size = 0;
    fs_files[fs_count].used = 1;
    fs_files[fs_count].is_dir = is_dir;
    fs_files[fs_count].parent = parent;
    fs_count++;
    return 0;
}

int fs_create(const char* name, int is_dir) {
    return fs_create_at(-1, name, is_dir);
}

int fs_delete(const char* name) {
    int idx = fs_find_path(name);
    if (idx < 0) return -1;
    /* Xóa cả con nếu là dir */
    if (fs_files[idx].is_dir) {
        for (int i = 0; i < fs_count; i++) {
            if (fs_files[i].used && fs_files[i].parent == idx) {
                fs_files[i].used = 0;
            }
        }
    }
    fs_files[idx].used = 0;
    return 0;
}

const char* fs_read(const char* name, int* size_out) {
    int idx = fs_find_path(name);
    if (idx < 0) { if (size_out) *size_out = 0; return 0; }
    if (size_out) *size_out = fs_files[idx].size;
    return fs_files[idx].data;
}

int fs_write(const char* name, const char* data, int size) {
    int idx = fs_find_path(name);
    if (idx < 0) {
        if (fs_create(name, 0) < 0) return -1;
        idx = fs_find_path(name);
    }
    if (size >= MAX_DATA) size = MAX_DATA - 1;
    for (int i = 0; i < size; i++) fs_files[idx].data[i] = data[i];
    fs_files[idx].data[size] = 0;
    fs_files[idx].size = size;
    return 0;
}

int fs_append(const char* name, const char* data, int size) {
    int idx = fs_find_path(name);
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

int fs_get_parent(int i) {
    if (i < 0 || i >= fs_count) return -2;
    return fs_files[i].parent;
}

/* Liệt kê con của 1 thư mục */
int fs_list_children(int parent, int* out, int max) {
    int n = 0;
    for (int i = 0; i < fs_count && n < max; i++) {
        if (fs_files[i].used && fs_files[i].parent == parent) {
            out[n++] = i;
        }
    }
    return n;
}

/* Join path */
void fs_join(char* out, const char* base, const char* name, int max) {
    int j = 0;
    if (base[0]) {
        for (int i = 0; base[i] && j < max - 1; i++) out[j++] = base[i];
        if (j > 0 && out[j-1] != '/' && j < max - 1) out[j++] = '/';
    }
    for (int i = 0; name[i] && j < max - 1; i++) out[j++] = name[i];
    out[j] = 0;
}

/* Resolve path có hỗ trợ relative + .. */
int fs_resolve(int cwd, const char* path) {
    if (!path || !*path) return cwd;
    int cur = (*path == '/') ? -1 : cwd;
    const char* p = path;
    if (*p == '/') p++;
    char name[MAX_NAME];
    while (*p) {
        int i = 0;
        while (*p && *p != '/' && i < MAX_NAME - 1) name[i++] = *p++;
        name[i] = 0;
        if (*p == '/') p++;
        if (i == 0) continue;
        if (s_eq(name, ".")) continue;
        if (s_eq(name, "..")) {
            if (cur >= 0) cur = fs_files[cur].parent;
            continue;
        }
        int idx = find_in_parent(cur, name);
        if (idx < 0) return -2;  /* Không tìm thấy */
        cur = idx;
    }
    return cur;
}

/* Lấy đường dẫn tuyệt đối của entry */
void fs_path_of(int idx, char* out, int max) {
    if (idx < 0) { s_copy(out, "/", max); return; }
    char parts[16][MAX_NAME];
    int n = 0;
    int cur = idx;
    while (cur >= 0 && n < 16) {
        s_copy(parts[n++], fs_files[cur].name, MAX_NAME);
        cur = fs_files[cur].parent;
    }
    int j = 0;
    if (n == 0 && j < max - 1) out[j++] = '/';
    for (int i = n - 1; i >= 0; i--) {
        if (j < max - 1) out[j++] = '/';
        for (int k = 0; parts[i][k] && j < max - 1; k++) out[j++] = parts[i][k];
    }
    out[j] = 0;
}
