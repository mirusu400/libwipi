#include <wipi/constants.h>
#include <wipi/runtime.h>

extern M_Addr __wipi_ktf_table_mc_srl;
extern M_Addr __wipi_ktf_table_mc_grp;
extern M_Addr __wipi_ktf_table_mc_fs;
extern M_Addr __wipi_ktf_table_mc_net;
extern M_Addr __wipi_ktf_table_mc_util;
extern M_Addr __wipi_ktf_table_mc_mda;
extern M_Addr __wipi_ktf_table_mc_misc;
extern M_Addr __wipi_ktf_table_mc_phn;
extern M_Addr __wipi_ktf_table_mc_db;
extern M_Addr __wipi_ktf_table_mc_knl;
extern M_Addr __wipi_ktf_table_mc_uic;

#define CHECK(expression)     \
    do {                      \
        if (!(expression)) {  \
            return __LINE__;  \
        }                     \
    } while (0)

static void fill_master_vector(M_Addr *master)
{
    master[0] = 0x1000u;
    master[1] = 0x2000u;
    master[2] = 0x3000u;
    master[4] = 0x4000u;
    master[6] = 0x5000u;
    master[7] = 0x6000u;
    master[8] = 0x7000u;
    master[9] = 0x8000u;
    master[10] = 0x9000u;
    master[11] = 0xa000u;
}

int main(void)
{
    M_Addr master[17] = {0};

    CHECK(wipi_ktf_imports_bound() == M_FALSE);
    __wipi_ktf_table_mc_knl = 0x1111u;
    CHECK(wipi_ktf_bind_table(WIPI_KTF_FAMILY_KNL, 0u) == M_E_ERROR);
    CHECK(__wipi_ktf_table_mc_knl == 0x1111u);
    CHECK(wipi_ktf_bind_table(WIPI_KTF_FAMILY_COUNT, 0x2222u) == M_E_ERROR);

    fill_master_vector(master);
    CHECK(wipi_ktf_bind_master_vector(master) == M_SUCCESS);
    CHECK(__wipi_ktf_table_mc_util == 0x1000u);
    CHECK(__wipi_ktf_table_mc_misc == 0x2000u);
    CHECK(__wipi_ktf_table_mc_grp == 0x3000u);
    CHECK(__wipi_ktf_table_mc_db == 0x4000u);
    CHECK(__wipi_ktf_table_mc_fs == 0x5000u);
    CHECK(__wipi_ktf_table_mc_srl == 0x6000u);
    CHECK(__wipi_ktf_table_mc_uic == 0x7000u);
    CHECK(__wipi_ktf_table_mc_mda == 0x8000u);
    CHECK(__wipi_ktf_table_mc_net == 0x9000u);
    CHECK(__wipi_ktf_table_mc_phn == 0xa000u);
    CHECK(wipi_ktf_imports_bound() == M_TRUE);

    __wipi_ktf_table_mc_util = 0xabcdu;
    master[10] = 0u;
    CHECK(wipi_ktf_bind_master_vector(master) == M_E_ERROR);
    CHECK(__wipi_ktf_table_mc_util == 0xabcdu);
    CHECK(wipi_ktf_bind_master_vector((const M_Addr *)0) == M_E_ERROR);

    return 0;
}
