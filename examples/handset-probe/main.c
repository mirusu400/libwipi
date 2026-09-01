#include <wipi/wipi.h>

enum {
    SCREEN_WIDTH = 240,
    SCREEN_HEIGHT = 320,
    TIMER_PERIOD_MS = 1000
};

static MC_GrpFrameBuffer screen;
static MC_GrpContext graphics;
static MCTimer probe_timer;
static M_Uint32 timer_cookie = 0x57383330u;
static M_Int32 font_handle;
static M_Int32 screen_ready;
static M_Int32 timer_defined;
static M_Int32 timer_running;
static M_Uint32 ticks;
static M_Uint32 events;
static M_Int32 last_event;
static M_Int32 last_key;

static M_Int32 text_length(const M_Char *text)
{
    M_Int32 length = 0;
    while (text[length] != '\0') {
        ++length;
    }
    return length;
}

static M_Char *append_text(M_Char *output, const M_Char *text)
{
    while (*text != '\0') {
        *output++ = *text++;
    }
    *output = '\0';
    return output;
}

static M_Char *append_uint(M_Char *output, M_Uint32 value)
{
    M_Char digits[10];
    M_Int32 count = 0;
    do {
        digits[count++] = (M_Char)('0' + value % 10u);
        value /= 10u;
    } while (value != 0u && count < 10);
    while (count > 0) {
        *output++ = digits[--count];
    }
    *output = '\0';
    return output;
}

static M_Char *append_int(M_Char *output, M_Int32 value)
{
    M_Uint32 magnitude;
    if (value < 0) {
        *output++ = '-';
        magnitude = 0u - (M_Uint32)value;
    } else {
        magnitude = (M_Uint32)value;
    }
    return append_uint(output, magnitude);
}

static M_Uint32 color(M_Int32 red, M_Int32 green, M_Int32 blue)
{
    return (M_Uint32)MC_grpGetPixelFromRGB(red, green, blue);
}

static void draw_text(M_Int32 x, M_Int32 y, const M_Char *text,
                      M_Uint32 foreground)
{
    graphics.fg_pixel = foreground;
    graphics.font = font_handle;
    MC_grpDrawString(screen, x, y, text, text_length(text), &graphics);
}

static void draw_probe(void)
{
    M_Char line[40];
    M_Char *cursor;
    M_Uint32 background;
    M_Uint32 panel;
    M_Uint32 accent;
    M_Uint32 white;

    if (screen_ready == 0) {
        return;
    }
    background = color(12, 30, 62);
    panel = color(24, 58, 108);
    accent = color((last_key & 1) != 0 ? 255 : 72, 196, 132);
    white = color(245, 250, 255);

    graphics.fg_pixel = background;
    MC_grpFillRect(screen, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, &graphics);
    graphics.fg_pixel = panel;
    MC_grpFillRect(screen, 8, 10, 224, 126, &graphics);
    graphics.fg_pixel = accent;
    MC_grpDrawRect(screen, 8, 10, 224, 126, &graphics);

    draw_text(20, 24, "SCH-W8300 PROBE", white);
    draw_text(20, 48, "SCREEN OK", accent);

    cursor = append_text(line, "TICK ");
    (void)append_uint(cursor, ticks);
    draw_text(20, 72, line, white);

    cursor = append_text(line, timer_running != 0 ? "TIMER OK " : "TIMER WAIT ");
    (void)append_uint(cursor, (M_Uint32)TIMER_PERIOD_MS);
    draw_text(20, 94, line, timer_running != 0 ? accent : white);

    cursor = append_text(line, "EVENT ");
    cursor = append_int(cursor, last_event);
    cursor = append_text(cursor, " KEY ");
    (void)append_int(cursor, last_key);
    draw_text(20, 116, line, white);

    graphics.fg_pixel = color(218, 72, 78);
    MC_grpFillRect(screen, 20, 160, 58, 58, &graphics);
    graphics.fg_pixel = color(66, 188, 112);
    MC_grpFillRect(screen, 91, 160, 58, 58, &graphics);
    graphics.fg_pixel = color(70, 128, 232);
    MC_grpFillRect(screen, 162, 160, 58, 58, &graphics);

    cursor = append_text(line, "INPUT EVENTS ");
    (void)append_uint(cursor, events);
    draw_text(20, 244, line, white);
    draw_text(20, 270, "INPUT BRIDGE PENDING", accent);
    draw_text(20, 292, "QPST BUILD 01", white);

    MC_grpFlushLcd(0, screen, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
}

static void probe_timer_callback(MCTimer *fired_timer, void *parameter)
{
    if (fired_timer != &probe_timer || parameter != (void *)&timer_cookie) {
        return;
    }
    ++ticks;
    draw_probe();
    timer_running =
        MC_knlSetTimer(&probe_timer, (M_Int64)TIMER_PERIOD_MS,
                       (void *)&timer_cookie) == M_SUCCESS;
}

void startClet(M_Int32 argc, M_Char *argv[])
{
    (void)argc;
    (void)argv;
    screen = MC_grpGetScreenFrameBuffer(0);
    if (screen == 0) {
        return;
    }
    MC_grpInitContext(&graphics);
    font_handle = MC_grpGetFont(0, 12, 0);
    screen_ready = 1;

    /* Draw first so first-frame and timer failures remain distinguishable. */
    draw_probe();
    MC_knlDefTimer(&probe_timer, probe_timer_callback);
    timer_defined = 1;
    timer_running =
        MC_knlSetTimer(&probe_timer, (M_Int64)TIMER_PERIOD_MS,
                       (void *)&timer_cookie) == M_SUCCESS;
    draw_probe();
}

void destroyClet(void)
{
    if (timer_defined != 0) {
        MC_knlUnsetTimer(&probe_timer);
    }
    timer_running = 0;
}

void pauseClet(void)
{
    if (timer_defined != 0) {
        MC_knlUnsetTimer(&probe_timer);
    }
    timer_running = 0;
}

void resumeClet(void)
{
    if (timer_defined != 0) {
        timer_running =
            MC_knlSetTimer(&probe_timer, (M_Int64)TIMER_PERIOD_MS,
                           (void *)&timer_cookie) == M_SUCCESS;
    }
    draw_probe();
}

void paintClet(M_Int32 x, M_Int32 y, M_Int32 width, M_Int32 height)
{
    (void)x;
    (void)y;
    (void)width;
    (void)height;
    draw_probe();
}

void handleCletEvent(M_Int32 type, M_Int32 param1, M_Int32 param2)
{
    (void)param2;
    ++events;
    last_event = type;
    last_key = param1;
    draw_probe();
}
