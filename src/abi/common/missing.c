#include <wipi/runtime.h>

volatile M_Uint32 wipi_missing_import_count;
static WipiMissingImportHandler wipi_missing_import_handler;

void wipi_set_missing_import_handler(WipiMissingImportHandler handler)
{
    wipi_missing_import_handler = handler;
}

M_Int64 __wipi_missing_import(void)
{
    ++wipi_missing_import_count;
    if (wipi_missing_import_handler != (WipiMissingImportHandler)0) {
        wipi_missing_import_handler();
    }
    return (M_Int64)-1;
}
