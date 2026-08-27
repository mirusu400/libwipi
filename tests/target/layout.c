#include <stddef.h>
#include <wipi/wipi.h>

WIPI_STATIC_ASSERT(sizeof(M_Addr) == 4, address_width);
WIPI_STATIC_ASSERT(sizeof(MC_BackLight) == 4, backlight_width);
WIPI_STATIC_ASSERT(sizeof(MC_FileInfo) == 12, file_info_size);
WIPI_STATIC_ASSERT(offsetof(MC_FileInfo, size) == 8, file_info_size_offset);
WIPI_STATIC_ASSERT(sizeof(MC_GrpDisplayInfo) == 36, display_info_size);

#if defined(LIBWIPI_PROFILE_KTF_SAMSUNG)
WIPI_STATIC_ASSERT(sizeof(MCTimer) == 28, ktf_timer_size);
WIPI_STATIC_ASSERT(offsetof(MCTimer, parm) == 4, ktf_timer_parm_offset);
WIPI_STATIC_ASSERT(offsetof(MCTimer, deadline_ms) == 16,
                   ktf_timer_deadline_offset);
WIPI_STATIC_ASSERT(offsetof(MCTimer, active) == 24,
                   ktf_timer_active_offset);
WIPI_STATIC_ASSERT(sizeof(MC_GrpContext) == 60, ktf_context_size);
WIPI_STATIC_ASSERT(offsetof(MC_GrpContext, pixel_op) == 32,
                   ktf_context_pixel_op_offset);
WIPI_STATIC_ASSERT(offsetof(MC_GrpContext, offset) == 52,
                   ktf_context_offset_offset);
#elif defined(LIBWIPI_PROFILE_LGT_RAPTOR)
WIPI_STATIC_ASSERT(sizeof(MCTimer) == 4, lgt_timer_size);
WIPI_STATIC_ASSERT(sizeof(MC_GrpContext) == 56, lgt_context_size);
WIPI_STATIC_ASSERT(offsetof(MC_GrpContext, pixel_op) == 28,
                   lgt_context_pixel_op_offset);
WIPI_STATIC_ASSERT(offsetof(MC_GrpContext, offset) == 48,
                   lgt_context_offset_offset);
#endif
