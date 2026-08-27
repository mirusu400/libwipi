#include <wipi/wipi.h>

#define ARRAY_COUNT(values) ((M_Int32)(sizeof(values) / sizeof((values)[0])))

static const M_Char expected_resource[] = "LIBWIPI RESOURCE OK\n";

static MC_GrpFrameBuffer screen;
static MC_GrpDisplayInfo display;
static MC_GrpContext graphics;
static M_Int32 graphics_ready;
static M_Int32 font_handle;
static M_Int32 allocation_passed;
static M_Int32 calloc_passed;
static M_Int32 resource_passed;
static M_Int32 memory_stats_passed;
static M_Int32 total_memory;
static M_Int32 free_memory_before;
static M_Int32 free_memory_after;
static M_Uint32 run_count;
static M_Char resource_text[32];

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

static void draw_status(M_Int32 y, const M_Char *label, M_Int32 passed)
{
    M_Char line[40];
    M_Char *cursor = line;

    cursor = append_text(cursor, label);
    (void)append_text(cursor, passed != 0 ? "  PASS" : "  FAIL");
    draw_text(16, y, line,
              passed != 0 ? color(76, 224, 155) : color(255, 105, 112));
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

static void run_memory_checks(void)
{
    M_Uint32 allocated_id;
    M_Uint32 zeroed_id;
    M_Uint32 resource_memory_id;
    M_Byte *allocated;
    M_Byte *zeroed;
    M_Byte *resource_data;
    M_Int32 resource_id;
    M_Int32 resource_size;
    M_Int32 index;
    M_Int32 resource_matches;

    allocation_passed = 0;
    calloc_passed = 0;
    resource_passed = 0;
    resource_text[0] = '\0';
    total_memory = MC_knlGetTotalMemory();
    free_memory_before = MC_knlGetFreeMemory();
    memory_stats_passed = total_memory > 0 && free_memory_before >= 0;

    allocated_id = MC_knlAlloc(32);
    zeroed_id = MC_knlCalloc(32);
    allocated = (M_Byte *)MC_GETDPTR(allocated_id);
    zeroed = (M_Byte *)MC_GETDPTR(zeroed_id);
    if (allocated != (M_Byte *)0) {
        for (index = 0; index < 32; ++index) {
            allocated[index] = (M_Byte)(index ^ 0x5a);
        }
        allocation_passed = allocated[0] == 0x5au &&
                            allocated[31] == (M_Byte)(31 ^ 0x5a);
    }
    if (zeroed != (M_Byte *)0) {
        calloc_passed = 1;
        for (index = 0; index < 32; ++index) {
            if (zeroed[index] != 0u) {
                calloc_passed = 0;
            }
        }
    }
    if (allocated_id != 0u) {
        MC_knlFree(allocated_id);
    }
    if (zeroed_id != 0u) {
        MC_knlFree(zeroed_id);
    }

    resource_size = 0;
    resource_id = MC_knlGetResourceID("res/sdk-message.txt", &resource_size);
    resource_memory_id = 0u;
    if (resource_id >= 0 && resource_size == text_length(expected_resource)) {
        resource_memory_id = MC_knlAlloc(resource_size + 1);
    }
    resource_data = (M_Byte *)MC_GETDPTR(resource_memory_id);
    if (resource_data != (M_Byte *)0 &&
        MC_knlGetResource(resource_id, resource_data, resource_size) ==
            M_SUCCESS) {
        resource_matches = 1;
        for (index = 0; index < resource_size; ++index) {
            if (resource_data[index] != (M_Byte)expected_resource[index]) {
                resource_matches = 0;
            }
            if (index < ARRAY_COUNT(resource_text) - 1 &&
                resource_data[index] != (M_Byte)'\n') {
                resource_text[index] = (M_Char)resource_data[index];
                resource_text[index + 1] = '\0';
            }
        }
        resource_passed = resource_matches;
    }
    if (resource_memory_id != 0u) {
        MC_knlFree(resource_memory_id);
    }
    free_memory_after = MC_knlGetFreeMemory();
    ++run_count;
}

static M_Int32 all_checks_passed(void)
{
    return graphics_ready != 0 && memory_stats_passed != 0 &&
           allocation_passed != 0 && calloc_passed != 0 &&
           resource_passed != 0;
}

void paintClet(M_Int32 x, M_Int32 y, M_Int32 width, M_Int32 height)
{
    M_Char line[48];
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

    graphics.fg_pixel = color(12, 25, 37);
    MC_grpFillRect(screen, 0, 0, display.m_width, display.m_height, &graphics);
    graphics.fg_pixel = color(28, 48, 66);
    MC_grpFillRect(screen, 9, 50, display.m_width - 18, 212, &graphics);
    graphics.fg_pixel = color(72, 199, 159);
    MC_grpDrawRect(screen, 9, 50, display.m_width - 18, 212, &graphics);
    draw_text(14, 14, "MEMORY + RESOURCE", color(239, 248, 255));
    draw_text(14, 33, "HANDLE AND PACKAGE CHECKS", color(151, 184, 210));
    draw_status(68, "MEMORY STATS", memory_stats_passed);
    draw_status(96, "ALLOC + WRITE", allocation_passed);
    draw_status(124, "CALLOC ZERO", calloc_passed);
    draw_status(152, "RESOURCE LOOKUP", resource_passed);

    cursor = line;
    cursor = append_text(cursor, "TOTAL / FREE  ");
    cursor = append_uint(cursor, (M_Uint32)total_memory);
    cursor = append_text(cursor, " / ");
    (void)append_uint(cursor, (M_Uint32)free_memory_after);
    draw_text(16, 188, line, color(190, 210, 230));
    draw_text(16, 216,
              resource_text[0] != '\0' ? resource_text : "NO RESOURCE TEXT",
              color(255, 214, 92));

    cursor = line;
    cursor = append_text(cursor, "RUN  ");
    (void)append_uint(cursor, run_count);
    draw_text(16, 242, line, color(151, 184, 210));
    draw_text(14, display.m_height - 20, "OK: RUN CHECKS AGAIN",
              color(190, 210, 230));
    MC_grpFlushLcd(0, screen, 0, 0, display.m_width, display.m_height);
}

void startClet(M_Int32 argc, M_Char *argv[])
{
    (void)argc;
    (void)argv;
    run_count = 0u;
    initialize_graphics();
    run_memory_checks();
    paintClet(0, 0, display.m_width, display.m_height);
    if (all_checks_passed() == 0) {
        MC_knlExit(1);
    }
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
    if (type == WIPI_CLET_EVENT_KEY_PRESS &&
        (param1 == WIPI_CLET_KEY_SELECT || param1 == '5')) {
        run_memory_checks();
        paintClet(0, 0, display.m_width, display.m_height);
        if (all_checks_passed() == 0) {
            MC_knlExit(1);
        }
    }
}
