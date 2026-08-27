# Reusable native WIPI-C application build for the implemented Raptor target.

LIBWIPI_APPLICATION_MK_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
LIBWIPI_ROOT ?= $(abspath $(LIBWIPI_APPLICATION_MK_DIR)..)

API_LEVEL ?= 1.2.1
PROFILE ?= lgt-raptor
INSTALL_PROFILE ?= aram-wie-raptor

include $(LIBWIPI_ROOT)/mk/wipi.mk

ifeq ($(strip $(APP_AID)),)
$(error APP_AID is required before including mk/application.mk)
endif
APP_NAME ?= $(APP_AID)
APP_SOURCES ?= main.c
APP_RESOURCES ?=
PYTHON ?= python3

ifeq ($(filter $(API_LEVEL)/$(PROFILE)/$(INSTALL_PROFILE),1.2.1/lgt-raptor/aram-raptor 1.2.1/lgt-raptor/aram-wie-raptor),)
$(error mk/application.mk requires an implemented 1.2.1/lgt-raptor emulator install profile)
endif

APP_BUILD_DIR := build/wipi-$(API_LEVEL)/$(PROFILE)/$(INSTALL_PROFILE)
APP_OBJECTS := $(addprefix $(APP_BUILD_DIR)/,$(APP_SOURCES:.c=.o))
APP_RESOURCE_FILES := $(foreach resource,$(APP_RESOURCES),\
	$(firstword $(subst =, ,$(resource))))
APP_RESOURCE_ARGS := $(foreach resource,$(APP_RESOURCES),\
	--resource $(resource))
APP_METADATA_OBJECT := $(APP_BUILD_DIR)/libwipi/raptor_metadata.o
APP_ELF := $(APP_BUILD_DIR)/binary.mod
APP_PACKAGE := $(APP_BUILD_DIR)/$(APP_AID).zip
LIBWIPI_LIBRARY := $(LIBWIPI_ROOT)/build/wipi-$(API_LEVEL)/$(PROFILE)/$(INSTALL_PROFILE)/lib/libwipi.a

.PHONY: all package inspect clean FORCE

all: package
package: $(APP_PACKAGE)

$(APP_BUILD_DIR)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(WIPI_CPPFLAGS) $(WIPI_PROFILE_CPPFLAGS) $(WIPI_CFLAGS) \
		$(CPPFLAGS) $(CFLAGS) -c $< -o $@

$(APP_METADATA_OBJECT): $(LIBWIPI_ROOT)/src/container/raptor_metadata.S
	@mkdir -p $(dir $@)
	$(CC) $(WIPI_CPPFLAGS) $(WIPI_PROFILE_CPPFLAGS) $(WIPI_ASFLAGS) \
		$(CPPFLAGS) $(ASFLAGS) -c $< -o $@

FORCE:

$(LIBWIPI_LIBRARY): FORCE
	$(MAKE) --no-print-directory -C $(LIBWIPI_ROOT) API_LEVEL=$(API_LEVEL) \
		PROFILE=$(PROFILE) INSTALL_PROFILE=$(INSTALL_PROFILE) \
		CROSS_COMPILE=$(CROSS_COMPILE) library

$(APP_ELF): $(APP_OBJECTS) $(APP_METADATA_OBJECT) $(LIBWIPI_LIBRARY) \
		$(LIBWIPI_ROOT)/ld/raptor.ld
	$(CC) $(WIPI_ARCH_FLAGS) -nostdlib -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,--strip-debug -Wl,-u,_start \
		-T $(LIBWIPI_ROOT)/ld/raptor.ld -o $@ $(APP_OBJECTS) \
		$(APP_METADATA_OBJECT) $(LIBWIPI_LIBRARY) -lgcc $(APP_LDFLAGS)

$(APP_PACKAGE): $(APP_ELF) $(APP_RESOURCE_FILES) \
		$(LIBWIPI_ROOT)/tools/package_raptor.py
	$(PYTHON) $(LIBWIPI_ROOT)/tools/package_raptor.py --binary $(APP_ELF) \
		--output $@ --aid $(APP_AID) --name "$(APP_NAME)" \
		$(APP_RESOURCE_ARGS)

inspect: $(APP_PACKAGE)
	$(PYTHON) $(LIBWIPI_ROOT)/tools/package_raptor.py --inspect $(APP_PACKAGE)

clean:
	$(RM) $(APP_OBJECTS) $(APP_METADATA_OBJECT) $(APP_ELF) $(APP_PACKAGE)
