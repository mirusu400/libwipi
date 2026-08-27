#include <stdint.h>
#include <wipi/wipi.h>

#define ARRAY_COUNT(values) ((M_Int32)(sizeof(values) / sizeof((values)[0])))

static M_Byte test_gif[] = {
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
    0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0x2c,
    0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02,
    0x01, 0x4c, 0x00, 0x3b,
};

static MC_GrpFrameBuffer screen;
static MC_GrpDisplayInfo display;
static MC_GrpContext graphics;
static MC_GrpImage image;
static M_Int32 font;
static M_Int32 image_ready;
static M_Int32 pipeline_ready;
static M_Uint32 generation;
static M_Uint32 pattern[64];
static M_Uint32 readback[64];

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

static void initialize_image(void)
{
    M_MemID buffer_id;
    M_Byte *buffer;
    M_Int32 index;
    M_Int32 result;

    buffer_id = MC_knlAlloc(ARRAY_COUNT(test_gif));
    buffer = (M_Byte *)MC_GETDPTR(buffer_id);
    if (buffer == (M_Byte *)0) {
        return;
    }
    for (index = 0; index < ARRAY_COUNT(test_gif); ++index) {
        buffer[index] = test_gif[index];
    }
    result = MC_grpCreateImage(&image, buffer_id, 0, ARRAY_COUNT(test_gif));
    image_ready = result >= 0 && image != (MC_GrpImage)0 &&
                  MC_grpGetImageProperty(image, 4) == 1 &&
                  MC_grpGetImageProperty(image, 5) == 1 &&
                  MC_grpGetImageFrameBuffer(image) != 0;
}

static void run_pipeline(void)
{
    MC_GrpFrameBuffer offscreen;
    M_Int32 index;
    M_Uint32 foreground;

    offscreen = MC_grpCreateOffScreenFrameBuffer(96, 96);
    if (offscreen == 0) {
        pipeline_ready = 0;
        return;
    }
    foreground = color(28, 50, 92);
    MC_grpSetContext(&graphics, 1, (void *)(uintptr_t)foreground);
    MC_grpFillRect(offscreen, 0, 0, 96, 96, &graphics);

    for (index = 0; index < ARRAY_COUNT(pattern); ++index) {
        M_Uint32 red = (M_Uint32)((index & 7) * 32);
        M_Uint32 green = (M_Uint32)((index >> 3) * 32);
        pattern[index] = red << 16 | green << 8 |
                         (0x40u + generation * 23u) % 0xffu;
        readback[index] = 0u;
    }
    MC_grpSetRGBPixels(offscreen, 8, 8, 8, 8, pattern, 8, &graphics);
    MC_grpGetRGBPixels(offscreen, 8, 8, 8, 8, readback, 8);

    MC_grpCopyFrameBuffer(screen, 18, 70, 96, 96,
                          offscreen, 0, 0, &graphics);
    MC_grpCopyArea(screen, 132, 70, 72, 72, 18, 70, &graphics);
    if (image_ready != 0) {
        MC_grpDrawImage(screen, 112, 176, 1, 1, image, 0, 0, &graphics);
    }
    pipeline_ready = readback[1] != 0u;
    MC_grpDestroyOffScreenFrameBuffer(offscreen);
}

static void draw_frame(void)
{
    const M_Char *status = image_ready != 0 && pipeline_ready != 0
        ? "IMAGE PIPELINE PASS" : "IMAGE PIPELINE FAIL";

    graphics.fg_pixel = color(8, 18, 32);
    MC_grpFillRect(screen, 0, 0, display.m_width, display.m_height, &graphics);
    run_pipeline();
    graphics.fg_pixel = image_ready != 0 && pipeline_ready != 0
        ? color(90, 228, 160) : color(255, 104, 96);
    graphics.font = font;
    MC_grpDrawString(screen, 14, 18, status, text_length(status), &graphics);
    graphics.fg_pixel = color(178, 198, 226);
    MC_grpDrawString(screen, 14, display.m_height - 30,
                     "PRESS A KEY TO REBUILD", 22, &graphics);
    MC_grpRepaint(0, 0, 0, display.m_width, display.m_height);
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
    image = (MC_GrpImage)0;
    image_ready = 0;
    generation = 0u;
    initialize_image();
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
    (void)param1;
    (void)param2;
    if (type == WIPI_CLET_EVENT_KEY_PRESS) {
        generation = (generation + 1u) % 7u;
        draw_frame();
    }
}
