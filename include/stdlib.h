#ifndef LIBWIPI_STDLIB_H
#define LIBWIPI_STDLIB_H

#ifdef __cplusplus
extern "C" {
#endif

double atof(const char *s);
int atoi(const char *s);
long long atoll(const char *s);
double strtod(const char *s, char **endptr);
long strtol(const char *s, char **endptr, int base);
unsigned long strtoul(const char *s, char **endptr, int base);

#ifdef __cplusplus
}
#endif

#endif /* LIBWIPI_STDLIB_H */
