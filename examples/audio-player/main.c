#include <wipi/wipi.h>

#define ARRAY_COUNT(values) ((M_Int32)(sizeof(values) / sizeof((values)[0])))

enum {
    PLAYER_STOPPED = 0,
    PLAYER_PLAYING = 1,
    MIN_VOLUME = 0,
    MAX_VOLUME = 10
};

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

static MC_GrpFrameBuffer screen;
static MC_GrpDisplayInfo display;
static MC_GrpContext graphics;
static MC_MdaClip *clip;
static M_Int32 graphics_ready;
static M_Int32 audio_ready;
static M_Int32 font_handle;
static M_Int32 volume;
static M_Int32 player_state;
static M_Uint32 play_count;

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

static M_Int32 play_tone(void)
{
    if (clip == (MC_MdaClip *)0) {
        return 0;
    }
    (void)MC_mdaStop(clip);
    if (MC_mdaPlay(clip, M_FALSE) != M_SUCCESS) {
        player_state = PLAYER_STOPPED;
        return 0;
    }
    player_state = PLAYER_PLAYING;
    ++play_count;
    return 1;
}

static void initialize_audio(void)
{
    M_Int32 written;

    volume = 7;
    clip = MC_mdaClipCreate("audio/mmf", ARRAY_COUNT(test_tone), (MEDIACB)0);
    if (clip == (MC_MdaClip *)0) {
        audio_ready = 0;
        return;
    }
    written = MC_mdaClipPutData(clip, test_tone, ARRAY_COUNT(test_tone));
    MC_mdaClipSetVolume(clip, volume);
    volume = MC_mdaClipGetVolume(clip);
    audio_ready = written == ARRAY_COUNT(test_tone) && volume == 7;
    if (audio_ready != 0) {
        audio_ready = play_tone();
    }
}

static void release_audio(void)
{
    if (clip != (MC_MdaClip *)0) {
        (void)MC_mdaStop(clip);
        (void)MC_mdaClipFree(clip);
        clip = (MC_MdaClip *)0;
    }
    player_state = PLAYER_STOPPED;
}

static void change_volume(M_Int32 delta)
{
    if (clip == (MC_MdaClip *)0) {
        return;
    }
    volume += delta;
    if (volume < MIN_VOLUME) {
        volume = MIN_VOLUME;
    } else if (volume > MAX_VOLUME) {
        volume = MAX_VOLUME;
    }
    MC_mdaClipSetVolume(clip, volume);
    volume = MC_mdaClipGetVolume(clip);
}

void paintClet(M_Int32 x, M_Int32 y, M_Int32 width, M_Int32 height)
{
    M_Char line[40];
    M_Char *cursor;
    M_Int32 index;
    M_Int32 bar_height;

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

    graphics.fg_pixel = color(19, 15, 38);
    MC_grpFillRect(screen, 0, 0, display.m_width, display.m_height, &graphics);
    graphics.fg_pixel = color(42, 30, 75);
    MC_grpFillRect(screen, 12, 54, display.m_width - 24, 180, &graphics);
    graphics.fg_pixel = color(176, 112, 255);
    MC_grpDrawRect(screen, 12, 54, display.m_width - 24, 180, &graphics);
    draw_text(14, 14, "SYNTHETIC AUDIO PLAYER", color(246, 242, 255));
    draw_text(14, 34, "ORIGINAL TWO-NOTE SMAF", color(184, 164, 222));

    for (index = 0; index < 9; ++index) {
        bar_height = 24 + ((index * 19 + (M_Int32)play_count * 7) % 70);
        graphics.fg_pixel = color(82 + index * 17, 205 - index * 9,
                                  246 - index * 8);
        MC_grpFillRect(screen, 28 + index * 20, 180 - bar_height,
                       11, bar_height, &graphics);
    }

    draw_text(22, 196,
              player_state == PLAYER_PLAYING ? "STATE  PLAYING" :
                                               "STATE  STOPPED",
              player_state == PLAYER_PLAYING ? color(89, 230, 166) :
                                               color(255, 181, 91));
    cursor = line;
    cursor = append_text(cursor, "VOLUME  ");
    cursor = append_uint(cursor, (M_Uint32)volume);
    cursor = append_text(cursor, "    PLAYS  ");
    (void)append_uint(cursor, play_count);
    draw_text(22, 218, line, color(231, 224, 247));

    draw_text(14, 250, "OK PLAY  RIGHT RELOAD", color(194, 180, 226));
    draw_text(14, 270, "LEFT      STOP", color(194, 180, 226));
    draw_text(14, 290, "UP/DOWN   VOLUME", color(194, 180, 226));
    MC_grpFlushLcd(0, screen, 0, 0, display.m_width, display.m_height);
}

void startClet(M_Int32 argc, M_Char *argv[])
{
    (void)argc;
    (void)argv;
    clip = (MC_MdaClip *)0;
    play_count = 0u;
    player_state = PLAYER_STOPPED;
    initialize_graphics();
    initialize_audio();
    paintClet(0, 0, display.m_width, display.m_height);
    if (graphics_ready == 0 || audio_ready == 0) {
        MC_knlExit(1);
    }
}

void destroyClet(void)
{
    release_audio();
}

void pauseClet(void)
{
    if (clip != (MC_MdaClip *)0) {
        (void)MC_mdaStop(clip);
        player_state = PLAYER_STOPPED;
    }
}

void resumeClet(void)
{
    if (audio_ready != 0) {
        (void)play_tone();
    }
    paintClet(0, 0, display.m_width, display.m_height);
}

void handleCletEvent(M_Int32 type, M_Int32 param1, M_Int32 param2)
{
    (void)param2;
    if (type != WIPI_CLET_EVENT_KEY_PRESS || clip == (MC_MdaClip *)0) {
        return;
    }
    if (param1 == WIPI_CLET_KEY_SELECT || param1 == '5') {
        (void)play_tone();
    } else if (param1 == WIPI_CLET_KEY_RIGHT || param1 == '6') {
        release_audio();
        initialize_audio();
    } else if (param1 == WIPI_CLET_KEY_LEFT || param1 == '4') {
        (void)MC_mdaStop(clip);
        player_state = PLAYER_STOPPED;
    } else if (param1 == WIPI_CLET_KEY_UP || param1 == '2') {
        change_volume(1);
    } else if (param1 == WIPI_CLET_KEY_DOWN || param1 == '8') {
        change_volume(-1);
    }
    paintClet(0, 0, display.m_width, display.m_height);
}
