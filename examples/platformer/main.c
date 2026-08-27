#include <wipi/wipi.h>

#define ARRAY_COUNT(values) ((M_Int32)(sizeof(values) / sizeof((values)[0])))

enum {
    WORLD_WIDTH = 1280,
    PLAYER_WIDTH = 14,
    PLAYER_HEIGHT = 20,
    PLAYER_SPEED = 3,
    PLAYER_JUMP_SPEED = -10,
    PLAYER_MAX_FALL_SPEED = 9,
    HAZARD_WIDTH = 16,
    HAZARD_HEIGHT = 14,
    TIMER_PERIOD_MS = 50,
    GAME_PLAYING = 0,
    GAME_WON = 1
};

typedef struct GameRect {
    M_Int32 x;
    M_Int32 y;
    M_Int32 width;
    M_Int32 height;
} GameRect;

typedef struct GameOrb {
    M_Int32 x;
    M_Int32 y;
    M_Boolean collected;
} GameOrb;

typedef struct GameHazard {
    M_Int32 x;
    M_Int32 y;
    M_Int32 minimum_x;
    M_Int32 maximum_x;
    M_Int32 direction;
    M_Boolean active;
} GameHazard;

typedef struct GamePalette {
    M_Uint32 sky;
    M_Uint32 cloud;
    M_Uint32 hill_far;
    M_Uint32 hill_near;
    M_Uint32 platform;
    M_Uint32 platform_top;
    M_Uint32 player;
    M_Uint32 player_light;
    M_Uint32 hazard;
    M_Uint32 orb;
    M_Uint32 portal;
    M_Uint32 ink;
    M_Uint32 panel;
    M_Uint32 white;
} GamePalette;

static const GameRect platforms[] = {
    {0, 210, 210, 30},
    {250, 210, 260, 30},
    {550, 210, 180, 30},
    {770, 210, 230, 30},
    {1040, 210, 240, 30},
    {100, 170, 72, 10},
    {285, 160, 80, 10},
    {405, 130, 70, 10},
    {575, 170, 100, 10},
    {690, 140, 60, 10},
    {825, 165, 90, 10},
    {950, 125, 80, 10},
    {1070, 170, 60, 10},
};

static GameOrb orbs[] = {
    {132, 145, M_FALSE},
    {318, 135, M_FALSE},
    {438, 105, M_FALSE},
    {612, 145, M_FALSE},
    {718, 115, M_FALSE},
    {866, 140, M_FALSE},
    {990, 100, M_FALSE},
    {1102, 145, M_FALSE},
};

static GameHazard hazards[] = {
    {430, 196, 390, 490, 1, M_TRUE},
    {846, 151, 830, 895, 1, M_TRUE},
    {1090, 196, 1060, 1150, -1, M_TRUE},
};

static MC_GrpFrameBuffer screen;
static MC_GrpDisplayInfo display;
static MC_GrpContext graphics;
static MCTimer game_timer;
static M_Uint32 timer_cookie = 0x534b5948u;
static M_Int32 font_handle;
static M_Int32 graphics_ready;
static M_Int32 timer_defined;
static M_Int32 player_x;
static M_Int32 player_y;
static M_Int32 player_velocity_y;
static M_Int32 player_grounded;
static M_Int32 player_facing;
static M_Int32 moving_left;
static M_Int32 moving_right;
static M_Int32 camera_x;
static M_Int32 score;
static M_Int32 lives;
static M_Int32 collected_orbs;
static M_Int32 game_state;
static GamePalette palette;

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

static void initialize_palette(void)
{
    palette.sky = color(92, 184, 236);
    palette.cloud = color(236, 248, 255);
    palette.hill_far = color(102, 194, 162);
    palette.hill_near = color(47, 143, 112);
    palette.platform = color(78, 68, 96);
    palette.platform_top = color(126, 222, 132);
    palette.player = color(91, 70, 214);
    palette.player_light = color(106, 231, 240);
    palette.hazard = color(240, 104, 68);
    palette.orb = color(255, 214, 70);
    palette.portal = color(234, 104, 226);
    palette.ink = color(18, 26, 48);
    palette.panel = color(27, 38, 68);
    palette.white = color(245, 250, 255);
}

static void draw_text(M_Int32 x, M_Int32 y, const M_Char *text,
                      M_Uint32 foreground)
{
    graphics.fg_pixel = foreground;
    graphics.font = font_handle;
    MC_grpDrawString(screen, x, y, text, text_length(text), &graphics);
}

static M_Int32 overlaps(M_Int32 first_x, M_Int32 first_y,
                        M_Int32 first_width, M_Int32 first_height,
                        M_Int32 second_x, M_Int32 second_y,
                        M_Int32 second_width, M_Int32 second_height)
{
    return first_x < second_x + second_width &&
           first_x + first_width > second_x &&
           first_y < second_y + second_height &&
           first_y + first_height > second_y;
}

static void reset_player(void)
{
    player_x = 34;
    player_y = 190;
    player_velocity_y = 0;
    player_grounded = 1;
    player_facing = 1;
    moving_left = 0;
    moving_right = 0;
    camera_x = 0;
}

static void reset_course(void)
{
    M_Int32 index;
    for (index = 0; index < ARRAY_COUNT(orbs); ++index) {
        orbs[index].collected = M_FALSE;
    }
    hazards[0].x = 430;
    hazards[0].direction = 1;
    hazards[1].x = 846;
    hazards[1].direction = 1;
    hazards[2].x = 1090;
    hazards[2].direction = -1;
    for (index = 0; index < ARRAY_COUNT(hazards); ++index) {
        hazards[index].active = M_TRUE;
    }
    score = 0;
    lives = 3;
    collected_orbs = 0;
    game_state = GAME_PLAYING;
    reset_player();
}

static void lose_life(void)
{
    --lives;
    if (lives <= 0) {
        reset_course();
    } else {
        reset_player();
    }
}

static void start_jump(void)
{
    if (game_state == GAME_PLAYING && player_grounded != 0) {
        player_velocity_y = PLAYER_JUMP_SPEED;
        player_grounded = 0;
    }
}

static void update_hazards(void)
{
    M_Int32 index;
    for (index = 0; index < ARRAY_COUNT(hazards); ++index) {
        GameHazard *hazard = &hazards[index];
        if (hazard->active == M_FALSE) {
            continue;
        }
        hazard->x += hazard->direction;
        if (hazard->x <= hazard->minimum_x) {
            hazard->x = hazard->minimum_x;
            hazard->direction = 1;
        } else if (hazard->x >= hazard->maximum_x) {
            hazard->x = hazard->maximum_x;
            hazard->direction = -1;
        }
    }
}

static M_Int32 handle_hazard_collisions(M_Int32 previous_y)
{
    M_Int32 index;
    for (index = 0; index < ARRAY_COUNT(hazards); ++index) {
        GameHazard *hazard = &hazards[index];
        if (hazard->active == M_FALSE ||
            overlaps(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT,
                     hazard->x, hazard->y, HAZARD_WIDTH, HAZARD_HEIGHT) == 0) {
            continue;
        }
        if (player_velocity_y > 0 &&
            previous_y + PLAYER_HEIGHT <= hazard->y + 4) {
            hazard->active = M_FALSE;
            player_velocity_y = -7;
            score += 50;
        } else {
            lose_life();
            return 1;
        }
    }
    return 0;
}

static void collect_orbs(void)
{
    M_Int32 index;
    for (index = 0; index < ARRAY_COUNT(orbs); ++index) {
        if (orbs[index].collected == M_FALSE &&
            overlaps(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT,
                     orbs[index].x - 5, orbs[index].y - 5, 10, 10) != 0) {
            orbs[index].collected = M_TRUE;
            ++collected_orbs;
            score += 10;
        }
    }
}

static void update_player(void)
{
    M_Int32 index;
    M_Int32 previous_y = player_y;
    M_Int32 next_y;

    if (moving_left != 0 && moving_right == 0) {
        player_x -= PLAYER_SPEED;
        player_facing = -1;
    } else if (moving_right != 0 && moving_left == 0) {
        player_x += PLAYER_SPEED;
        player_facing = 1;
    }
    if (player_x < 0) {
        player_x = 0;
    } else if (player_x > WORLD_WIDTH - PLAYER_WIDTH) {
        player_x = WORLD_WIDTH - PLAYER_WIDTH;
    }

    ++player_velocity_y;
    if (player_velocity_y > PLAYER_MAX_FALL_SPEED) {
        player_velocity_y = PLAYER_MAX_FALL_SPEED;
    }
    next_y = player_y + player_velocity_y;
    player_grounded = 0;
    if (player_velocity_y >= 0) {
        for (index = 0; index < ARRAY_COUNT(platforms); ++index) {
            const GameRect *platform = &platforms[index];
            if (player_x + PLAYER_WIDTH > platform->x &&
                player_x < platform->x + platform->width &&
                previous_y + PLAYER_HEIGHT <= platform->y &&
                next_y + PLAYER_HEIGHT >= platform->y) {
                next_y = platform->y - PLAYER_HEIGHT;
                player_velocity_y = 0;
                player_grounded = 1;
            }
        }
    }
    player_y = next_y;
    if (player_y > display.m_height + 40) {
        lose_life();
        return;
    }
    update_hazards();
    if (handle_hazard_collisions(previous_y) != 0) {
        return;
    }
    collect_orbs();
    if (player_x + PLAYER_WIDTH >= 1200 && player_y < 210) {
        game_state = GAME_WON;
        moving_left = 0;
        moving_right = 0;
        score += 100;
    }

    camera_x = player_x - display.m_width / 3;
    if (camera_x < 0) {
        camera_x = 0;
    } else if (camera_x > WORLD_WIDTH - display.m_width) {
        camera_x = WORLD_WIDTH - display.m_width;
    }
}

static void update_game(void)
{
    if (game_state == GAME_PLAYING) {
        update_player();
    }
}

static void fill_world_rect(M_Int32 x, M_Int32 y, M_Int32 width,
                            M_Int32 height, M_Uint32 fill)
{
    M_Int32 screen_x = x - camera_x;
    if (screen_x + width <= 0 || screen_x >= display.m_width) {
        return;
    }
    graphics.fg_pixel = fill;
    MC_grpFillRect(screen, screen_x, y, width, height, &graphics);
}

static void draw_background(void)
{
    M_Int32 cloud_shift = camera_x / 3;
    graphics.fg_pixel = palette.sky;
    MC_grpFillRect(screen, 0, 0, display.m_width, display.m_height,
                   &graphics);

    graphics.fg_pixel = palette.cloud;
    MC_grpFillArc(screen, 52 - cloud_shift, 42, 42, 22, 0, 360, &graphics);
    MC_grpFillArc(screen, 76 - cloud_shift, 36, 48, 28, 0, 360, &graphics);
    MC_grpFillArc(screen, 235 - cloud_shift, 55, 58, 24, 0, 360, &graphics);
    MC_grpFillArc(screen, 440 - cloud_shift, 32, 52, 25, 0, 360, &graphics);

    graphics.fg_pixel = palette.hill_far;
    MC_grpFillArc(screen, -80 - camera_x / 5, 118, 250, 170, 0, 180,
                  &graphics);
    MC_grpFillArc(screen, 120 - camera_x / 5, 128, 280, 170, 0, 180,
                  &graphics);
    graphics.fg_pixel = palette.hill_near;
    MC_grpFillArc(screen, -20 - camera_x / 2, 154, 210, 115, 0, 180,
                  &graphics);
    MC_grpFillArc(screen, 210 - camera_x / 2, 164, 230, 110, 0, 180,
                  &graphics);
}

static void draw_platforms(void)
{
    M_Int32 index;
    for (index = 0; index < ARRAY_COUNT(platforms); ++index) {
        const GameRect *platform = &platforms[index];
        fill_world_rect(platform->x, platform->y, platform->width,
                        platform->height, palette.platform);
        fill_world_rect(platform->x, platform->y, platform->width, 4,
                        palette.platform_top);
    }
}

static void draw_orbs(void)
{
    M_Int32 index;
    graphics.fg_pixel = palette.orb;
    for (index = 0; index < ARRAY_COUNT(orbs); ++index) {
        M_Int32 screen_x;
        if (orbs[index].collected != M_FALSE) {
            continue;
        }
        screen_x = orbs[index].x - camera_x;
        if (screen_x < -10 || screen_x > display.m_width + 10) {
            continue;
        }
        MC_grpFillArc(screen, screen_x - 5, orbs[index].y - 5, 10, 10,
                      0, 360, &graphics);
        graphics.fg_pixel = palette.white;
        MC_grpDrawLine(screen, screen_x - 1, orbs[index].y - 3,
                       screen_x - 1, orbs[index].y, &graphics);
        graphics.fg_pixel = palette.orb;
    }
}

static void draw_hazards(void)
{
    M_Int32 index;
    for (index = 0; index < ARRAY_COUNT(hazards); ++index) {
        GameHazard *hazard = &hazards[index];
        M_Int32 screen_x = hazard->x - camera_x;
        if (hazard->active == M_FALSE || screen_x < -HAZARD_WIDTH ||
            screen_x > display.m_width) {
            continue;
        }
        graphics.fg_pixel = palette.hazard;
        MC_grpFillRect(screen, screen_x, hazard->y, HAZARD_WIDTH,
                       HAZARD_HEIGHT, &graphics);
        graphics.fg_pixel = palette.ink;
        MC_grpFillRect(screen, screen_x + 3, hazard->y + 4, 3, 3,
                       &graphics);
        MC_grpFillRect(screen, screen_x + 10, hazard->y + 4, 3, 3,
                       &graphics);
        MC_grpDrawLine(screen, screen_x + 2, hazard->y + HAZARD_HEIGHT,
                       screen_x - 2, hazard->y + HAZARD_HEIGHT + 3,
                       &graphics);
        MC_grpDrawLine(screen, screen_x + HAZARD_WIDTH - 2,
                       hazard->y + HAZARD_HEIGHT,
                       screen_x + HAZARD_WIDTH + 2,
                       hazard->y + HAZARD_HEIGHT + 3, &graphics);
    }
}

static void draw_portal(void)
{
    M_Int32 screen_x = 1192 - camera_x;
    graphics.fg_pixel = palette.portal;
    MC_grpFillRect(screen, screen_x, 151, 8, 59, &graphics);
    MC_grpDrawArc(screen, screen_x - 18, 141, 44, 34, 0, 180, &graphics);
    graphics.fg_pixel = palette.white;
    MC_grpFillRect(screen, screen_x + 2, 158, 3, 3, &graphics);
}

static void draw_player(void)
{
    M_Int32 screen_x = player_x - camera_x;
    graphics.fg_pixel = palette.player;
    MC_grpFillRect(screen, screen_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT,
                   &graphics);
    graphics.fg_pixel = palette.player_light;
    if (player_facing >= 0) {
        MC_grpFillRect(screen, screen_x + 7, player_y + 4, 5, 5, &graphics);
    } else {
        MC_grpFillRect(screen, screen_x + 2, player_y + 4, 5, 5, &graphics);
    }
    graphics.fg_pixel = palette.ink;
    MC_grpFillRect(screen, screen_x + 2, player_y + PLAYER_HEIGHT - 3,
                   4, 3, &graphics);
    MC_grpFillRect(screen, screen_x + 9, player_y + PLAYER_HEIGHT - 3,
                   4, 3, &graphics);
    MC_grpDrawLine(screen, screen_x + 7, player_y,
                   screen_x + 7, player_y - 4, &graphics);
}

static void draw_hud(void)
{
    M_Char line[48];
    M_Char *cursor;

    graphics.fg_pixel = palette.panel;
    MC_grpFillRect(screen, 0, 0, display.m_width, 27, &graphics);
    draw_text(8, 7, "SKY HOPPER", palette.white);

    cursor = line;
    cursor = append_text(cursor, "ORB ");
    cursor = append_uint(cursor, (M_Uint32)collected_orbs);
    cursor = append_text(cursor, "/");
    cursor = append_uint(cursor, (M_Uint32)ARRAY_COUNT(orbs));
    cursor = append_text(cursor, "  LIFE ");
    cursor = append_uint(cursor, (M_Uint32)lives);
    cursor = append_text(cursor, "  SCORE ");
    (void)append_uint(cursor, (M_Uint32)score);
    draw_text(111, 7, line, palette.white);
}

static void draw_win_panel(void)
{
    M_Int32 panel_x = display.m_width / 2 - 92;
    M_Int32 panel_y = display.m_height / 2 - 34;
    graphics.fg_pixel = palette.panel;
    MC_grpFillRect(screen, panel_x, panel_y, 184, 68, &graphics);
    graphics.fg_pixel = palette.portal;
    MC_grpDrawRect(screen, panel_x, panel_y, 184, 68, &graphics);
    draw_text(panel_x + 40, panel_y + 13, "COURSE CLEAR", palette.white);
    draw_text(panel_x + 30, panel_y + 39, "PRESS OK TO RESTART",
              palette.orb);
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
    font_handle = MC_grpGetFont(0, 10, 0);
    initialize_palette();
}

static void game_timer_callback(MCTimer *fired_timer, void *parameter)
{
    if (fired_timer == &game_timer && parameter == (void *)&timer_cookie) {
        update_game();
        paintClet(0, 0, display.m_width, display.m_height);
    }
    (void)MC_knlSetTimer(&game_timer, (M_Int64)TIMER_PERIOD_MS,
                         (void *)&timer_cookie);
}

void startClet(M_Int32 argc, M_Char *argv[])
{
    (void)argc;
    (void)argv;
    initialize_graphics();
    reset_course();
    MC_knlDefTimer(&game_timer, game_timer_callback);
    timer_defined = 1;
    (void)MC_knlSetTimer(&game_timer, (M_Int64)TIMER_PERIOD_MS,
                         (void *)&timer_cookie);
    paintClet(0, 0, display.m_width, display.m_height);
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
    draw_background();
    draw_platforms();
    draw_orbs();
    draw_hazards();
    draw_portal();
    draw_player();
    draw_hud();
    if (game_state == GAME_WON) {
        draw_win_panel();
    }
    MC_grpFlushLcd(0, screen, 0, 0, display.m_width, display.m_height);
}

void destroyClet(void)
{
    if (timer_defined != 0) {
        MC_knlUnsetTimer(&game_timer);
        timer_defined = 0;
    }
}

void pauseClet(void)
{
    if (timer_defined != 0) {
        MC_knlUnsetTimer(&game_timer);
    }
    moving_left = 0;
    moving_right = 0;
}

void resumeClet(void)
{
    if (timer_defined != 0) {
        (void)MC_knlSetTimer(&game_timer, (M_Int64)TIMER_PERIOD_MS,
                             (void *)&timer_cookie);
    }
    paintClet(0, 0, display.m_width, display.m_height);
}

void handleCletEvent(M_Int32 type, M_Int32 param1, M_Int32 param2)
{
    (void)param2;
    if (type == WIPI_CLET_EVENT_KEY_PRESS) {
        if (param1 == WIPI_CLET_KEY_LEFT || param1 == '4') {
            moving_left = 1;
        } else if (param1 == WIPI_CLET_KEY_RIGHT || param1 == '6') {
            moving_right = 1;
        } else if (param1 == WIPI_CLET_KEY_UP || param1 == '2') {
            start_jump();
        } else if (param1 == WIPI_CLET_KEY_SELECT || param1 == '5') {
            if (game_state == GAME_WON) {
                reset_course();
            } else {
                start_jump();
            }
        }
    } else if (type == WIPI_CLET_EVENT_KEY_RELEASE) {
        if (param1 == WIPI_CLET_KEY_LEFT || param1 == '4') {
            moving_left = 0;
        } else if (param1 == WIPI_CLET_KEY_RIGHT || param1 == '6') {
            moving_right = 0;
        }
    }
}
