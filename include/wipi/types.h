#ifndef LIBWIPI_TYPES_H
#define LIBWIPI_TYPES_H

#include <stdint.h>
#include <wipi/profile.h>

typedef int8_t M_Int8;
typedef int16_t M_Int16;
typedef int32_t M_Int32;
typedef int64_t M_Int64;
typedef uint8_t M_Uint8;
typedef uint16_t M_Uint16;
typedef uint32_t M_Uint32;
typedef uint64_t M_Uint64;
typedef uint8_t M_Byte;
typedef uint8_t M_Boolean;
typedef uint16_t M_Ucode;
typedef M_Ucode M_UCode;
typedef char M_Char;
typedef uint32_t M_Addr;
typedef uint32_t M_MemID;

#define WIPI_JOIN_INNER(a, b) a##b
#define WIPI_JOIN(a, b) WIPI_JOIN_INNER(a, b)
#if defined(__STDC_VERSION__) && __STDC_VERSION__ >= 201112L
#define WIPI_STATIC_ASSERT(expr, name) _Static_assert((expr), #name)
#else
#define WIPI_STATIC_ASSERT(expr, name) \
    typedef char WIPI_JOIN(wipi_static_assert_, __LINE__)[(expr) ? 1 : -1]
#endif

WIPI_STATIC_ASSERT(sizeof(M_Int8) == 1, m_int8_is_one_byte);
WIPI_STATIC_ASSERT(sizeof(M_Int16) == 2, m_int16_is_two_bytes);
WIPI_STATIC_ASSERT(sizeof(M_Int32) == 4, m_int32_is_four_bytes);
WIPI_STATIC_ASSERT(sizeof(M_Int64) == 8, m_int64_is_eight_bytes);
WIPI_STATIC_ASSERT(sizeof(M_UCode) == 2, m_ucode_is_two_bytes);
WIPI_STATIC_ASSERT(sizeof(M_Addr) == 4, m_addr_is_four_bytes);

#if !defined(LIBWIPI_PROFILE_HOST_SIM) && \
    !defined(LIBWIPI_ABI_TEST_HOST)
WIPI_STATIC_ASSERT(sizeof(void *) == 4, target_pointer_is_four_bytes);
WIPI_STATIC_ASSERT(sizeof(int) == 4, target_int_is_four_bytes);
WIPI_STATIC_ASSERT(sizeof(long) == 4, target_long_is_four_bytes);
WIPI_STATIC_ASSERT(sizeof(long long) == 8, target_long_long_is_eight_bytes);
WIPI_STATIC_ASSERT(sizeof(double) == 8, target_double_is_eight_bytes);
#if !defined(__BYTE_ORDER__) || !defined(__ORDER_LITTLE_ENDIAN__) || \
    __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "libwipi target profiles require little-endian code generation"
#endif
#endif

#endif /* LIBWIPI_TYPES_H */
