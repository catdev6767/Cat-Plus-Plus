#ifndef FELIS_STRING_H
#define FELIS_STRING_H

unsigned long strlen(const char* s);
char* strcpy(char* d, const char* s);
char* strncpy(char* d, const char* s, unsigned long n);
char* strcat(char* d, const char* s);
int strcmp(const char* a, const char* b);
int strncmp(const char* a, const char* b, unsigned long n);
char* strchr(const char* s, int c);
char* strrchr(const char* s, int c);
void* memcpy(void* d, const void* s, unsigned long n);
void* memset(void* d, int c, unsigned long n);
int memcmp(const void* a, const void* b, unsigned long n);
char* strtok(char* s, const char* delim);

#endif
