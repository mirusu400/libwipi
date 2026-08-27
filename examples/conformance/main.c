#include <stdint.h>
#include <wipi/wipi.h>

#define ARRAY_COUNT(values) ((M_Int32)(sizeof(values) / sizeof((values)[0])))

static MC_GrpFrameBuffer screen;
static MC_GrpDisplayInfo display;
static MC_GrpContext graphics;
static MCTimer timer;
static MC_MdaClip *audio_clip;
static M_Uint32 timer_cookie = 0x4c575450u;
static M_Int32 graphics_ready;
static M_Int32 font_ready;
static M_Int32 system_ready;
static M_Int32 memory_ready;
static M_Int32 timer_ready;
static M_Int32 input_ready;
static M_Int32 audio_ready;
static M_Uint32 timer_ticks;
static M_Uint32 input_count;
static M_Int32 last_key;
static M_Int32 font_handle;
static M_Int32 total_memory;
static M_Int32 free_memory;
static M_Int64 start_time;
static M_Char phone_model[24];

/* Original synthetic SMAF: C4 followed by E4, about one second total. */
static M_Byte test_tone[] = {
    0x4d, 0x4d, 0x4d, 0x44, 0x00, 0x00, 0x00, 0x3a,
    0x4d, 0x54, 0x52, 0x00, 0x00, 0x00, 0x00, 0x30,
    0x02, 0x00, 0x02, 0x02,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x4d, 0x74, 0x73, 0x71, 0x00, 0x00, 0x00, 0x14,
    0x00, 0xb0, 0x07, 0x7f,
    0x00, 0xc0, 0x00,
    0x00, 0x90, 0x3c, 0x6e, 0x7d,
    0x7d, 0x80, 0x40, 0x7d,
    0x7d, 0xff, 0x2f, 0x00,
    0x00, 0x00,
};

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

static void status_line(M_Int32 y, const M_Char *name, M_Int32 passed,
                        M_Uint32 value, M_Int32 show_value)
{
    M_Char line[48];
    M_Char *cursor = line;
    cursor = append_text(cursor, name);
    cursor = append_text(cursor, passed != 0 ? " PASS" : " WAIT");
    if (show_value != 0) {
        cursor = append_text(cursor, "  ");
        (void)append_uint(cursor, value);
    }
    draw_text(14, y, line,
              passed != 0 ? color(84, 232, 164) : color(255, 196, 92));
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
    font_handle = MC_grpGetFont(0, 12, 0);
    font_ready = 1;
}

static void initialize_system(void)
{
    M_Uint32 memory_id;
    M_Byte *bytes;
    M_Int32 index;
    M_Int32 zero_filled = 1;

    total_memory = MC_knlGetTotalMemory();
    free_memory = MC_knlGetFreeMemory();
    start_time = MC_knlCurrentTime();
    phone_model[0] = '\0';
    system_ready =
        total_memory > 0 && free_memory >= 0 && start_time >= 0 &&
        MC_knlGetSystemProperty("PHONEMODEL", phone_model,
                                ARRAY_COUNT(phone_model)) == M_SUCCESS &&
        phone_model[0] != '\0';

    memory_id = MC_knlCalloc(16);
    bytes = (M_Byte *)MC_GETDPTR(memory_id);
    if (bytes == (M_Byte *)0) {
        memory_ready = 0;
        return;
    }
    for (index = 0; index < 16; ++index) {
        if (bytes[index] != 0u) {
            zero_filled = 0;
        }
    }
    bytes[0] = (M_Byte)'O';
    bytes[1] = (M_Byte)'K';
    memory_ready = zero_filled != 0 && bytes[0] == (M_Byte)'O' &&
                   bytes[1] == (M_Byte)'K';
    MC_knlFree(memory_id);
}

static void initialize_audio(void)
{
    M_Int32 written;
    M_Int32 played;

    audio_clip = MC_mdaClipCreate("audio/mmf", ARRAY_COUNT(test_tone),
                                  (MEDIACB)0);
    if (audio_clip == (MC_MdaClip *)0) {
        audio_ready = 0;
        return;
    }
    written = MC_mdaClipPutData(audio_clip, test_tone,
                                ARRAY_COUNT(test_tone));
    MC_mdaClipSetVolume(audio_clip, 7);
    played = MC_mdaPlay(audio_clip, M_FALSE);
    audio_ready = written == ARRAY_COUNT(test_tone) && played == M_SUCCESS;
}

static void timer_callback(MCTimer *fired_timer, void *parameter)
{
    if (fired_timer == &timer && parameter == (void *)&timer_cookie) {
        timer_ready = 1;
        ++timer_ticks;
    }
    (void)MC_knlSetTimer(&timer, (M_Int64)250, (void *)&timer_cookie);
    paintClet(0, 0, display.m_width, display.m_height);
}

void startClet(M_Int32 argc, M_Char *argv[])
{
    (void)argc;
    (void)argv;
    initialize_graphics();
    initialize_system();
    initialize_audio();
    MC_knlDefTimer(&timer, timer_callback);
    timer_ready = 0;
    timer_ticks = 0u;
    if (MC_knlSetTimer(&timer, (M_Int64)120, (void *)&timer_cookie) !=
        M_SUCCESS) {
        timer_ready = 0;
    }
    paintClet(0, 0, display.m_width, display.m_height);
}

void paintClet(M_Int32 x, M_Int32 y, M_Int32 width, M_Int32 height)
{
    M_Int32 panel_width;
    M_Int32 footer_y;
    M_Uint32 background;
    M_Uint32 panel;
    M_Uint32 accent;
    M_Char model_line[48];
    M_Char *cursor;

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

    background = color(12, 20, 38);
    panel = color(25, 39, 68);
    accent = color(88, 166, 255);
    panel_width = display.m_width - 16;
    footer_y = display.m_height - 36;

    graphics.fg_pixel = background;
    MC_grpFillRect(screen, 0, 0, display.m_width, display.m_height,
                   &graphics);
    graphics.fg_pixel = panel;
    MC_grpFillRect(screen, 8, 42, panel_width, 202, &graphics);
    graphics.fg_pixel = accent;
    MC_grpDrawRect(screen, 8, 42, panel_width, 202, &graphics);
    MC_grpDrawLine(screen, 8, 72, display.m_width - 8, 72, &graphics);
    MC_grpDrawArc(screen, display.m_width - 46, 8, 28, 28, 0, 360,
                  &graphics);
    if ((timer_ticks & 1u) != 0u) {
        MC_grpFillArc(screen, display.m_width - 42, 12, 20, 20, 0, 360,
                      &graphics);
    }

    draw_text(14, 17, "libwipi CONFORMANCE", color(235, 244, 255));
    status_line(52, "GRAPHICS", graphics_ready, 0u, 0);
    status_line(78, "FONT", font_ready, (M_Uint32)font_handle, 1);
    status_line(100, "SYSTEM", system_ready, (M_Uint32)free_memory, 1);
    status_line(122, "MEMORY", memory_ready, (M_Uint32)total_memory, 1);
    status_line(144, "TIMER", timer_ready, timer_ticks, 1);
    status_line(166, "INPUT", input_ready, (M_Uint32)last_key, 1);
    status_line(188, "AUDIO", audio_ready,
                (M_Uint32)ARRAY_COUNT(test_tone), 1);

    cursor = model_line;
    cursor = append_text(cursor, "MODEL  ");
    (void)append_text(cursor, phone_model[0] != '\0' ? phone_model : "unknown");
    draw_text(14, 216, model_line, color(178, 196, 224));
    draw_text(14, footer_y, "PRESS ANY KEY TO VERIFY INPUT",
              input_ready != 0 ? color(84, 232, 164) : color(178, 196, 224));
    MC_grpFlushLcd(0, screen, 0, 0, display.m_width, display.m_height);
}

void destroyClet(void)
{
    MC_knlUnsetTimer(&timer);
    if (audio_clip != (MC_MdaClip *)0) {
        (void)MC_mdaStop(audio_clip);
        (void)MC_mdaClipFree(audio_clip);
        audio_clip = (MC_MdaClip *)0;
    }
}

void pauseClet(void)
{
    MC_knlUnsetTimer(&timer);
}

void resumeClet(void)
{
    (void)MC_knlSetTimer(&timer, (M_Int64)120, (void *)&timer_cookie);
    paintClet(0, 0, display.m_width, display.m_height);
}

void handleCletEvent(M_Int32 type, M_Int32 param1, M_Int32 param2)
{
    (void)param2;
    if (type == WIPI_CLET_EVENT_KEY_PRESS ||
        type == WIPI_CLET_EVENT_KEY_RELEASE) {
        input_ready = 1;
        last_key = param1;
        ++input_count;
        if (type == WIPI_CLET_EVENT_KEY_PRESS &&
            audio_clip != (MC_MdaClip *)0) {
            (void)MC_mdaPlay(audio_clip, M_FALSE);
        }
        paintClet(0, 0, display.m_width, display.m_height);
    }
}
