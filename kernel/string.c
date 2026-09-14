#include <stdint.h>

unsigned long strlen(const char* s) {
    unsigned long n = 0;
    while (s[n]) n++;
    return n;
}

char* strcpy(char* d, const char* s) {
    char* r = d;
    while ((*d++ = *s++));
    return r;
}

char* strncpy(char* d, const char* s, unsigned long n) {
    char* r = d;
    while (n && (*d++ = *s++)) n--;
    while (n--) *d++ = 0;
    return r;
}

char* strcat(char* d, const char* s) {
    char* r = d;
    while (*d) d++;
    while ((*d++ = *s++));
    return r;
}

int strcmp(const char* a, const char* b) {
    while (*a && *a == *b) { a++; b++; }
    return (unsigned char)*a - (unsigned char)*b;
}

int strncmp(const char* a, const char* b, unsigned long n) {
    while (n && *a && *a == *b) { a++; b++; n--; }
    if (n == 0) return 0;
    return (unsigned char)*a - (unsigned char)*b;
}

char* strchr(const char* s, int c) {
    while (*s) { if (*s == (char)c) return (char*)s; s++; }
    return (c == 0) ? (char*)s : 0;
}

char* strrchr(const char* s, int c) {
    const char* last = 0;
    while (*s) { if (*s == (char)c) last = s; s++; }
    return (c == 0) ? (char*)s : (char*)last;
}

static char* saved_tok = 0;
char* strtok(char* s, const char* delim) {
    if (s) saved_tok = s;
    if (!saved_tok || !*saved_tok) return 0;
    while (*saved_tok) {
        int is_delim = 0;
        for (const char* d = delim; *d; d++) if (*d == *saved_tok) { is_delim = 1; break; }
        if (!is_delim) break;
        saved_tok++;
    }
    if (!*saved_tok) return 0;
    char* start = saved_tok;
    while (*saved_tok) {
        for (const char* d = delim; *d; d++) if (*d == *saved_tok) {
            *saved_tok = 0; saved_tok++;
            return start;
        }
        saved_tok++;
    }
    return start;
}
