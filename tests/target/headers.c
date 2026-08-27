#include <wipi/wipi.h>
#include <wipi/generated/api_counts.h>

static M_Int32 (*const fs_open_probe)(M_Char *, M_Int32, M_Int32) = MC_fsOpen;
static M_Int32 (*const display_probe)(M_Int32, MC_GrpDisplayInfo *) =
    MC_grpGetDisplayInfo;
static M_Int32 (*const timer_probe)(MCTimer *, M_Int64, void *) =
    MC_knlSetTimer;
static MC_UicComponent (*const uic_probe)(MC_UicApplicationContext,
                                          MC_UicClass) = MC_uicCreate;
static void (*const start_clet_probe)(M_Int32, M_Char **) = startClet;
static void (*const paint_clet_probe)(M_Int32, M_Int32, M_Int32, M_Int32) =
    paintClet;

M_Int32 libwipi_header_probe(void)
{
#if !defined(LIBWIPI_API_LEVEL_1_2_1)
#error "header probe did not select WIPI-C 1.2.1"
#endif
    return fs_open_probe != 0 && display_probe != 0 && timer_probe != 0 &&
                   uic_probe != 0 && start_clet_probe != 0 &&
                   paint_clet_probe != 0 && LIBWIPI_PUBLIC_API_COUNT == 239
               ? M_SUCCESS
               : M_E_ERROR;
}
