#ifndef LIBWIPI_ABI_TYPES_H
#define LIBWIPI_ABI_TYPES_H

#include <stddef.h>
#include <time.h>
#include <wipi/constants.h>

#if defined(__GNUC__)
#define WIPI_GUEST_STRUCT __attribute__((packed, aligned(4)))
#else
#define WIPI_GUEST_STRUCT
#endif

typedef struct _MCTimer MCTimer;
typedef void (*TIMERCB)(MCTimer *tm, void *parm);

#if defined(LIBWIPI_PROFILE_LGT_RAPTOR)
struct WIPI_GUEST_STRUCT _MCTimer {
    TIMERCB cb;
};
#else
struct WIPI_GUEST_STRUCT _MCTimer {
    TIMERCB cb;
    void *parm;
    M_Int64 timeout_ms;
    M_Int64 deadline_ms;
    M_Int32 active;
};
#endif

typedef M_Int32 MC_GrpFrameBuffer;
typedef void *MC_GrpImage;
typedef M_Int32 (*MC_GrpPixelOpProc)(M_Int32 srcpxl, M_Int32 orgpxl,
                                     M_Int32 param1);

typedef struct WIPI_GUEST_STRUCT MC_FileInfo {
    M_Int32 attrib;
    M_Uint32 creationTime;
    M_Uint32 size;
} MC_FileInfo;

typedef struct WIPI_GUEST_STRUCT MC_GrpContext {
    M_Int32 clip[4];
#if !defined(LIBWIPI_PROFILE_LGT_RAPTOR)
    M_Int32 clip_enabled;
#endif
    M_Uint32 fg_pixel;
    M_Uint32 bg_pixel;
    M_Int32 alpha;
    MC_GrpPixelOpProc pixel_op;
    M_Int32 pixel_param1;
    M_Int32 font;
    M_Int32 style;
    M_Int32 xor_mode;
    M_Int32 offset[2];
} MC_GrpContext;

typedef struct WIPI_GUEST_STRUCT MC_GrpDisplayInfo {
    M_Int32 m_bpp;
    M_Int32 m_depth;
    M_Int32 m_width;
    M_Int32 m_height;
    M_Int32 m_bpl;
    M_Int32 m_colortype;
    M_Int32 m_redmask;
    M_Int32 m_bluemask;
    M_Int32 m_greenmask;
} MC_GrpDisplayInfo;

typedef struct MC_MdaClip MC_MdaClip;
typedef void (*MEDIACB)(MC_MdaClip *clip, M_Int32 status);

typedef M_Int32 MC_UicComponent;
typedef M_Int32 MC_UicClass;
typedef M_Int32 MC_UicApplicationContext;
typedef void (*MC_UicCallbackProc)(MC_UicComponent component,
                                   void *server_data, M_Int32 client_data);
typedef M_Int32 (*MC_UicEventHandlerProc)(MC_UicComponent component,
                                          M_Int32 type, M_Int32 param1,
                                          M_Int32 param2);

typedef void (*SRLREADCB)(M_Int32 fd, M_Int32 error, void *param);
typedef void (*SRLWRITECB)(M_Int32 fd, M_Int32 error, void *param);
typedef void (*NETCONNECTCB)(M_Int32 error, void *param);
typedef void (*NETSOCKCONNECTCB)(M_Int32 fd, M_Int32 error, void *param);
typedef void (*NETSOCKACCEPTCB)(M_Int32 sd, M_Int32 fd, M_Int32 error,
                                void *param);
typedef void (*NETSOCKREADCB)(M_Int32 fd, M_Int32 error, void *param);
typedef void (*NETSOCKWRITECB)(M_Int32 fd, M_Int32 error, void *param);
typedef void (*NETHOSTADDRCB)(M_Int32 addr, void *param);
typedef void (*NETHTTPCB)(M_Int32 fd, M_Int32 sd, M_Int32 error,
                          void *param);

#if !defined(LIBWIPI_PROFILE_HOST_SIM)
WIPI_STATIC_ASSERT(sizeof(TIMERCB) == 4, timer_callback_is_four_bytes);
WIPI_STATIC_ASSERT(sizeof(MC_FileInfo) == 12, file_info_layout);
WIPI_STATIC_ASSERT(sizeof(MC_GrpDisplayInfo) == 36, display_info_layout);
#if defined(LIBWIPI_PROFILE_KTF_SAMSUNG) || \
    defined(LIBWIPI_PROFILE_SKT_SAMSUNG_SCH_W830_DL21)
WIPI_STATIC_ASSERT(sizeof(MCTimer) == 28, samsung_timer_layout);
WIPI_STATIC_ASSERT(offsetof(MCTimer, timeout_ms) == 8,
                   samsung_timer_timeout_offset);
WIPI_STATIC_ASSERT(sizeof(MC_GrpContext) == 60,
                   samsung_graphics_context_layout);
WIPI_STATIC_ASSERT(offsetof(MC_GrpContext, fg_pixel) == 20,
                   samsung_graphics_fg_offset);
#else
WIPI_STATIC_ASSERT(sizeof(MCTimer) == 4, lgt_timer_layout);
WIPI_STATIC_ASSERT(sizeof(MC_GrpContext) == 56, lgt_graphics_context_layout);
WIPI_STATIC_ASSERT(offsetof(MC_GrpContext, fg_pixel) == 16,
                   lgt_graphics_fg_offset);
#endif
#endif

#undef WIPI_GUEST_STRUCT

#endif /* LIBWIPI_ABI_TYPES_H */
