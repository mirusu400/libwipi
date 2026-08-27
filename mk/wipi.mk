# Central target contract for every libwipi build and example.
CROSS_COMPILE ?= arm-none-eabi-
CC := $(CROSS_COMPILE)gcc
AR := $(CROSS_COMPILE)ar
OBJDUMP := $(CROSS_COMPILE)objdump
NM := $(CROSS_COMPILE)nm
HOST_CC ?= cc

API_LEVEL ?= 1.2.1
PROFILE ?= ktf-samsung
INSTALL_PROFILE ?= none

LIBWIPI_MK_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
LIBWIPI_ROOT ?= $(abspath $(LIBWIPI_MK_DIR)..)
LIBWIPI_ROOT := $(abspath $(LIBWIPI_ROOT))
include $(LIBWIPI_MK_DIR)generated/api-levels.mk

ifeq ($(filter $(API_LEVEL),$(LIBWIPI_KNOWN_API_LEVELS)),)
$(error unknown API_LEVEL '$(API_LEVEL)')
endif
ifeq ($(filter $(API_LEVEL),$(LIBWIPI_IMPLEMENTED_API_LEVELS)),)
$(error API_LEVEL '$(API_LEVEL)' is not implemented)
endif
ifeq ($(filter $(PROFILE),$(LIBWIPI_KNOWN_PROFILES)),)
$(error unknown PROFILE '$(PROFILE)')
endif
ifeq ($(filter $(INSTALL_PROFILE),$(LIBWIPI_KNOWN_INSTALL_PROFILES)),)
$(error unknown INSTALL_PROFILE '$(INSTALL_PROFILE)')
endif
ifeq ($(filter $(API_LEVEL)/$(PROFILE),$(LIBWIPI_AVAILABLE_API_PROFILE_PAIRS)),)
$(error unavailable API/profile pair '$(API_LEVEL)/$(PROFILE)')
endif
ifeq ($(filter $(API_LEVEL)/$(PROFILE)/$(INSTALL_PROFILE),$(LIBWIPI_AVAILABLE_BUILD_TRIPLES)),)
$(error unavailable build triple '$(API_LEVEL)/$(PROFILE)/$(INSTALL_PROFILE)')
endif

WIPI_ARCH_FLAGS := -mcpu=arm7tdmi -mthumb -mlittle-endian \
	-mfloat-abi=soft -mabi=aapcs
WIPI_FREESTANDING_FLAGS := -ffreestanding -fno-builtin -fno-common \
	-fno-stack-protector -fno-unwind-tables -fno-asynchronous-unwind-tables \
	-ffunction-sections -fdata-sections -fno-jump-tables -fno-short-enums
WIPI_WARNING_FLAGS := -Wall -Wextra -Werror -Wshadow -Wundef
WIPI_OPT_FLAGS ?= -Os -g3
WIPI_CFLAGS := $(WIPI_ARCH_FLAGS) $(WIPI_FREESTANDING_FLAGS) \
	$(WIPI_WARNING_FLAGS) $(WIPI_OPT_FLAGS) -std=c11
WIPI_ASFLAGS := $(WIPI_ARCH_FLAGS) $(WIPI_FREESTANDING_FLAGS) -g3
WIPI_CPPFLAGS := -I$(LIBWIPI_ROOT)/include $(WIPI_API_CPPFLAGS) \
	$(WIPI_INSTALL_CPPFLAGS)

ifeq ($(PROFILE),ktf-samsung)
WIPI_PROFILE_CPPFLAGS := -DLIBWIPI_PROFILE_KTF_SAMSUNG=1
endif
ifeq ($(PROFILE),lgt-raptor)
WIPI_PROFILE_CPPFLAGS := -DLIBWIPI_PROFILE_LGT_RAPTOR=1
endif
