#include <stdlib.h>

static int wipi_is_space(char c)
{
    return c == ' ' || c == '\t' || c == '\n' || c == '\r' ||
           c == '\f' || c == '\v';
}

static int wipi_digit(char c)
{
    if (c >= '0' && c <= '9') {
        return c - '0';
    }
    if (c >= 'a' && c <= 'z') {
        return c - 'a' + 10;
    }
    if (c >= 'A' && c <= 'Z') {
        return c - 'A' + 10;
    }
    return -1;
}

static const char *wipi_skip_space(const char *s)
{
    while (wipi_is_space(*s)) {
        ++s;
    }
    return s;
}

typedef struct WipiUnsignedParse {
    unsigned long value;
    const char *end;
    int negative;
    int converted;
    int overflow;
} WipiUnsignedParse;

static WipiUnsignedParse wipi_parse_unsigned(const char *s, int base)
{
    const char *cursor = wipi_skip_space(s);
    const unsigned long maximum = ~0ul;
    WipiUnsignedParse result = {0ul, s, 0, 0, 0};

    if (*cursor == '+' || *cursor == '-') {
        result.negative = *cursor == '-';
        ++cursor;
    }
    if ((base == 0 || base == 16) && cursor[0] == '0' &&
        (cursor[1] == 'x' || cursor[1] == 'X') &&
        wipi_digit(cursor[2]) >= 0 && wipi_digit(cursor[2]) < 16) {
        base = 16;
        cursor += 2;
    } else if (base == 0) {
        base = cursor[0] == '0' ? 8 : 10;
    }
    if (base < 2 || base > 36) {
        return result;
    }

    for (;;) {
        int digit = wipi_digit(*cursor);
        if (digit < 0 || digit >= base) {
            break;
        }
        result.converted = 1;
        if (result.value >
            (maximum - (unsigned long)digit) / (unsigned long)base) {
            result.value = maximum;
            result.overflow = 1;
        } else {
            result.value = result.value * (unsigned long)base +
                           (unsigned long)digit;
        }
        ++cursor;
    }
    if (result.converted) {
        result.end = cursor;
    }
    return result;
}

unsigned long strtoul(const char *s, char **endptr, int base)
{
    WipiUnsignedParse parsed = wipi_parse_unsigned(s, base);
    if (endptr != (char **)0) {
        *endptr = (char *)parsed.end;
    }
    if (parsed.overflow) {
        return ~0ul;
    }
    return parsed.negative ? 0ul - parsed.value : parsed.value;
}

long strtol(const char *s, char **endptr, int base)
{
    WipiUnsignedParse parsed = wipi_parse_unsigned(s, base);
    const unsigned long positive_limit = (unsigned long)__LONG_MAX__;
    const unsigned long negative_limit = positive_limit + 1ul;

    if (endptr != (char **)0) {
        *endptr = (char *)parsed.end;
    }
    if (!parsed.converted) {
        return 0l;
    }
    if (parsed.negative) {
        if (parsed.overflow || parsed.value >= negative_limit) {
            return (-__LONG_MAX__ - 1l);
        }
        return -(long)parsed.value;
    }
    if (parsed.overflow || parsed.value > positive_limit) {
        return __LONG_MAX__;
    }
    return (long)parsed.value;
}

int atoi(const char *s)
{
    return (int)strtol(s, (char **)0, 10);
}

long long atoll(const char *s)
{
    const char *cursor = wipi_skip_space(s);
    unsigned long long value = 0ull;
    int negative = 0;

    if (*cursor == '+' || *cursor == '-') {
        negative = *cursor == '-';
        ++cursor;
    }
    while (*cursor >= '0' && *cursor <= '9') {
        value = value * 10ull + (unsigned long long)(*cursor - '0');
        ++cursor;
    }
    return negative ? -(long long)value : (long long)value;
}

double strtod(const char *s, char **endptr)
{
    const char *original = s;
    const char *cursor = wipi_skip_space(s);
    double value = 0.0;
    double fraction_scale = 0.1;
    int negative = 0;
    int converted = 0;
    int exponent = 0;
    int exponent_negative = 0;

    if (*cursor == '+' || *cursor == '-') {
        negative = *cursor == '-';
        ++cursor;
    }
    while (*cursor >= '0' && *cursor <= '9') {
        value = value * 10.0 + (double)(*cursor - '0');
        converted = 1;
        ++cursor;
    }
    if (*cursor == '.') {
        ++cursor;
        while (*cursor >= '0' && *cursor <= '9') {
            value += (double)(*cursor - '0') * fraction_scale;
            fraction_scale *= 0.1;
            converted = 1;
            ++cursor;
        }
    }
    if (converted && (*cursor == 'e' || *cursor == 'E')) {
        const char *exponent_mark = cursor++;
        const char *exponent_digits;
        if (*cursor == '+' || *cursor == '-') {
            exponent_negative = *cursor == '-';
            ++cursor;
        }
        exponent_digits = cursor;
        while (*cursor >= '0' && *cursor <= '9') {
            if (exponent < 10000) {
                exponent = exponent * 10 + (*cursor - '0');
            }
            ++cursor;
        }
        if (cursor == exponent_digits) {
            cursor = exponent_mark;
            exponent = 0;
        }
    }
    while (exponent-- > 0) {
        value = exponent_negative ? value / 10.0 : value * 10.0;
    }
    if (endptr != (char **)0) {
        *endptr = (char *)(converted ? cursor : original);
    }
    return negative ? -value : value;
}

double atof(const char *s)
{
    return strtod(s, (char **)0);
}
