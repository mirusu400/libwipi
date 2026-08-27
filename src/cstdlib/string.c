#include <string.h>

char *strcpy(char *dst, const char *src)
{
    char *result = dst;
    while ((*dst++ = *src++) != '\0') {
    }
    return result;
}

char *strncpy(char *dst, const char *src, size_t n)
{
    char *result = dst;
    size_t i = 0;
    while (i < n && src[i] != '\0') {
        dst[i] = src[i];
        ++i;
    }
    while (i < n) {
        dst[i++] = '\0';
    }
    return result;
}

char *strcat(char *dst, const char *src)
{
    strcpy(dst + strlen(dst), src);
    return dst;
}

char *strncat(char *dst, const char *src, size_t n)
{
    char *tail = dst + strlen(dst);
    size_t i = 0;
    while (i < n && src[i] != '\0') {
        tail[i] = src[i];
        ++i;
    }
    tail[i] = '\0';
    return dst;
}

int strcmp(const char *a, const char *b)
{
    while (*a != '\0' && *a == *b) {
        ++a;
        ++b;
    }
    return (int)(unsigned char)*a - (int)(unsigned char)*b;
}

int strncmp(const char *a, const char *b, size_t n)
{
    size_t i;
    for (i = 0; i < n; ++i) {
        unsigned char av = (unsigned char)a[i];
        unsigned char bv = (unsigned char)b[i];
        if (av != bv) {
            return (int)av - (int)bv;
        }
        if (av == 0u) {
            return 0;
        }
    }
    return 0;
}

char *strchr(const char *s, int c)
{
    char wanted = (char)c;
    for (;;) {
        if (*s == wanted) {
            return (char *)s;
        }
        if (*s == '\0') {
            return (char *)0;
        }
        ++s;
    }
}

char *strrchr(const char *s, int c)
{
    const char *last = (const char *)0;
    char wanted = (char)c;
    do {
        if (*s == wanted) {
            last = s;
        }
    } while (*s++ != '\0');
    return (char *)last;
}

size_t strspn(const char *s, const char *accept)
{
    size_t count = 0;
    while (s[count] != '\0' && strchr(accept, s[count]) != (char *)0) {
        ++count;
    }
    return count;
}

size_t strcspn(const char *s, const char *reject)
{
    size_t count = 0;
    while (s[count] != '\0' && strchr(reject, s[count]) == (char *)0) {
        ++count;
    }
    return count;
}

char *strpbrk(const char *s, const char *accept)
{
    while (*s != '\0') {
        if (strchr(accept, *s) != (char *)0) {
            return (char *)s;
        }
        ++s;
    }
    return (char *)0;
}

char *strstr(const char *haystack, const char *needle)
{
    size_t needle_length = strlen(needle);
    if (needle_length == 0u) {
        return (char *)haystack;
    }
    while (*haystack != '\0') {
        if (*haystack == *needle &&
            strncmp(haystack, needle, needle_length) == 0) {
            return (char *)haystack;
        }
        ++haystack;
    }
    return (char *)0;
}

size_t strlen(const char *s)
{
    const char *end = s;
    while (*end != '\0') {
        ++end;
    }
    return (size_t)(end - s);
}

char *strtok(char *s, const char *delim)
{
    static char *next;
    char *token;

    if (s != (char *)0) {
        next = s;
    }
    if (next == (char *)0) {
        return (char *)0;
    }

    next += strspn(next, delim);
    if (*next == '\0') {
        next = (char *)0;
        return (char *)0;
    }

    token = next;
    next += strcspn(next, delim);
    if (*next != '\0') {
        *next++ = '\0';
    } else {
        next = (char *)0;
    }
    return token;
}

void *memcpy(void *dst, const void *src, size_t n)
{
    unsigned char *out = (unsigned char *)dst;
    const unsigned char *in = (const unsigned char *)src;
    size_t i;
    for (i = 0; i < n; ++i) {
        out[i] = in[i];
    }
    return dst;
}

void *memmove(void *dst, const void *src, size_t n)
{
    unsigned char *out = (unsigned char *)dst;
    const unsigned char *in = (const unsigned char *)src;
    if (out < in) {
        size_t i;
        for (i = 0; i < n; ++i) {
            out[i] = in[i];
        }
    } else if (out > in) {
        while (n != 0u) {
            --n;
            out[n] = in[n];
        }
    }
    return dst;
}

int memcmp(const void *a, const void *b, size_t n)
{
    const unsigned char *left = (const unsigned char *)a;
    const unsigned char *right = (const unsigned char *)b;
    size_t i;
    for (i = 0; i < n; ++i) {
        if (left[i] != right[i]) {
            return (int)left[i] - (int)right[i];
        }
    }
    return 0;
}

void *memchr(const void *s, int c, size_t n)
{
    const unsigned char *bytes = (const unsigned char *)s;
    unsigned char wanted = (unsigned char)c;
    size_t i;
    for (i = 0; i < n; ++i) {
        if (bytes[i] == wanted) {
            return (void *)(bytes + i);
        }
    }
    return (void *)0;
}

void *memset(void *s, int c, size_t n)
{
    unsigned char *bytes = (unsigned char *)s;
    unsigned char value = (unsigned char)c;
    size_t i;
    for (i = 0; i < n; ++i) {
        bytes[i] = value;
    }
    return s;
}
