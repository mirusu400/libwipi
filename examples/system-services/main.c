#include <wipi/wipi.h>

#define ARRAY_COUNT(values) ((M_Int32)(sizeof(values) / sizeof((values)[0])))

static MC_GrpFrameBuffer screen;
static MC_GrpDisplayInfo display;
static MC_GrpContext graphics;
static MCTimer timer;
static M_Int32 font;
static M_Int32 system_ready;
static M_Int32 timer_ready;
static M_Int32 timer_fired;
static M_Int64 current_time;
static M_Uint32 timer_cookie = 0x53595354u;
static M_Char program_name[40];
static M_Char property_value[40];

static M_Int32 text_length(const M_Char *text)
{
    M_Int32 length = 0;
    while (text[length] != '\0') {
        ++length;
    }
    return length;
}

static M_Int32 text_equal(const M_Char *left, const M_Char *right)
{
    while (*left != '\0' && *right != '\0' && *left == *right) {
        ++left;
        ++right;
    }
    return *left == *right;
}

static M_Uint32 color(M_Int32 red, M_Int32 green, M_Int32 blue)
{
    return (M_Uint32)MC_grpGetPixelFromRGB(red, green, blue);
}

static void draw_text(M_Int32 y, const M_Char *text, M_Uint32 foreground)
{
    graphics.fg_pixel = foreground;
    graphics.font = font;
    MC_grpDrawString(screen, 14, y, text, text_length(text), &graphics);
}

static void draw_frame(void)
{
    M_Uint32 pass = color(88, 224, 158);
    M_Uint32 wait = color(255, 190, 86);

    if (screen == 0) {
        return;
    }
    graphics.fg_pixel = color(10, 22, 40);
    MC_grpFillRect(screen, 0, 0, display.m_width, display.m_height, &graphics);
    graphics.fg_pixel = color(34, 52, 82);
    MC_grpFillRect(screen, 10, 48, display.m_width - 20, 172, &graphics);
    graphics.fg_pixel = color(112, 176, 255);
    MC_grpDrawRect(screen, 10, 48, display.m_width - 20, 172, &graphics);

    draw_text(16, "SYSTEM SERVICES", color(238, 246, 255));
    draw_text(62, system_ready != 0 ? "IDENTITY       PASS" :
                                      "IDENTITY       FAIL",
              system_ready != 0 ? pass : wait);
    draw_text(88, current_time >= 0 ? "MONOTONIC TIME PASS" :
                                     "MONOTONIC TIME FAIL",
              current_time >= 0 ? pass : wait);
    draw_text(114, timer_ready != 0 ? "TIMER SET      PASS" :
                                     "TIMER SET      FAIL",
              timer_ready != 0 ? pass : wait);
    draw_text(140, timer_fired != 0 ? "TIMER CALLBACK PASS" :
                                     "TIMER CALLBACK WAIT",
              timer_fired != 0 ? pass : wait);
    draw_text(176, program_name[0] != '\0' ? program_name : "NO PROGRAM NAME",
              color(190, 208, 232));
    draw_text(198, property_value[0] != '\0' ? property_value : "NO PROPERTY",
              color(190, 208, 232));
    draw_text(display.m_height - 34, "DIRECTION REFRESH   OK EXIT",
              color(190, 208, 232));
    MC_grpFlushLcd(0, screen, 0, 0, display.m_width, display.m_height);
}

static void timer_callback(MCTimer *fired_timer, void *parameter)
{
    if (fired_timer == &timer && parameter == (void *)&timer_cookie) {
        timer_fired = 1;
    }
    draw_frame();
}

static void initialize_system(void)
{
    M_Int32 first_set;
    M_Int32 second_set;

    program_name[0] = '\0';
    property_value[0] = '\0';
    current_time = MC_knlCurrentTime();
    system_ready =
        MC_knlGetProgramName(program_name, ARRAY_COUNT(program_name)) ==
            M_SUCCESS &&
        program_name[0] != '\0' &&
        MC_knlSetSystemProperty("LIBWIPI.SDK.LAB", "system-ok") ==
            M_SUCCESS &&
        MC_knlGetSystemProperty("LIBWIPI.SDK.LAB", property_value,
                                ARRAY_COUNT(property_value)) >= 0 &&
        text_equal(property_value, "system-ok") != 0;

    MC_knlDefTimer(&timer, timer_callback);
    first_set = MC_knlSetTimer(&timer, (M_Int64)500, &timer_cookie);
    MC_knlUnsetTimer(&timer);
    second_set = MC_knlSetTimer(&timer, (M_Int64)40, &timer_cookie);
    timer_ready = first_set == M_SUCCESS && second_set == M_SUCCESS;
}

void startClet(M_Int32 argc, M_Char *argv[])
{
    (void)argc;
    (void)argv;
    screen = MC_grpGetScreenFrameBuffer(0);
    if (screen == 0 || MC_grpGetDisplayInfo(0, &display) != M_SUCCESS) {
        MC_knlExit(1);
        return;
    }
    MC_grpInitContext(&graphics);
    font = MC_grpGetFont(0, 11, 0);
    timer_fired = 0;
    initialize_system();
    draw_frame();
}

void destroyClet(void)
{
    MC_knlUnsetTimer(&timer);
}

void pauseClet(void)
{
    MC_knlUnsetTimer(&timer);
}

void resumeClet(void)
{
    (void)MC_knlSetTimer(&timer, (M_Int64)40, &timer_cookie);
    draw_frame();
}

void paintClet(M_Int32 x, M_Int32 y, M_Int32 width, M_Int32 height)
{
    (void)x;
    (void)y;
    (void)width;
    (void)height;
    draw_frame();
}

void handleCletEvent(M_Int32 type, M_Int32 param1, M_Int32 param2)
{
    (void)param2;
    if (type != WIPI_CLET_EVENT_KEY_PRESS) {
        return;
    }
    if (param1 == WIPI_CLET_KEY_SELECT || param1 == '5') {
        MC_knlExit(system_ready != 0 && timer_ready != 0 ? 0 : 1);
        return;
    }
    current_time = MC_knlCurrentTime();
    draw_frame();
}
