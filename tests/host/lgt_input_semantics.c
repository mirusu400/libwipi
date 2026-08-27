#include <assert.h>

#include "../../src/abi/lgt/input.h"

int main(void)
{
    assert(wipi_lgt_normalize_key(WIPI_LGT_ENVIRONMENT_ARAM, -3) == -3);
    assert(wipi_lgt_normalize_key(WIPI_LGT_ENVIRONMENT_WIE, 141) == -1);
    assert(wipi_lgt_normalize_key(WIPI_LGT_ENVIRONMENT_WIE, 146) == -2);
    assert(wipi_lgt_normalize_key(WIPI_LGT_ENVIRONMENT_WIE, 142) == -3);
    assert(wipi_lgt_normalize_key(WIPI_LGT_ENVIRONMENT_WIE, 145) == -4);
    assert(wipi_lgt_normalize_key(WIPI_LGT_ENVIRONMENT_WIE, 148) == -5);
    assert(wipi_lgt_normalize_key(WIPI_LGT_ENVIRONMENT_WIE, '4') == '4');
    assert(wipi_lgt_normalize_key(WIPI_LGT_ENVIRONMENT_WIE, 999) == 999);
    return 0;
}
