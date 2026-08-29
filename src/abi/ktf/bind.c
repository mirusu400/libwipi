#include <stdint.h>
#include <wipi/constants.h>
#include <wipi/runtime.h>

#define WIPI_KTF_PROCESS_IMPORT_POINTER ((M_Addr)0x01001000u)
#define WIPI_KTF_MASTER_GETTER_OFFSET 0x84u

M_Addr __wipi_ktf_table_mc_srl;
M_Addr __wipi_ktf_table_mc_grp;
M_Addr __wipi_ktf_table_mc_fs;
M_Addr __wipi_ktf_table_mc_net;
M_Addr __wipi_ktf_table_mc_http;
M_Addr __wipi_ktf_table_mc_util;
M_Addr __wipi_ktf_table_mc_mda;
M_Addr __wipi_ktf_table_mc_misc;
M_Addr __wipi_ktf_table_mc_phn;
M_Addr __wipi_ktf_table_mc_db;
M_Addr __wipi_ktf_table_mc_knl;
M_Addr __wipi_ktf_table_mc_uic;

M_Int32 wipi_ktf_bind_table(WipiKtfFamily family, M_Addr table)
{
    if (table == 0u) {
        return M_E_ERROR;
    }
    switch (family) {
    case WIPI_KTF_FAMILY_SRL:
        __wipi_ktf_table_mc_srl = table;
        break;
    case WIPI_KTF_FAMILY_GRP:
        __wipi_ktf_table_mc_grp = table;
        break;
    case WIPI_KTF_FAMILY_FS:
        __wipi_ktf_table_mc_fs = table;
        break;
    case WIPI_KTF_FAMILY_NET:
        __wipi_ktf_table_mc_net = table;
        break;
    case WIPI_KTF_FAMILY_HTTP:
        __wipi_ktf_table_mc_http = table;
        break;
    case WIPI_KTF_FAMILY_UTIL:
        __wipi_ktf_table_mc_util = table;
        break;
    case WIPI_KTF_FAMILY_MDA:
        __wipi_ktf_table_mc_mda = table;
        break;
    case WIPI_KTF_FAMILY_MISC:
        __wipi_ktf_table_mc_misc = table;
        break;
    case WIPI_KTF_FAMILY_PHN:
        __wipi_ktf_table_mc_phn = table;
        break;
    case WIPI_KTF_FAMILY_DB:
        __wipi_ktf_table_mc_db = table;
        break;
    case WIPI_KTF_FAMILY_KNL:
        __wipi_ktf_table_mc_knl = table;
        break;
    case WIPI_KTF_FAMILY_UIC:
        __wipi_ktf_table_mc_uic = table;
        break;
    default:
        return M_E_ERROR;
    }
    return M_SUCCESS;
}

M_Int32 wipi_ktf_bind_master_vector(const M_Addr *master_vector)
{
    if (master_vector == (const M_Addr *)0 || master_vector[0] == 0u ||
        master_vector[1] == 0u || master_vector[2] == 0u ||
        master_vector[4] == 0u || master_vector[6] == 0u ||
        master_vector[7] == 0u || master_vector[8] == 0u ||
        master_vector[9] == 0u || master_vector[10] == 0u ||
        master_vector[11] == 0u) {
        return M_E_ERROR;
    }
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_UTIL, master_vector[0]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_MISC, master_vector[1]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_GRP, master_vector[2]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_DB, master_vector[4]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_FS, master_vector[6]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_SRL, master_vector[7]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_UIC, master_vector[8]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_MDA, master_vector[9]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_NET, master_vector[10]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_PHN, master_vector[11]);
    return M_SUCCESS;
}

M_Boolean wipi_ktf_imports_bound(void)
{
    return __wipi_ktf_table_mc_knl != 0u &&
           __wipi_ktf_table_mc_util != 0u &&
           __wipi_ktf_table_mc_misc != 0u &&
           __wipi_ktf_table_mc_grp != 0u &&
           __wipi_ktf_table_mc_db != 0u &&
           __wipi_ktf_table_mc_fs != 0u &&
           __wipi_ktf_table_mc_srl != 0u &&
           __wipi_ktf_table_mc_uic != 0u &&
           __wipi_ktf_table_mc_mda != 0u &&
           __wipi_ktf_table_mc_net != 0u &&
           __wipi_ktf_table_mc_phn != 0u ? M_TRUE : M_FALSE;
}

M_Int32 wipi_ktf_bind_kernel_interface(M_Addr kernel_table)
{
    typedef const M_Addr *(*MasterVectorGetter)(void);
    M_Addr getter_address;
    MasterVectorGetter getter;
    const M_Addr *master_vector;

    if (wipi_ktf_bind_table(WIPI_KTF_FAMILY_KNL, kernel_table) != M_SUCCESS) {
        return M_E_ERROR;
    }
    getter_address = *(const volatile M_Addr *)(uintptr_t)
        (kernel_table + WIPI_KTF_MASTER_GETTER_OFFSET);
    if (getter_address == 0u) {
        return M_E_ERROR;
    }
    getter = (MasterVectorGetter)(uintptr_t)getter_address;
    master_vector = getter();
    return wipi_ktf_bind_master_vector(master_vector);
}

M_Int32 wipi_ktf_bind_process_imports(M_Addr import_root)
{
    const volatile M_Addr *fields;
    if (import_root == 0u) {
        return M_E_ERROR;
    }
    fields = (const volatile M_Addr *)(uintptr_t)import_root;
    if (fields[0x00u / 4u] == 0u || fields[0x04u / 4u] == 0u ||
        fields[0x0cu / 4u] == 0u || fields[0x14u / 4u] == 0u ||
        fields[0x18u / 4u] == 0u || fields[0x2cu / 4u] == 0u ||
        fields[0x44u / 4u] == 0u || fields[0x4cu / 4u] == 0u) {
        return M_E_ERROR;
    }
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_KNL, fields[0x00u / 4u]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_GRP, fields[0x04u / 4u]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_FS, fields[0x0cu / 4u]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_NET, fields[0x14u / 4u]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_UTIL, fields[0x18u / 4u]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_HTTP, fields[0x2cu / 4u]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_UIC, fields[0x44u / 4u]);
    wipi_ktf_bind_table(WIPI_KTF_FAMILY_MDA, fields[0x4cu / 4u]);
    return M_SUCCESS;
}

M_Int32 wipi_ktf_bind_default_imports(void)
{
    const volatile M_Addr *process_pointer =
        (const volatile M_Addr *)(uintptr_t)WIPI_KTF_PROCESS_IMPORT_POINTER;
    M_Addr import_root;

    if (wipi_ktf_imports_bound() == M_TRUE) {
        return M_SUCCESS;
    }
    import_root = *process_pointer;

    if (wipi_ktf_bind_process_imports(import_root) != M_SUCCESS ||
        __wipi_ktf_table_mc_knl == 0u) {
        return M_E_ERROR;
    }
    return wipi_ktf_bind_kernel_interface(__wipi_ktf_table_mc_knl);
}
