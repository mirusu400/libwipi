#ifndef LIBWIPI_RUNTIME_H
#define LIBWIPI_RUNTIME_H

#include <wipi/types.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef void (*WipiMissingImportHandler)(void);

extern volatile M_Uint32 wipi_missing_import_count;
void wipi_set_missing_import_handler(WipiMissingImportHandler handler);

#if defined(LIBWIPI_PROFILE_KTF_SAMSUNG)
enum {
    WIPI_KTF_FAMILY_SRL = 0,
    WIPI_KTF_FAMILY_GRP,
    WIPI_KTF_FAMILY_FS,
    WIPI_KTF_FAMILY_NET,
    WIPI_KTF_FAMILY_HTTP,
    WIPI_KTF_FAMILY_UTIL,
    WIPI_KTF_FAMILY_MDA,
    WIPI_KTF_FAMILY_MISC,
    WIPI_KTF_FAMILY_PHN,
    WIPI_KTF_FAMILY_DB,
    WIPI_KTF_FAMILY_KNL,
    WIPI_KTF_FAMILY_UIC,
    WIPI_KTF_FAMILY_COUNT
};
typedef M_Int32 WipiKtfFamily;

M_Int32 wipi_ktf_bind_table(WipiKtfFamily family, M_Addr table);
M_Int32 wipi_ktf_bind_master_vector(const M_Addr *master_vector);
M_Int32 wipi_ktf_bind_process_imports(M_Addr import_root);
M_Int32 wipi_ktf_bind_default_imports(void);
#endif

#ifdef __cplusplus
}
#endif

#endif /* LIBWIPI_RUNTIME_H */
