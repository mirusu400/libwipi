#ifndef LIBWIPI_PROFILE_H
#define LIBWIPI_PROFILE_H

#if (defined(LIBWIPI_PROFILE_KTF_SAMSUNG) + \
     defined(LIBWIPI_PROFILE_SKT_SAMSUNG_SCH_W830_DL21) + \
     defined(LIBWIPI_PROFILE_LGT_RAPTOR) + \
     defined(LIBWIPI_PROFILE_HOST_SIM)) != 1
#error "select exactly one libwipi profile"
#endif

#if defined(LIBWIPI_PROFILE_KTF_SAMSUNG)
#define LIBWIPI_PROFILE_ID "ktf-samsung"
#define LIBWIPI_DEVICE_POINTER_BITS 32
#elif defined(LIBWIPI_PROFILE_SKT_SAMSUNG_SCH_W830_DL21)
#define LIBWIPI_PROFILE_ID "skt-samsung-sch-w830-dl21"
#define LIBWIPI_DEVICE_POINTER_BITS 32
#elif defined(LIBWIPI_PROFILE_LGT_RAPTOR)
#define LIBWIPI_PROFILE_ID "lgt-raptor"
#define LIBWIPI_DEVICE_POINTER_BITS 32
#else
#define LIBWIPI_PROFILE_ID "host-sim"
#define LIBWIPI_DEVICE_POINTER_BITS (__SIZEOF_POINTER__ * 8)
#endif

#endif /* LIBWIPI_PROFILE_H */
