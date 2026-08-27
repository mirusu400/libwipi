#ifndef LIBWIPI_CLET_H
#define LIBWIPI_CLET_H

#include <wipi/types.h>

#ifdef __cplusplus
extern "C" {
#endif

void startClet(M_Int32 argc, M_Char *argv[]);
void destroyClet(void);
void paintClet(M_Int32 x, M_Int32 y, M_Int32 width, M_Int32 height);
void pauseClet(void);
void resumeClet(void);
void handleCletEvent(M_Int32 type, M_Int32 param1, M_Int32 param2);

enum {
    WIPI_CLET_EVENT_KEY_PRESS = 502,
    WIPI_CLET_EVENT_KEY_RELEASE = 503
};

/* Stable values delivered to Clet callbacks by libwipi ABI adapters. */
enum {
    WIPI_CLET_KEY_UP = -1,
    WIPI_CLET_KEY_DOWN = -2,
    WIPI_CLET_KEY_LEFT = -3,
    WIPI_CLET_KEY_RIGHT = -4,
    WIPI_CLET_KEY_SELECT = -5
};

/* Older documentation also spells the exported event callback this way. */
#define CletHandleEvent handleCletEvent

#ifdef __cplusplus
}
#endif

#endif /* LIBWIPI_CLET_H */
