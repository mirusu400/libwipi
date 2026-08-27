#include <time.h>
#include <wipi/generated/kernel.h>

static struct tm wipi_tm_storage;

static int wipi_is_leap(int year)
{
    return (year % 4 == 0 && year % 100 != 0) || year % 400 == 0;
}

static int wipi_days_in_month(int year, int month)
{
    static const unsigned char days[12] = {
        31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
    };
    if (month == 1 && wipi_is_leap(year)) {
        return 29;
    }
    return days[month];
}

clock_t clock(void)
{
    return (clock_t)MC_knlCurrentTime();
}

time_t time(time_t *timer)
{
    time_t result = (time_t)(MC_knlCurrentTime() / 1000);
    if (timer != (time_t *)0) {
        *timer = result;
    }
    return result;
}

double difftime(time_t time1, time_t time0)
{
    return (double)time1 - (double)time0;
}

struct tm *gmtime(const time_t *timer)
{
    M_Int64 seconds;
    M_Int64 days;
    int year = 1970;
    int month = 0;
    int year_days;

    if (timer == (const time_t *)0) {
        return (struct tm *)0;
    }
    seconds = (M_Int64)*timer;
    days = seconds / 86400;
    seconds %= 86400;
    if (seconds < 0) {
        seconds += 86400;
        --days;
    }

    wipi_tm_storage.tm_hour = (int)(seconds / 3600);
    seconds %= 3600;
    wipi_tm_storage.tm_min = (int)(seconds / 60);
    wipi_tm_storage.tm_sec = (int)(seconds % 60);
    wipi_tm_storage.tm_wday = (int)((days + 4) % 7);
    if (wipi_tm_storage.tm_wday < 0) {
        wipi_tm_storage.tm_wday += 7;
    }

    if (days >= 0) {
        while (days >= (year_days = wipi_is_leap(year) ? 366 : 365)) {
            days -= year_days;
            ++year;
        }
    } else {
        do {
            --year;
            days += wipi_is_leap(year) ? 366 : 365;
        } while (days < 0);
    }
    wipi_tm_storage.tm_year = year - 1900;
    wipi_tm_storage.tm_yday = (int)days;
    while (days >= wipi_days_in_month(year, month)) {
        days -= wipi_days_in_month(year, month);
        ++month;
    }
    wipi_tm_storage.tm_mon = month;
    wipi_tm_storage.tm_mday = (int)days + 1;
    wipi_tm_storage.tm_isdst = 0;
    return &wipi_tm_storage;
}

struct tm *localtime(const time_t *timer)
{
    /* No profile currently proves a device timezone service. */
    return gmtime(timer);
}

time_t mktime(struct tm *tm_value)
{
    M_Int64 days = 0;
    M_Int64 seconds;
    int year;
    int month;

    if (tm_value == (struct tm *)0 || tm_value->tm_mon < 0 ||
        tm_value->tm_mon > 11) {
        return (time_t)-1;
    }
    year = tm_value->tm_year + 1900;
    if (year >= 1970) {
        int current;
        for (current = 1970; current < year; ++current) {
            days += wipi_is_leap(current) ? 366 : 365;
        }
    } else {
        int current;
        for (current = year; current < 1970; ++current) {
            days -= wipi_is_leap(current) ? 366 : 365;
        }
    }
    for (month = 0; month < tm_value->tm_mon; ++month) {
        days += wipi_days_in_month(year, month);
    }
    days += tm_value->tm_mday - 1;
    seconds = days * 86400 + (M_Int64)tm_value->tm_hour * 3600 +
              (M_Int64)tm_value->tm_min * 60 + tm_value->tm_sec;
    return (time_t)seconds;
}
