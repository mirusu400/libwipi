#ifndef LIBWIPI_CONSTANTS_H
#define LIBWIPI_CONSTANTS_H

#include <wipi/types.h>

#define M_FALSE ((M_Boolean)0)
#define M_TRUE ((M_Boolean)1)
#define M_SUCCESS ((M_Int32)0)
#define M_E_ERROR ((M_Int32)-1)

enum {
    MC_LIGHT_ON = 0,
    MC_LIGHT_OFF = 1,
    MC_LIGHT_ALWAYS_ON = 2,
    MC_LIGHT_DEFAULT = 3
};
typedef M_Int32 MC_BackLight;

#define MC_FILE_OPEN_RDONLY 1
#define MC_FILE_OPEN_WRONLY 2
#define MC_FILE_OPEN_WRTRUNC 4
#define MC_FILE_OPEN_RDWR 8
#define MC_FILE_SEEK_SET 0
#define MC_FILE_SEEK_CUR 1
#define MC_FILE_SEEK_END 2

#define MC_AF_INET 2
#define MC_SOCKET_STREAM 1
#define MC_SOCKET_DGRAM 2

#endif /* LIBWIPI_CONSTANTS_H */
