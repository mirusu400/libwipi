#include <wipi/wipi.h>

static MC_GrpFrameBuffer screen;
static MC_GrpDisplayInfo display;
static MC_GrpContext graphics;
static M_Int32 font;
static M_Uint32 accent;

static void draw_frame(void)
{
    if (screen == 0) {
        screen = MC_grpGetScreenFrameBuffer(0);
    }
    if (screen == 0 || MC_grpGetDisplayInfo(0, &display) != M_SUCCESS) {
        return;
    }
    MC_grpInitContext(&graphics);
    graphics.fg_pixel = (M_Uint32)MC_grpGetPixelFromRGB(18, 28, 52);
    MC_grpFillRect(screen, 0, 0, display.m_width, display.m_height,
                   &graphics);
    graphics.fg_pixel = accent;
    graphics.font = font;
    MC_grpDrawString(screen, 18, 28, "HELLO LIBWIPI", 13, &graphics);
    MC_grpFlushLcd(0, screen, 0, 0, display.m_width, display.m_height);
}

void startClet(M_Int32 argc, M_Char *argv[])
{
    (void)argc;
    (void)argv;
    font = MC_grpGetFont(0, 12, 0);
    accent = (M_Uint32)MC_grpGetPixelFromRGB(88, 166, 255);
    draw_frame();
}

void destroyClet(void)
{
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
    if (type == WIPI_CLET_EVENT_KEY_PRESS) {
        accent = (M_Uint32)MC_grpGetPixelFromRGB(
            (param1 & 1) != 0 ? 255 : 84, 232, 164);
        draw_frame();
    }
}
