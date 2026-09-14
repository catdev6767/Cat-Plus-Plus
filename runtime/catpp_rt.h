/* Cat++ Runtime — freestanding-compatible */
#ifndef CATPP_RT_H
#define CATPP_RT_H

#include <stdint.h>
#include <stddef.h>

#ifdef CATPP_FREESTANDING

/* ═══ Freestanding (kernel) ═══ */
void  catpp_init(void);
void  catpp_print(long v);
void  catpp_print_str(const char* s);
long  catpp_len(void* arr);
int   catpp_in(long v, void* arr);
const char* catpp_str(long v);

void* catpp_alloc(size_t n);
void  catpp_free(void* p);
void  catpp_memset(void* p, int c, size_t n);
void  catpp_memcpy(void* d, const void* s, size_t n);
size_t catpp_strlen(const char* s);
int   catpp_strcmp(const char* a, const char* b);

#else

/* ═══ Hosted (Linux) ═══ */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static inline void catpp_init(void) {}
static inline void catpp_print(long v) { printf("%ld\n", v); }
static inline void catpp_print_str(const char* s) { printf("%s\n", s); }
static inline long catpp_len(void* arr) { return 0; }
static inline int catpp_in(long v, void* arr) { return 0; }

static inline void* catpp_alloc(size_t n) { return malloc(n); }
static inline void catpp_free(void* p) { free(p); }
static inline void catpp_memset(void* p, int c, size_t n) { memset(p, c, n); }
static inline void catpp_memcpy(void* d, const void* s, size_t n) { memcpy(d, s, n); }
static inline size_t catpp_strlen(const char* s) { return strlen(s); }
static inline int catpp_strcmp(const char* a, const char* b) { return strcmp(a, b); }

static inline const char* catpp_str(long v) {
    static char buf[32];
    snprintf(buf, sizeof(buf), "%ld", v);
    return buf;
}

static inline const char* catpp_method_upper(const char* s) { return s; }
static inline const char* catpp_method_lower(const char* s) { return s; }

#endif

#endif
