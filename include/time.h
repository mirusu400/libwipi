#ifndef LIBWIPI_TIME_H
#define LIBWIPI_TIME_H

#include <stdint.h>

typedef int32_t clock_t;
typedef int32_t time_t;

struct tm {
    int tm_sec;
    int tm_min;
    int tm_hour;
    int tm_mday;
    int tm_mon;
    int tm_year;
    int tm_wday;
    int tm_yday;
    int tm_isdst;
};

#define CLOCKS_PER_SEC 1000

#ifdef __cplusplus
extern "C" {
#endif

clock_t clock(void);
time_t time(time_t *timer);
double difftime(time_t time1, time_t time0);
time_t mktime(struct tm *tm);
struct tm *localtime(const time_t *timer);
struct tm *gmtime(const time_t *timer);

#ifdef __cplusplus
}
#endif

#endif /* LIBWIPI_TIME_H */
