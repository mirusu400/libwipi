#include <wipi/wipi.h>

#define ARRAY_COUNT(values) ((M_Int32)(sizeof(values) / sizeof((values)[0])))

static M_Char root_name[] = "sdkfs";
static M_Char persistent_name[] = "sdkfs/persist.bin";
static M_Char renamed_name[] = "sdkfs/renamed.bin";
static M_Char temporary_name[] = "sdkfs/delete.bin";
static M_Char temporary_directory[] = "sdkfs/empty";
static M_Byte marker[] = {'L', 'I', 'B', 'W', 'I', 'P', 'I', '1'};

static MC_GrpFrameBuffer screen;
static MC_GrpDisplayInfo display;
static MC_GrpContext graphics;
static M_Int32 font;
static M_Int32 test_passed;
static M_Int32 restart_seen;
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

static M_Int32 listing_contains(const M_Char *listing, M_Int32 capacity,
                                const M_Char *wanted)
{
    M_Int32 offset = 0;
    while (offset < capacity && listing[offset] != '\0') {
        M_Int32 index = 0;
        while (offset + index < capacity && listing[offset + index] != '\0' &&
               wanted[index] != '\0' && listing[offset + index] == wanted[index]) {
            ++index;
        }
        if (wanted[index] == '\0' && offset + index < capacity &&
            listing[offset + index] == '\0') {
            return 1;
        }
        while (offset < capacity && listing[offset] != '\0') {
            ++offset;
        }
        ++offset;
    }
    return 0;
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
        ? color(79, 226, 153)
        : color(255, 102, 111);
    M_Uint32 panel = (redraw_count & 1) != 0
        ? color(37, 57, 69)
        : color(31, 49, 61);

    graphics.fg_pixel = color(8, 23, 29);
    MC_grpFillRect(screen, 0, 0, display.m_width, display.m_height, &graphics);
    graphics.fg_pixel = panel;
    MC_grpFillRect(screen, 10, 50, display.m_width - 20, 184, &graphics);
    graphics.fg_pixel = color(78, 211, 193);
    MC_grpDrawRect(screen, 10, 50, display.m_width - 20, 184, &graphics);

    draw_text(16, "FILESYSTEM LAB", color(239, 248, 248));
    draw_text(70, test_passed != 0 ? "FILESYSTEM PASS" : "FILESYSTEM FAIL",
              result_color);
    draw_text(100, "OPEN WRITE READ CLOSE", color(182, 214, 215));
    draw_text(124, "SEEK TELL ATTRIBUTE", color(182, 214, 215));
    draw_text(148, "LIST RENAME REMOVE", color(182, 214, 215));
    draw_text(178, restart_seen != 0 ? "RESTART FILE PASS" :
                                      "FIRST LAUNCH WRITE",
              restart_seen != 0 ? result_color : color(255, 193, 92));
    draw_text(display.m_height - 34, "OK REDRAWS RESULT",
              color(174, 205, 208));
    MC_grpFlushLcd(0, screen, 0, 0, display.m_width, display.m_height);
}

static M_Int32 prepare_directory(void)
{
    M_Int32 exists = MC_fsIsExist(root_name, 0);
    if (exists != 0) {
        (void)MC_fsMkDir(root_name, 0);
        return 1;
    }
    return MC_fsMkDir(root_name, 0) == M_SUCCESS;
}

static M_Int32 verify_persistent_file(void)
{
    M_Byte readback[8];
    MC_FileInfo info;
    M_Int32 descriptor;
    M_Int32 existed = MC_fsIsExist(persistent_name, 0);

    restart_seen = existed != 0;
    descriptor = MC_fsOpen(
        persistent_name,
        existed != 0 ? MC_FILE_OPEN_RDWR :
                       MC_FILE_OPEN_RDWR | MC_FILE_OPEN_WRTRUNC,
        0);
    if (descriptor < 0) {
        return 0;
    }
    if (existed != 0) {
        if (MC_fsRead(descriptor, readback, ARRAY_COUNT(readback)) !=
                ARRAY_COUNT(readback) ||
            bytes_equal(readback, marker, ARRAY_COUNT(marker)) == 0 ||
            MC_fsSeek(descriptor, 0, MC_FILE_SEEK_SET) != 0) {
            (void)MC_fsClose(descriptor);
            return 0;
        }
    }
    if (MC_fsWrite(descriptor, marker, ARRAY_COUNT(marker)) !=
            ARRAY_COUNT(marker) ||
        MC_fsTell(descriptor) != ARRAY_COUNT(marker) ||
        MC_fsSeek(descriptor, 0, MC_FILE_SEEK_SET) != 0 ||
        MC_fsRead(descriptor, readback, ARRAY_COUNT(readback)) !=
            ARRAY_COUNT(readback) ||
        bytes_equal(readback, marker, ARRAY_COUNT(marker)) == 0 ||
        MC_fsSeek(descriptor, 0, MC_FILE_SEEK_END) != ARRAY_COUNT(marker) ||
        MC_fsClose(descriptor) != M_SUCCESS) {
        return 0;
    }
    if (MC_fsFileAttribute(persistent_name, &info, 0) != M_SUCCESS ||
        info.size != (M_Uint32)ARRAY_COUNT(marker)) {
        return 0;
    }
    if (existed != 0 && MC_fsSetMode(persistent_name, 0, 0) != M_SUCCESS) {
        return 0;
    }
    return 1;
}

static M_Int32 verify_directory_operations(void)
{
    M_Char listing[96];
    M_Int32 descriptor;
    M_Int32 index;

    (void)MC_fsRemove(temporary_name, 0);
    descriptor = MC_fsOpen(temporary_name,
                           MC_FILE_OPEN_RDWR | MC_FILE_OPEN_WRTRUNC, 0);
    if (descriptor < 0 ||
        MC_fsWrite(descriptor, marker, ARRAY_COUNT(marker)) !=
            ARRAY_COUNT(marker) ||
        MC_fsClose(descriptor) != M_SUCCESS ||
        MC_fsRemove(temporary_name, 0) != M_SUCCESS) {
        return 0;
    }

    (void)MC_fsRmDir(temporary_directory, 0);
    if (MC_fsMkDir(temporary_directory, 0) != M_SUCCESS ||
        MC_fsRmDir(temporary_directory, 0) != M_SUCCESS) {
        return 0;
    }
    if (MC_fsRename(persistent_name, renamed_name, 0) != M_SUCCESS ||
        MC_fsIsExist(persistent_name, 0) != 0 ||
        MC_fsIsExist(renamed_name, 0) == 0 ||
        MC_fsRename(renamed_name, persistent_name, 0) != M_SUCCESS) {
        return 0;
    }

    for (index = 0; index < ARRAY_COUNT(listing); ++index) {
        listing[index] = '\0';
    }
    if (MC_fsList(root_name, listing, ARRAY_COUNT(listing), 0) != M_SUCCESS ||
        listing_contains(listing, ARRAY_COUNT(listing), "persist.bin") == 0 ||
        MC_fsGetCounts(root_name, 0) != 1 ||
        MC_fsTotalSpace() <= 0 || MC_fsAvailable() <= 0) {
        return 0;
    }
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
    redraw_count = 0;
    test_passed = prepare_directory() != 0 &&
                  verify_persistent_file() != 0 &&
                  verify_directory_operations() != 0;
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
        ++redraw_count;
        draw_frame();
    }
}
