#include <wipi/wipi.h>

#define ARRAY_COUNT(values) ((M_Int32)(sizeof(values) / sizeof((values)[0])))

static const M_Char primary_name[] = "libwipi-crud";
static const M_Char temporary_name[] = "libwipi-crud-temp";

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

static M_Int32 contains_name(const M_Byte *names, M_Int32 capacity,
                             const M_Char *wanted)
{
    M_Int32 offset = 0;
    while (offset < capacity && names[offset] != 0) {
        M_Int32 index = 0;
        while (offset + index < capacity && names[offset + index] != 0 &&
               wanted[index] != '\0' &&
               names[offset + index] == (M_Byte)wanted[index]) {
            ++index;
        }
        if (wanted[index] == '\0' && offset + index < capacity &&
            names[offset + index] == 0) {
            return 1;
        }
        while (offset < capacity && names[offset] != 0) {
            ++offset;
        }
        ++offset;
    }
    return 0;
}

static M_Int32 compare_records(const void *left, const void *right)
{
    const M_Byte *left_record = (const M_Byte *)left;
    const M_Byte *right_record = (const M_Byte *)right;
    return (M_Int32)left_record[0] - (M_Int32)right_record[0];
}

static M_Int32 accept_record(const void *record)
{
    return ((const M_Byte *)record)[0] != 0 ? 1 : 0;
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
        ? color(80, 226, 151)
        : color(255, 103, 112);
    M_Uint32 panel = (redraw_count & 1) != 0
        ? color(34, 50, 78)
        : color(29, 44, 69);

    graphics.fg_pixel = color(9, 18, 34);
    MC_grpFillRect(screen, 0, 0, display.m_width, display.m_height, &graphics);
    graphics.fg_pixel = panel;
    MC_grpFillRect(screen, 10, 50, display.m_width - 20, 178, &graphics);
    graphics.fg_pixel = color(114, 168, 255);
    MC_grpDrawRect(screen, 10, 50, display.m_width - 20, 178, &graphics);

    draw_text(16, "DATABASE CRUD LAB", color(240, 246, 255));
    draw_text(70, test_passed != 0 ? "DATABASE CRUD PASS" :
                                      "DATABASE CRUD FAIL",
              result_color);
    draw_text(100, "INSERT SELECT UPDATE", color(190, 210, 238));
    draw_text(124, "DELETE LIST SORT", color(190, 210, 238));
    draw_text(148, "MODE COUNT SIZE", color(190, 210, 238));
    draw_text(178, restart_seen != 0 ? "RESTART DATA PASS" :
                                      "FIRST LAUNCH WRITE",
              restart_seen != 0 ? result_color : color(255, 192, 91));
    draw_text(display.m_height - 34, "OK REDRAWS RESULT",
              color(178, 198, 226));
    MC_grpFlushLcd(0, screen, 0, 0, display.m_width, display.m_height);
}

static void set_record(M_Byte *record, M_Byte value)
{
    M_Int32 index;
    record[0] = value;
    for (index = 1; index < 8; ++index) {
        record[index] = (M_Byte)(value + index);
    }
}

static M_Int32 verify_record(M_Int32 database, M_Int32 record_id,
                             M_Byte value)
{
    M_Byte expected[8];
    M_Byte actual[8];
    set_record(expected, value);
    if (MC_dbSelectRecord(database, record_id, actual,
                          ARRAY_COUNT(actual)) != M_SUCCESS) {
        return 0;
    }
    return bytes_equal(expected, actual, ARRAY_COUNT(actual));
}

static M_Int32 exercise_primary_database(void)
{
    M_Byte record[8];
    M_Byte database_names[96];
    M_Int32 listed[4];
    M_Int32 sorted[4];
    M_Int32 database;
    M_Int32 inserted;
    M_Int32 expected_count;
    M_Int32 list_count;
    M_Int32 sort_count;
    M_Int32 existed = MC_dbGetAccessMode((M_Char *)primary_name) == 0;

    restart_seen = existed;
    database = MC_dbOpenDataBase((M_Char *)primary_name, 8, M_TRUE, 0);
    if (database < 0 || MC_dbGetRecordSize(database) != 8) {
        return 0;
    }

    if (existed == 0) {
        set_record(record, 30);
        if (MC_dbInsertRecord(database, record, 8) != 1) {
            return 0;
        }
        set_record(record, 10);
        if (MC_dbInsertRecord(database, record, 8) != 2) {
            return 0;
        }
        set_record(record, 20);
        if (MC_dbInsertRecord(database, record, 8) != 3) {
            return 0;
        }
        set_record(record, 40);
        if (MC_dbUpdateRecord(database, 2, record, 8) != M_SUCCESS ||
            verify_record(database, 2, 40) == 0) {
            return 0;
        }
        expected_count = 3;
    } else {
        if (verify_record(database, 2, 40) == 0 ||
            verify_record(database, 3, 20) == 0) {
            return 0;
        }
        set_record(record, 50);
        inserted = MC_dbInsertRecord(database, record, 8);
        if (inserted <= 3) {
            return 0;
        }
        set_record(record, 25);
        if (MC_dbUpdateRecord(database, inserted, record, 8) != M_SUCCESS) {
            return 0;
        }
        expected_count = 3;
    }

    if (MC_dbGetNumberOfRecords(database) != expected_count) {
        return 0;
    }
    list_count = MC_dbListRecords(database, listed, (M_Int32)sizeof(listed));
    sort_count = MC_dbSortRecords(database, sorted, (M_Int32)sizeof(sorted),
                                  compare_records, accept_record);
    if (list_count != expected_count || sort_count != expected_count) {
        return 0;
    }
    if (existed == 0) {
        if (listed[0] != 1 || listed[1] != 2 || listed[2] != 3 ||
            sorted[0] != 3 || sorted[1] != 1 || sorted[2] != 2 ||
            MC_dbDeleteRecord(database, 1) != M_SUCCESS) {
            return 0;
        }
    } else {
        inserted = listed[expected_count - 1];
        if (sorted[0] != 3 || sorted[1] != inserted || sorted[2] != 2 ||
            MC_dbDeleteRecord(database, inserted) != M_SUCCESS) {
            return 0;
        }
    }
    if (MC_dbGetNumberOfRecords(database) != 2) {
        return 0;
    }

    if (existed != 0) {
        M_Int32 index;
        for (index = 0; index < ARRAY_COUNT(database_names); ++index) {
            database_names[index] = 0;
        }
        if (MC_dbListDataBases(database_names,
                               ARRAY_COUNT(database_names)) != M_SUCCESS ||
            contains_name(database_names, ARRAY_COUNT(database_names),
                          primary_name) == 0) {
            return 0;
        }
    }

    return MC_dbCloseDataBase(database) == M_SUCCESS;
}

static M_Int32 exercise_database_delete(void)
{
    M_Int32 temporary;
    (void)MC_dbDeleteDataBase((M_Char *)temporary_name, 0);
    temporary = MC_dbOpenDataBase((M_Char *)temporary_name, 4, M_TRUE, 0);
    if (temporary < 0 || MC_dbCloseDataBase(temporary) != M_SUCCESS) {
        return 0;
    }
    return MC_dbDeleteDataBase((M_Char *)temporary_name, 0) == M_SUCCESS;
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
    test_passed = exercise_primary_database() != 0 &&
                  exercise_database_delete() != 0;
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
