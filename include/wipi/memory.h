#ifndef LIBWIPI_MEMORY_H
#define LIBWIPI_MEMORY_H

#include <stdint.h>
#include <wipi/types.h>

#if defined(LIBWIPI_PROFILE_HOST_SIM)
void *wipi_host_resolve_memid(M_MemID memory_id);
#elif defined(LIBWIPI_PROFILE_LGT_RAPTOR)
#if !defined(LIBWIPI_INSTALL_ARAM_WIE_RAPTOR) && \
    !defined(LIBWIPI_INSTALL_ARAM_RAPTOR)
/* Deliberately undefined until a non-emulator LGT memory model is proven. */
void *wipi_lgt_resolve_memid(M_MemID memory_id);
#endif
#endif

static inline void *wipi_resolve_memid(M_MemID memory_id)
{
    if (memory_id == 0u) {
        return (void *)0;
    }
#if defined(LIBWIPI_PROFILE_KTF_SAMSUNG)
    {
        volatile const M_Addr *handle =
            (volatile const M_Addr *)(uintptr_t)memory_id;
        M_Addr indirect_head = handle[0];
        if (indirect_head == 0u) {
            return (void *)0;
        }
        return (void *)(uintptr_t)(indirect_head + 8u);
    }
#elif defined(LIBWIPI_PROFILE_LGT_RAPTOR)
#if defined(LIBWIPI_INSTALL_ARAM_WIE_RAPTOR) || \
    defined(LIBWIPI_INSTALL_ARAM_RAPTOR)
    /* Confirmed only for the selected pinned emulator install profile. */
    return (void *)(uintptr_t)memory_id;
#else
    return wipi_lgt_resolve_memid(memory_id);
#endif
#else
    return wipi_host_resolve_memid(memory_id);
#endif
}

#define MC_GETDPTR(memory_id) wipi_resolve_memid((M_MemID)(memory_id))

#endif /* LIBWIPI_MEMORY_H */
