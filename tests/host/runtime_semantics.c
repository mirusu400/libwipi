#include <wipi/memory.h>
#include <wipi/runtime.h>

#define CHECK(expression)     \
    do {                      \
        if (!(expression)) {  \
            return __LINE__;  \
        }                     \
    } while (0)

static M_Uint32 handler_calls;
static M_MemID resolved_memory_id;

static void missing_handler(void)
{
    ++handler_calls;
}

void *wipi_host_resolve_memid(M_MemID memory_id)
{
    resolved_memory_id = memory_id;
    return (void *)(uintptr_t)0x1234u;
}

extern M_Int64 __wipi_missing_import(void);

int main(void)
{
    CHECK(wipi_missing_import_count == 0u);
    wipi_set_missing_import_handler(missing_handler);
    CHECK(__wipi_missing_import() == (M_Int64)-1);
    CHECK(wipi_missing_import_count == 1u);
    CHECK(handler_calls == 1u);

    wipi_set_missing_import_handler((WipiMissingImportHandler)0);
    CHECK(__wipi_missing_import() == (M_Int64)-1);
    CHECK(wipi_missing_import_count == 2u);
    CHECK(handler_calls == 1u);

    CHECK(MC_GETDPTR(0u) == (void *)0);
    CHECK(resolved_memory_id == 0u);
    CHECK(MC_GETDPTR((M_MemID)0x55u) == (void *)(uintptr_t)0x1234u);
    CHECK(resolved_memory_id == (M_MemID)0x55u);
    return 0;
}
