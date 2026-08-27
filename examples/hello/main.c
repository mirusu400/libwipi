#include <wipi/wipi.h>

static MC_GrpFrameBuffer screen;
static MC_GrpDisplayInfo display;
static MC_GrpContext graphics;

void paintClet(M_Int32 x, M_Int32 y, M_Int32 width, M_Int32 height)
{
    (void)x;
    (void)y;
    (void)width;
    (void)height;
    if (screen == 0) {
        screen = MC_grpGetScreenFrameBuffer(0);
    }
    if (MC_grpGetDisplayInfo(0, &display) != M_SUCCESS) {
        return;
    }
    MC_grpInitContext(&graphics);
    graphics.fg_pixel = (M_Uint32)MC_grpGetPixelFromRGB(32, 96, 224);
    MC_grpFillRect(screen, 0, 0, display.m_width, display.m_height,
                   &graphics);
    MC_grpFlushLcd(0, screen, 0, 0, display.m_width, display.m_height);
}

void startClet(M_Int32 argc, M_Char *argv[])
{
    (void)argc;
    (void)argv;
#if defined(LIBWIPI_PROFILE_KTF_SAMSUNG)
    if (wipi_ktf_bind_default_imports() != M_SUCCESS) {
        return;
    }
#endif
    paintClet(0, 0, 0, 0);
}

void destroyClet(void)
{
}

void pauseClet(void)
{
}

void resumeClet(void)
{
    paintClet(0, 0, 0, 0);
}

void handleCletEvent(M_Int32 type, M_Int32 param1, M_Int32 param2)
{
    (void)type;
    (void)param1;
    (void)param2;
}
