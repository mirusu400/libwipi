#include <wipi/clet.h>

#include "input.h"

enum {
    WIPI_LGT_WIE_KEY_UP = 141,
    WIPI_LGT_WIE_KEY_LEFT = 142,
    WIPI_LGT_WIE_KEY_RIGHT = 145,
    WIPI_LGT_WIE_KEY_DOWN = 146,
    WIPI_LGT_WIE_KEY_SELECT = 148
};

M_Int32 wipi_lgt_normalize_key(M_Uint32 environment, M_Int32 key)
{
    if (environment != WIPI_LGT_ENVIRONMENT_WIE) {
        return key;
    }
    switch (key) {
    case WIPI_LGT_WIE_KEY_UP:
        return WIPI_CLET_KEY_UP;
    case WIPI_LGT_WIE_KEY_DOWN:
        return WIPI_CLET_KEY_DOWN;
    case WIPI_LGT_WIE_KEY_LEFT:
        return WIPI_CLET_KEY_LEFT;
    case WIPI_LGT_WIE_KEY_RIGHT:
        return WIPI_CLET_KEY_RIGHT;
    case WIPI_LGT_WIE_KEY_SELECT:
        return WIPI_CLET_KEY_SELECT;
    default:
        return key;
    }
}
