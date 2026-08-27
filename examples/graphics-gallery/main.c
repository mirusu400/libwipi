#include <wipi/wipi.h>

#define ARRAY_COUNT(values) ((M_Int32)(sizeof(values) / sizeof((values)[0])))

enum {
    PAGE_COUNT = 3
};

static MC_GrpFrameBuffer screen;
static MC_GrpDisplayInfo display;
static MC_GrpContext graphics;
static M_Int32 graphics_ready;
static M_Int32 font_handle;
static M_Int32 page;

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
    } while (value != 0u && count < ARRAY_COUNT(digits));
    while (count > 0) {
        *output++ = digits[--count];
    }
    *output = '\0';
    return output;
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

static void draw_header(const M_Char *title, const M_Char *subtitle)
{
    graphics.fg_pixel = color(13, 21, 38);
    MC_grpFillRect(screen, 0, 0, display.m_width, display.m_height, &graphics);
    graphics.fg_pixel = color(34, 51, 82);
    MC_grpFillRect(screen, 0, 0, display.m_width, 54, &graphics);
    graphics.fg_pixel = color(94, 184, 255);
    MC_grpDrawLine(screen, 0, 53, display.m_width - 1, 53, &graphics);
    draw_text(12, 11, title, color(244, 249, 255));
    draw_text(12, 32, subtitle, color(160, 190, 225));
}

static void draw_primitives(void)
{
    M_Int32 index;

    draw_header("GRAPHICS GALLERY", "1/3  PRIMITIVES");

    graphics.fg_pixel = color(255, 102, 105);
    MC_grpDrawRect(screen, 14, 76, 80, 54, &graphics);
    graphics.fg_pixel = color(55, 201, 151);
    MC_grpFillRect(screen, 105, 76, 80, 54, &graphics);

    graphics.fg_pixel = color(255, 213, 96);
    MC_grpDrawArc(screen, 20, 151, 56, 56, 0, 360, &graphics);
    graphics.fg_pixel = color(137, 112, 255);
    MC_grpFillArc(screen, 112, 151, 56, 56, 0, 360, &graphics);

    graphics.fg_pixel = color(82, 173, 255);
    for (index = 0; index < 7; ++index) {
        MC_grpDrawLine(screen, 15, 232 + index * 5,
                       display.m_width - 16, 207 + index * 5, &graphics);
    }
    for (index = 0; index < 24; ++index) {
        graphics.fg_pixel = color(255, 244 - index * 5, 116);
        MC_grpPutPixel(screen, 18 + index * 7, 286, &graphics);
    }
    draw_text(14, display.m_height - 20, "LEFT / RIGHT: CHANGE PAGE",
              color(188, 205, 228));
}

static void draw_palette(void)
{
    static const M_Int32 red[] = {255, 255, 255, 72, 73, 131, 236, 245};
    static const M_Int32 green[] = {94, 179, 224, 201, 151, 112, 101, 245};
    static const M_Int32 blue[] = {105, 71, 102, 176, 255, 255, 236, 245};
    M_Char metrics[48];
    M_Char *cursor;
    M_Int32 index;
    M_Int32 font_height;
    M_Int32 ascent;
    M_Int32 descent;
    M_Int32 width;
    M_Int32 sample_red;
    M_Int32 sample_green;
    M_Int32 sample_blue;
    M_Uint32 sample;

    draw_header("GRAPHICS GALLERY", "2/3  COLOR AND FONT");
    for (index = 0; index < ARRAY_COUNT(red); ++index) {
        graphics.fg_pixel = color(red[index], green[index], blue[index]);
        MC_grpFillRect(screen, 14 + (index % 4) * 52,
                       76 + (index / 4) * 48, 42, 36, &graphics);
    }

    sample = color(94, 184, 255);
    sample_red = 0;
    sample_green = 0;
    sample_blue = 0;
    (void)MC_grpGetRGBFromPixel((M_Int32)sample, &sample_red,
                                &sample_green, &sample_blue);
    font_height = MC_grpGetFontHeight(font_handle);
    ascent = MC_grpGetFontAscent(font_handle);
    descent = MC_grpGetFontDescent(font_handle);
    width = MC_grpGetStringWidth(font_handle,
                                 (const M_Uint8 *)"LIBWIPI", 7);

    cursor = metrics;
    cursor = append_text(cursor, "FONT H/A/D  ");
    cursor = append_uint(cursor, (M_Uint32)font_height);
    cursor = append_text(cursor, "/");
    cursor = append_uint(cursor, (M_Uint32)ascent);
    cursor = append_text(cursor, "/");
    (void)append_uint(cursor, (M_Uint32)descent);
    draw_text(14, 186, metrics, color(232, 241, 252));

    cursor = metrics;
    cursor = append_text(cursor, "TEXT WIDTH  ");
    (void)append_uint(cursor, (M_Uint32)width);
    draw_text(14, 211, metrics, color(232, 241, 252));

    cursor = metrics;
    cursor = append_text(cursor, "RGB  ");
    cursor = append_uint(cursor, (M_Uint32)sample_red);
    cursor = append_text(cursor, "/");
    cursor = append_uint(cursor, (M_Uint32)sample_green);
    cursor = append_text(cursor, "/");
    (void)append_uint(cursor, (M_Uint32)sample_blue);
    draw_text(14, 236, metrics, sample);
    draw_text(14, display.m_height - 20, "LEFT / RIGHT: CHANGE PAGE",
              color(188, 205, 228));
}

static void draw_composition(void)
{
    M_Int32 center_x = display.m_width / 2;
    M_Int32 index;

    draw_header("GRAPHICS GALLERY", "3/3  COMPOSITION");
    graphics.fg_pixel = color(24, 40, 68);
    MC_grpFillRect(screen, 12, 70, display.m_width - 24, 212, &graphics);
    graphics.fg_pixel = color(79, 222, 171);
    MC_grpDrawRect(screen, 12, 70, display.m_width - 24, 212, &graphics);

    for (index = 0; index < 6; ++index) {
        graphics.fg_pixel = color(73 + index * 28, 112 + index * 17,
                                  255 - index * 21);
        MC_grpFillArc(screen, center_x - 62 + index * 20,
                      95 + index * 17, 44, 44, 0, 360, &graphics);
    }
    graphics.fg_pixel = color(255, 208, 86);
    MC_grpDrawLine(screen, 28, 250, display.m_width - 29, 92, &graphics);
    MC_grpDrawLine(screen, 28, 92, display.m_width - 29, 250, &graphics);
    draw_text(center_x - 53, 172, "DRAW WITH CODE", color(247, 250, 255));
    draw_text(14, display.m_height - 20, "LEFT / RIGHT: CHANGE PAGE",
              color(188, 205, 228));
}

static void initialize_graphics(void)
{
    screen = MC_grpGetScreenFrameBuffer(0);
    graphics_ready =
        screen != 0 && MC_grpGetDisplayInfo(0, &display) == M_SUCCESS;
    if (graphics_ready == 0) {
        return;
    }
    MC_grpInitContext(&graphics);
    font_handle = MC_grpGetFont(0, 11, 0);
}

void paintClet(M_Int32 x, M_Int32 y, M_Int32 width, M_Int32 height)
{
    (void)x;
    (void)y;
    (void)width;
    (void)height;
    if (graphics_ready == 0) {
        initialize_graphics();
    }
    if (graphics_ready == 0) {
        return;
    }
    if (page == 0) {
        draw_primitives();
    } else if (page == 1) {
        draw_palette();
    } else {
        draw_composition();
    }
    MC_grpFlushLcd(0, screen, 0, 0, display.m_width, display.m_height);
}

void startClet(M_Int32 argc, M_Char *argv[])
{
    (void)argc;
    (void)argv;
    page = 0;
    initialize_graphics();
    paintClet(0, 0, display.m_width, display.m_height);
}

void destroyClet(void)
{
}

void pauseClet(void)
{
}

void resumeClet(void)
{
    paintClet(0, 0, display.m_width, display.m_height);
}

void handleCletEvent(M_Int32 type, M_Int32 param1, M_Int32 param2)
{
    (void)param2;
    if (type != WIPI_CLET_EVENT_KEY_PRESS) {
        return;
    }
    if (param1 == WIPI_CLET_KEY_RIGHT || param1 == '6' ||
        param1 == WIPI_CLET_KEY_SELECT || param1 == '5') {
        page = (page + 1) % PAGE_COUNT;
        paintClet(0, 0, display.m_width, display.m_height);
    } else if (param1 == WIPI_CLET_KEY_LEFT || param1 == '4') {
        page = (page + PAGE_COUNT - 1) % PAGE_COUNT;
        paintClet(0, 0, display.m_width, display.m_height);
    }
}
