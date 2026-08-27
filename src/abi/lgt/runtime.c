#include <stddef.h>
#include <stdint.h>
#include <wipi/wipi.h>

#include "input.h"

enum {
    WIPI_LGT_DEPENDENCY_SLOT = 0x214,
    WIPI_LGT_PUBLIC_MODULE = 0x1fb,
    WIPI_LGT_CLET_REGISTER = 0x03
};

typedef M_Addr (*WipiLgtResolveImport)(M_Uint32 module, M_Uint32 method);
typedef void (*WipiLgtRegisterClet)(const void *callbacks,
                                    M_Uint32 annunciator);

typedef struct WipiLgtCletDescriptor {
    M_Uint32 version;
    void (*initialize)(void);
    const M_Char *name;
    M_Addr reserved[3];
    void (*start)(M_Int32 argc, M_Char *argv[]);
    void (*destroy)(void);
    void (*pause)(void);
    void (*resume)(void);
    void (*paint)(M_Int32 x, M_Int32 y, M_Int32 width, M_Int32 height);
    void (*handle_event)(M_Int32 type, M_Int32 param1, M_Int32 param2);
} WipiLgtCletDescriptor;

extern M_Int64 __wipi_missing_import(void);

M_Addr __wipi_lgt_resolver;
M_Uint32 __wipi_lgt_environment;

static void wipi_lgt_initialize(void);
static void wipi_lgt_handle_event(M_Int32 type, M_Int32 param1,
                                  M_Int32 param2);
static const M_Char wipi_lgt_name[] = "libwipi Clet";

WIPI_STATIC_ASSERT(sizeof(WipiLgtCletDescriptor) == 0x30,
                   lgt_clet_descriptor_size);
WIPI_STATIC_ASSERT(offsetof(WipiLgtCletDescriptor, start) == 0x18,
                   lgt_clet_start_offset);
WIPI_STATIC_ASSERT(offsetof(WipiLgtCletDescriptor, handle_event) == 0x2c,
                   lgt_clet_event_offset);

__attribute__((section(".data.wipi_clet"), used, aligned(4)))
const WipiLgtCletDescriptor __wipi_lgt_clet = {
    3u,
    wipi_lgt_initialize,
    wipi_lgt_name,
    {0u, 0u, 0u},
    startClet,
    destroyClet,
    pauseClet,
    resumeClet,
    paintClet,
    wipi_lgt_handle_event,
};

static void wipi_lgt_handle_event(M_Int32 type, M_Int32 param1,
                                  M_Int32 param2)
{
    if (type == WIPI_CLET_EVENT_KEY_PRESS ||
        type == WIPI_CLET_EVENT_KEY_RELEASE) {
        param1 = wipi_lgt_normalize_key(__wipi_lgt_environment, param1);
    }
    handleCletEvent(type, param1, param2);
}

static M_Addr wipi_lgt_resolve(M_Uint32 module, M_Uint32 method)
{
    const volatile M_Addr *resolver_table;
    WipiLgtResolveImport resolver;

    if (__wipi_lgt_resolver == 0u) {
        (void)__wipi_missing_import();
        return 0u;
    }
    resolver_table =
        (const volatile M_Addr *)(uintptr_t)__wipi_lgt_resolver;
    if (resolver_table[1] == 0u) {
        (void)__wipi_missing_import();
        return 0u;
    }
    resolver = (WipiLgtResolveImport)(uintptr_t)resolver_table[1];
    return resolver(module, method);
}

static void wipi_lgt_initialize(void)
{
    M_Addr entry =
        wipi_lgt_resolve(WIPI_LGT_PUBLIC_MODULE, WIPI_LGT_CLET_REGISTER);
    WipiLgtRegisterClet register_clet;

    if (entry == 0u) {
        return;
    }
    register_clet = (WipiLgtRegisterClet)(uintptr_t)entry;
    register_clet((const void *)&__wipi_lgt_clet.start, 0u);
}

__attribute__((section(".text._start"), used))
void _start(volatile M_Addr *output, M_Addr resolver, M_Uint32 reserved)
{
    __wipi_lgt_resolver = resolver;
    __wipi_lgt_environment =
        reserved != 0u ? WIPI_LGT_ENVIRONMENT_ARAM : WIPI_LGT_ENVIRONMENT_WIE;
    if (output != (volatile M_Addr *)0) {
        output[WIPI_LGT_DEPENDENCY_SLOT / sizeof(M_Addr)] =
            (M_Addr)(uintptr_t)&__wipi_lgt_clet;
    }
}
