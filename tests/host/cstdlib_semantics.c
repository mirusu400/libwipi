#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <wipi/types.h>

static M_Int64 fake_current_time;

M_Int64 MC_knlCurrentTime(void)
{
    return fake_current_time;
}

#define CHECK(expression)     \
    do {                      \
        if (!(expression)) {  \
            return __LINE__;  \
        }                     \
    } while (0)

int main(void)
{
    char buffer[32];
    char overlap[] = "abcdef";
    char tokens[] = ",one,,two";
    char *end;
    char *token;
    time_t epoch;
    struct tm *calendar;
    struct tm leap_day = {0, 0, 0, 29, 1, 100, 0, 0, 0};

    CHECK(strcmp(strcpy(buffer, "wipi"), "wipi") == 0);
    CHECK(strcmp(strcat(buffer, "-c"), "wipi-c") == 0);
    memset(buffer, 'x', sizeof(buffer));
    strncpy(buffer, "ab", 5);
    CHECK(buffer[0] == 'a' && buffer[1] == 'b' && buffer[2] == '\0' &&
          buffer[4] == '\0');
    CHECK(strncmp("abc", "abd", 2) == 0);
    CHECK(strchr("abc", 'b') != (char *)0);
    CHECK(strrchr("abca", 'a') != (char *)0 &&
          strrchr("abca", 'a')[1] == '\0');
    CHECK(strspn("aabbc", "ab") == 4u);
    CHECK(strcspn("hello", "xyzl") == 2u);
    CHECK(strstr("libwipi", "wipi") != (char *)0);
    memmove(overlap + 1, overlap, 5);
    CHECK(memcmp(overlap, "aabcde", 6) == 0);
    CHECK(memchr(overlap, 'd', 6) == overlap + 4);

    token = strtok(tokens, ",");
    CHECK(token != (char *)0 && strcmp(token, "one") == 0);
    token = strtok((char *)0, ",");
    CHECK(token != (char *)0 && strcmp(token, "two") == 0);
    CHECK(strtok((char *)0, ",") == (char *)0);

#if __SIZEOF_LONG__ == 4
    CHECK(strtol(" -2147483648x", &end, 10) == (-2147483647l - 1l));
    CHECK(*end == 'x');
    CHECK(strtol("2147483648", &end, 10) == 2147483647l);
#else
    CHECK(strtol(" -12345x", &end, 10) == -12345l && *end == 'x');
#endif
    CHECK(strtoul("0xff!", &end, 0) == 255ul && *end == '!');
    CHECK(strtoul("-2", &end, 10) == (unsigned long)-2l);
    CHECK(atoi(" -42") == -42);
    CHECK(atoll("922337") == 922337ll);
    CHECK(strtod(" -12.5e2tail", &end) == -1250.0 && *end == 't');

    fake_current_time = 951782400000ll;
    CHECK(clock() == (clock_t)fake_current_time);
    CHECK(time(&epoch) == 951782400 && epoch == 951782400);
    calendar = gmtime(&epoch);
    CHECK(calendar != (struct tm *)0);
    CHECK(calendar->tm_year == 100 && calendar->tm_mon == 1 &&
          calendar->tm_mday == 29 && calendar->tm_wday == 2);
    CHECK(mktime(&leap_day) == epoch);
    CHECK(localtime(&epoch) == calendar);
    CHECK(difftime(12, 7) == 5.0);

    return 0;
}
