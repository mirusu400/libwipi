#include <wipi/wipi.h>

static MC_GrpFrameBuffer screen;
static MC_GrpDisplayInfo display;
static MC_GrpContext graphics;
static M_Int32 font;
static M_Int32 connected;
static M_Int32 closed;
static M_Int32 close_result;
static M_Uint32 callback_cookie = 0x4e45544cu;

static M_Int32 text_length(const M_Char *text)
{
    M_Int32 length = 0;
    while (text[length] != '\0') {
        ++length;
    }
    return length;
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
    M_Uint32 pass = color(86, 226, 158);
    M_Uint32 wait = color(255, 188, 88);

    graphics.fg_pixel = color(10, 24, 34);
    MC_grpFillRect(screen, 0, 0, display.m_width, display.m_height, &graphics);
    graphics.fg_pixel = color(25, 60, 70);
    MC_grpFillRect(screen, 12, 56, display.m_width - 24, 146, &graphics);
    draw_text(18, "NETWORK LIFECYCLE", color(238, 248, 250));
    draw_text(76, connected != 0 ? "CONNECT CALLBACK PASS" :
                                   "CONNECT CALLBACK WAIT",
              connected != 0 ? pass : wait);
    draw_text(108, close_result < 0 ? "INVALID CLOSE PASS" :
                                     "INVALID CLOSE WAIT",
              close_result < 0 ? pass : wait);
    draw_text(140, closed != 0 ? "SERVICE CLOSE PASS" :
                                "SERVICE CLOSE WAIT",
              closed != 0 ? pass : wait);
    draw_text(display.m_height - 52, "UP CONNECT", color(184, 210, 220));
    draw_text(display.m_height - 30, "OK CLOSE", color(184, 210, 220));
    MC_grpFlushLcd(0, screen, 0, 0, display.m_width, display.m_height);
}

static void connect_callback(M_Int32 error, void *parameter)
{
    if (error == M_SUCCESS && parameter == (void *)&callback_cookie) {
        connected = 1;
        closed = 0;
    }
    draw_frame();
}

static void connect_service(void)
{
    connected = 0;
    closed = 0;
    (void)MC_netConnect(connect_callback, &callback_cookie);
}

void startClet(M_Int32 argc, M_Char *argv[])
{
    (void)argc;
    (void)argv;
    screen = MC_grpGetScreenFrameBuffer(0);
    if (screen == 0 || MC_grpGetDisplayInfo(0, &display) != M_SUCCESS) {
        return;
    }
    MC_grpInitContext(&graphics);
    font = MC_grpGetFont(0, 11, 0);
    close_result = 0;
    connect_service();
    draw_frame();
}

void destroyClet(void)
{
    MC_netClose();
}

void pauseClet(void)
{
}

void resumeClet(void)
{
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
    if (param1 == WIPI_CLET_KEY_UP || param1 == '2') {
        connect_service();
    } else if (param1 == WIPI_CLET_KEY_SELECT || param1 == '5') {
        close_result = MC_netSocketClose(-1);
        MC_netClose();
        connected = 0;
        closed = 1;
    }
    draw_frame();
}
