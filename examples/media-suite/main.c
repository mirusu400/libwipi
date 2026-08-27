#include <wipi/wipi.h>

#define ARRAY_COUNT(values) ((M_Int32)(sizeof(values) / sizeof((values)[0])))

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
static M_Byte memory_data[] = {'R', 'A', 'M'};
static M_Byte package_name[] = "res/clip-data.bin";

static MC_GrpFrameBuffer screen;
static MC_GrpDisplayInfo display;
static MC_GrpContext graphics;
static MC_MdaClip *audio_clip;
static M_Int32 font;
static M_Int32 test_passed;
static M_Int32 paused;
static M_Int32 redraw_count;

static M_Int32 text_length(const M_Char *text)
{
    M_Int32 length = 0;
    while (text[length] != '\0') {
        ++length;
    }
    return length;
}

static M_Int32 bytes_equal(const M_Byte *left, const M_Byte *right,
                           M_Int32 length)
{
    M_Int32 index;
    for (index = 0; index < length; ++index) {
        if (left[index] != right[index]) {
            return 0;
        }
    }
    return 1;
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
    M_Uint32 result_color = test_passed != 0
        ? color(91, 231, 157)
        : color(255, 105, 117);
    M_Int32 bar;

    graphics.fg_pixel = color(22, 13, 37);
    MC_grpFillRect(screen, 0, 0, display.m_width, display.m_height, &graphics);
    graphics.fg_pixel = color(48, 31, 73);
    MC_grpFillRect(screen, 10, 50, display.m_width - 20, 184, &graphics);
    graphics.fg_pixel = color(196, 124, 255);
    MC_grpDrawRect(screen, 10, 50, display.m_width - 20, 184, &graphics);

    draw_text(16, "MEDIA API SUITE", color(247, 241, 255));
    draw_text(70, test_passed != 0 ? "ALL 21 MEDIA PASS" :
                                      "MEDIA API FAIL",
              result_color);
    draw_text(100, "BUFFER + FILE CLIPS", color(211, 191, 232));
    draw_text(124, "PLAY PAUSE RESUME STOP", color(211, 191, 232));
    draw_text(148, "VOLUME MUTE RECORD", color(211, 191, 232));
    draw_text(178, paused != 0 ? "STATE PAUSED" : "STATE PLAYING",
              paused != 0 ? color(255, 194, 92) : result_color);
    for (bar = 0; bar < 8; ++bar) {
        graphics.fg_pixel = color(104 + bar * 15, 104 + bar * 9,
                                  235 - bar * 8);
        MC_grpFillRect(screen, 24 + bar * 24, 218 - ((bar + redraw_count) % 4) * 8,
                       13, 10 + ((bar + redraw_count) % 4) * 8, &graphics);
    }
    draw_text(display.m_height - 34, "OK TOGGLES PLAYBACK",
              color(205, 188, 225));
    MC_grpFlushLcd(0, screen, 0, 0, display.m_width, display.m_height);
}

static M_Int32 exercise_data_clip(void)
{
    static const M_Char type_name[] = "application/octet-stream";
    M_Byte type_buffer[32];
    M_Byte output[3];
    MC_MdaClip *clip;
    M_Int32 file_size = 24;

    clip = MC_mdaClipCreate((M_Char *)type_name, 96, (MEDIACB)0);
    if (clip == (MC_MdaClip *)0) {
        return 0;
    }
    if (MC_mdaClipGetType(clip, type_buffer, ARRAY_COUNT(type_buffer)) !=
            text_length(type_name) ||
        bytes_equal(type_buffer, (const M_Byte *)type_name,
                    text_length(type_name)) == 0 ||
        MC_mdaClipPutData(clip, memory_data, ARRAY_COUNT(memory_data)) !=
            ARRAY_COUNT(memory_data) ||
        MC_mdaClipAvailableDataSize(clip) != ARRAY_COUNT(memory_data) ||
        MC_mdaClipGetData(clip, output, ARRAY_COUNT(output)) !=
            ARRAY_COUNT(output) ||
        bytes_equal(output, memory_data, ARRAY_COUNT(output)) == 0 ||
        MC_mdaClipClearData(clip) != M_SUCCESS ||
        MC_mdaClipPutDataByFile(clip, package_name, file_size, 1) != file_size ||
        MC_mdaClipAvailableDataSize(clip) != file_size ||
        MC_mdaClipSetPosition(clip, 0) != M_SUCCESS) {
        (void)MC_mdaClipFree(clip);
        return 0;
    }
    MC_mdaClipSetVolume(clip, 37);
    if (MC_mdaClipGetVolume(clip) != 37 ||
        MC_mdaRecord(clip) != M_SUCCESS ||
        MC_mdaClipFree(clip) != M_SUCCESS) {
        return 0;
    }
    return 1;
}

static M_Int32 exercise_audio_clip(void)
{
    audio_clip = MC_mdaClipCreate("audio/mmf", ARRAY_COUNT(test_tone),
                                  (MEDIACB)0);
    if (audio_clip == (MC_MdaClip *)0 ||
        MC_mdaClipPutData(audio_clip, test_tone, ARRAY_COUNT(test_tone)) !=
            ARRAY_COUNT(test_tone)) {
        return 0;
    }
    MC_mdaClipSetVolume(audio_clip, 72);
    if (MC_mdaClipGetVolume(audio_clip) != 72 ||
        MC_mdaPlay(audio_clip, M_TRUE) != M_SUCCESS ||
        MC_mdaPause(audio_clip) != M_SUCCESS ||
        MC_mdaResume(audio_clip) != M_SUCCESS ||
        MC_mdaStop(audio_clip) != M_SUCCESS ||
        MC_mdaPlay(audio_clip, M_TRUE) != M_SUCCESS) {
        return 0;
    }
    paused = 0;
    return 1;
}

static M_Int32 exercise_global_media(void)
{
    MC_mdaSetVolume(63);
    if (MC_mdaGetVolume() != 63 ||
        MC_mdaSetMuteState(0, M_TRUE) != M_SUCCESS ||
        MC_mdaGetMuteState(0) != M_TRUE ||
        MC_mdaSetMuteState(0, M_FALSE) != M_SUCCESS ||
        MC_mdaGetMuteState(0) != M_FALSE) {
        return 0;
    }
    MC_mdaVibrator(85, 350);
    return 1;
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
    audio_clip = (MC_MdaClip *)0;
    redraw_count = 0;
    paused = 0;
    test_passed = exercise_data_clip() != 0 &&
                  exercise_global_media() != 0 &&
                  exercise_audio_clip() != 0;
    draw_frame();
}

void destroyClet(void)
{
    if (audio_clip != (MC_MdaClip *)0) {
        (void)MC_mdaStop(audio_clip);
        (void)MC_mdaClipFree(audio_clip);
        audio_clip = (MC_MdaClip *)0;
    }
    MC_mdaVibrator(0, 0);
}

void pauseClet(void)
{
    if (audio_clip != (MC_MdaClip *)0) {
        (void)MC_mdaPause(audio_clip);
        paused = 1;
    }
}

void resumeClet(void)
{
    if (audio_clip != (MC_MdaClip *)0) {
        (void)MC_mdaResume(audio_clip);
        paused = 0;
    }
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
    if (type != WIPI_CLET_EVENT_KEY_PRESS ||
        audio_clip == (MC_MdaClip *)0) {
        return;
    }
    if (param1 == WIPI_CLET_KEY_SELECT || param1 == '5') {
        if (paused != 0) {
            (void)MC_mdaResume(audio_clip);
            paused = 0;
        } else {
            (void)MC_mdaPause(audio_clip);
            paused = 1;
        }
    }
    ++redraw_count;
    draw_frame();
}
