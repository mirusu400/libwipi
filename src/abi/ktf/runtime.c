#include <stdint.h>
#include <wipi/constants.h>
#include <wipi/runtime.h>
#include <wipi/types.h>

typedef M_Addr (*WipiKtfGetInterface)(const M_Char *name);

extern const M_Addr __wipi_ktf_main_class[];
extern void startClet(M_Int32 argc, M_Char *argv[]);

static const M_Char wipi_ktf_kernel_interface_name[] =
    "WIPIC_knlInterface";
static const M_Char wipi_ktf_main_class_name[] = "LibwipiClet";

static M_Boolean wipi_ktf_string_equal(const M_Char *left,
                                       const M_Char *right)
{
    if (left == (const M_Char *)0 || right == (const M_Char *)0) {
        return M_FALSE;
    }
    while (*left != '\0' && *left == *right) {
        ++left;
        ++right;
    }
    return *left == *right ? M_TRUE : M_FALSE;
}

M_Int32 __wipi_ktf_interface_init(M_Addr parameter0, M_Addr parameter1,
                                  M_Addr parameter2, M_Addr parameter3,
                                  M_Addr parameter4)
{
    const volatile M_Addr *host;
    WipiKtfGetInterface get_interface;
    M_Addr kernel_table;

    (void)parameter0;
    (void)parameter1;
    (void)parameter2;
    (void)parameter3;
    if (parameter4 == 0u) {
        return M_E_ERROR;
    }
    host = (const volatile M_Addr *)(uintptr_t)parameter4;
    if (host[0] == 0u) {
        return M_E_ERROR;
    }
    get_interface = (WipiKtfGetInterface)(uintptr_t)host[0];
    kernel_table = get_interface(wipi_ktf_kernel_interface_name);
    return wipi_ktf_bind_kernel_interface(kernel_table);
}

M_Int32 __wipi_ktf_executable_init(void)
{
    return M_SUCCESS;
}

M_Addr __wipi_ktf_get_class(const M_Char *name)
{
    if (wipi_ktf_string_equal(name, wipi_ktf_main_class_name) != M_TRUE) {
        return 0u;
    }
    return (M_Addr)(uintptr_t)__wipi_ktf_main_class;
}

M_Int32 __wipi_ktf_java_constructor(M_Addr environment, M_Addr instance)
{
    (void)environment;
    (void)instance;
    return M_SUCCESS;
}

M_Int32 __wipi_ktf_java_start_app(M_Addr environment, M_Addr instance,
                                  M_Addr arguments)
{
    (void)environment;
    (void)instance;
    (void)arguments;
    startClet(0, (M_Char **)0);
    return M_SUCCESS;
}
