/*
 * Vibration test clet.
 *
 * A minimal original WIPI-C application that exercises MC_mdaVibrator so a
 * rumble motor (host gamepad) or phone vibrator can be verified end to end.
 * It draws only code-drawn rectangles and text; no commercial assets.
 *
 * Controls (host controls map to these WIPI keys):
 *   - OK / any key : buzz at the current level for the current duration;
 *   - Up / Down    : raise or lower the level by 10 (0..100), with a preview;
 *   - Left / Right : shorten or lengthen the pulse by 100 ms (100..2000);
 *   - 0..9         : set the level to that digit x10 (0 stops), then buzz.
 */
#include <wipi/wipi.h>

static MC_GrpFrameBuffer screen;
static MC_GrpDisplayInfo display;
static MC_GrpContext graphics;
static M_Int32 font;

static M_Int32 level = 100;       /* motor strength, 0..100 */
static M_Int32 duration_ms = 400; /* pulse length, 100..2000 */
static M_Int32 active;            /* draw the buzzing state */
static M_Int32 device_ready;

static M_Int32 clampi(M_Int32 value, M_Int32 low, M_Int32 high)
{
    if (value < low) {
        return low;
    }
    if (value > high) {
        return high;
    }
    return value;
}

static void buzz(void)
{
    /* Level 0 asks the device to stop; a positive level starts a pulse. */
    MC_mdaVibrator(level, level == 0 ? 0 : duration_ms);
}

static void draw_frame(void)
{
    M_Int32 bar_x, bar_y, bar_w, bar_h, fill;

    if (screen == 0) {
        screen = MC_grpGetScreenFrameBuffer(0);
    }
    if (screen == 0 || MC_grpGetDisplayInfo(0, &display) != M_SUCCESS) {
        return;
    }

    MC_grpInitContext(&graphics);
    graphics.fg_pixel = active
        ? (M_Uint32)MC_grpGetPixelFromRGB(120, 30, 30)
        : (M_Uint32)MC_grpGetPixelFromRGB(18, 28, 52);
    MC_grpFillRect(screen, 0, 0, display.m_width, display.m_height, &graphics);

    graphics.font = font;
    graphics.fg_pixel = (M_Uint32)MC_grpGetPixelFromRGB(240, 240, 240);
    MC_grpDrawString(screen, 12, 18, "VIBRATION TEST", 14, &graphics);

    graphics.fg_pixel = (M_Uint32)MC_grpGetPixelFromRGB(150, 180, 220);
    MC_grpDrawString(screen, 12, 40, "OK: buzz", 8, &graphics);
    MC_grpDrawString(screen, 12, 56, "Up/Down: level", 14, &graphics);
    MC_grpDrawString(screen, 12, 72, "Left/Right: length", 18, &graphics);
    MC_grpDrawString(screen, 12, 88, "0-9: set level", 14, &graphics);

    /* Level bar: outline plus a fill proportional to the current level. */
    bar_x = 12;
    bar_y = 108;
    bar_w = display.m_width - 24;
    bar_h = 16;
    if (bar_w < 20) {
        bar_w = 20;
    }
    graphics.fg_pixel = (M_Uint32)MC_grpGetPixelFromRGB(90, 90, 110);
    MC_grpFillRect(screen, bar_x, bar_y, bar_w, bar_h, &graphics);
    fill = bar_w * clampi(level, 0, 100) / 100;
    graphics.fg_pixel = active
        ? (M_Uint32)MC_grpGetPixelFromRGB(255, 210, 90)
        : (M_Uint32)MC_grpGetPixelFromRGB(88, 200, 140);
    MC_grpFillRect(screen, bar_x, bar_y, fill, bar_h, &graphics);

    graphics.fg_pixel = device_ready != 0
        ? (M_Uint32)MC_grpGetPixelFromRGB(88, 220, 150)
        : (M_Uint32)MC_grpGetPixelFromRGB(255, 110, 100);
    MC_grpDrawString(screen, 12, 142,
                     device_ready != 0 ? "DEVICE CONTROLS PASS" :
                                         "DEVICE CONTROLS FAIL",
                     20, &graphics);

    MC_grpFlushLcd(0, screen, 0, 0, display.m_width, display.m_height);
}

void startClet(M_Int32 argc, M_Char *argv[])
{
    (void)argc;
    (void)argv;
    font = MC_grpGetFont(0, 12, 0);
    level = 100;
    duration_ms = 400;
    active = 0;
    device_ready =
        MC_miscBackLight(0, MC_LIGHT_ALWAYS_ON, 0xffffff, 0) == M_SUCCESS &&
        MC_mdaSetMuteState(0, M_TRUE) == M_SUCCESS &&
        MC_mdaGetMuteState(0) == M_TRUE;
    draw_frame();
}

void destroyClet(void)
{
    level = 0;
    buzz();
}

void pauseClet(void)
{
    level = 0;
    buzz();
    level = 100;
}

void resumeClet(void)
{
    active = 0;
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

    if (type == WIPI_CLET_EVENT_KEY_RELEASE) {
        active = 0;
        draw_frame();
        return;
    }
    if (type != WIPI_CLET_EVENT_KEY_PRESS) {
        return;
    }

    if (param1 >= '0' && param1 <= '9') {
        level = (param1 - '0') * 10;
    } else if (param1 == WIPI_CLET_KEY_UP) {
        level = clampi(level + 10, 0, 100);
    } else if (param1 == WIPI_CLET_KEY_DOWN) {
        level = clampi(level - 10, 0, 100);
    } else if (param1 == WIPI_CLET_KEY_LEFT) {
        duration_ms = clampi(duration_ms - 100, 100, 2000);
    } else if (param1 == WIPI_CLET_KEY_RIGHT) {
        duration_ms = clampi(duration_ms + 100, 100, 2000);
    }

    /* Every press buzzes so the motor is easy to feel; a length change buzzes
     * at the new length, a level change previews the new strength. */
    active = 1;
    buzz();
    draw_frame();
}
