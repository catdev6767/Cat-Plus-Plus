/* Kitty OS — utils */
#include "utils.h"

int str_eq(const char* a, const char* b) {
    while (*a && *a == *b) { a++; b++; }
    return *a == *b;
}
