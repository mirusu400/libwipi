#ifndef LIBWIPI_ABI_LGT_INPUT_H
#define LIBWIPI_ABI_LGT_INPUT_H

#include <wipi/types.h>

enum {
    WIPI_LGT_ENVIRONMENT_ARAM = 1,
    WIPI_LGT_ENVIRONMENT_WIE = 2
};

M_Int32 wipi_lgt_normalize_key(M_Uint32 environment, M_Int32 key);

#endif /* LIBWIPI_ABI_LGT_INPUT_H */
