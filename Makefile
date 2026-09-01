include mk/wipi.mk

ifeq ($(PROFILE),ktf-samsung)
ABI_C_SOURCES := src/abi/ktf/bind.c src/abi/ktf/runtime.c
ABI_ASM_SOURCES := src/abi/ktf/generated_veneer.S
else ifeq ($(PROFILE),skt-samsung-sch-w830-dl21)
ABI_C_SOURCES :=
ABI_ASM_SOURCES := src/abi/skt/generated_veneer.S
else ifeq ($(PROFILE),lgt-raptor)
ABI_C_SOURCES := src/abi/lgt/runtime.c src/abi/lgt/input.c
ifeq ($(INSTALL_PROFILE),aram-raptor)
ABI_ASM_SOURCES := src/abi/lgt/generated_veneer_aram_raptor.S
else
ABI_ASM_SOURCES := src/abi/lgt/generated_veneer.S
endif
else
ABI_C_SOURCES :=
ABI_ASM_SOURCES :=
endif

COMMON_C_SOURCES := \
	src/abi/common/missing.c \
	src/cstdlib/string.c \
	src/cstdlib/stdlib.c \
	src/cstdlib/time.c
LIB_SOURCES := $(COMMON_C_SOURCES) $(ABI_C_SOURCES) $(ABI_ASM_SOURCES)
BUILD_DIR := build/wipi-$(API_LEVEL)/$(PROFILE)/$(INSTALL_PROFILE)
LIB_OBJECTS := $(addprefix $(BUILD_DIR)/,$(LIB_SOURCES:.c=.o))
LIB_OBJECTS := $(LIB_OBJECTS:.S=.o)
LIBRARY := $(BUILD_DIR)/lib/libwipi.a
EXAMPLE_OBJECT := $(BUILD_DIR)/examples/hello/main.o
EXAMPLE_RELOC := $(BUILD_DIR)/examples/hello/hello.rel
EXAMPLE_ELF := $(BUILD_DIR)/examples/hello/binary.mod
EXAMPLE_CLIENT := $(BUILD_DIR)/examples/hello/client.bin
EXAMPLE_PACKAGE := $(BUILD_DIR)/examples/hello/libwipi-hello.zip
CONFORMANCE_OBJECT := $(BUILD_DIR)/examples/conformance/main.o
CONFORMANCE_ELF := $(BUILD_DIR)/examples/conformance/binary.mod
CONFORMANCE_CLIENT := $(BUILD_DIR)/examples/conformance/client.bin
CONFORMANCE_PACKAGE := $(BUILD_DIR)/examples/conformance/libwipi-conformance.zip
RAPTOR_METADATA_OBJECT := $(BUILD_DIR)/src/container/raptor_metadata.o
KTF_METADATA_OBJECT := $(BUILD_DIR)/src/container/ktf_metadata.o
ifeq ($(PROFILE),ktf-samsung)
VENEER_OBJECT := $(BUILD_DIR)/src/abi/ktf/generated_veneer.o
else ifeq ($(PROFILE),skt-samsung-sch-w830-dl21)
VENEER_OBJECT := $(BUILD_DIR)/src/abi/skt/generated_veneer.o
else ifeq ($(PROFILE),lgt-raptor)
ifeq ($(INSTALL_PROFILE),aram-raptor)
VENEER_OBJECT := $(BUILD_DIR)/src/abi/lgt/generated_veneer_aram_raptor.o
else
VENEER_OBJECT := $(BUILD_DIR)/src/abi/lgt/generated_veneer.o
endif
endif
VENEER_DISASSEMBLY := $(BUILD_DIR)/tests/generated_veneer.dis
HOST_SEMANTICS_TEST := build/host/tests/cstdlib-semantics
HOST_KTF_BIND_TEST := build/host/tests/ktf-bind-semantics
HOST_RUNTIME_TEST := build/host/tests/runtime-semantics
HOST_LGT_INPUT_TEST := build/host/tests/lgt-input-semantics

.PHONY: all clean library example conformance generate check-generated test test-host test-semantics \
	test-target test-target-profile test-target-ktf test-target-skt test-target-lgt \
	test-application-template test-platformer-example platformer \
	sdk-examples test-sdk-examples aram-sdk-examples test-aram-sdk-examples \
	ktf-examples test-ktf-examples test-sch-w8300-qpst-probe \
	docs docs-check docs-linkcheck docs-packages release-bundles

SDK_VERSION ?= dev

all: $(LIBRARY) example

generate:
	python3 tools/generate.py
	python3 tools/generate_docs.py

check-generated:
	python3 tools/generate.py --check
	python3 tools/generate_docs.py --check

docs:
	python3 tools/build_docs.py

docs-check: check-generated
	python3 tools/build_docs.py --jobs auto

docs-linkcheck: check-generated
	python3 tools/build_docs.py --builder linkcheck --jobs 1

docs-packages:
	python3 tools/update_docs_packages.py

release-bundles:
	python3 tools/build_release_bundles.py --version $(SDK_VERSION)

$(BUILD_DIR)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(WIPI_CPPFLAGS) $(WIPI_PROFILE_CPPFLAGS) $(WIPI_CFLAGS) \
		$(CPPFLAGS) $(CFLAGS) -c $< -o $@

$(BUILD_DIR)/%.o: %.S
	@mkdir -p $(dir $@)
	$(CC) $(WIPI_CPPFLAGS) $(WIPI_PROFILE_CPPFLAGS) $(WIPI_ASFLAGS) \
		$(CPPFLAGS) $(ASFLAGS) -c $< -o $@

$(LIBRARY): $(LIB_OBJECTS)
	@mkdir -p $(dir $@)
	$(AR) rcsD $@ $^

library: $(LIBRARY)

$(EXAMPLE_RELOC): $(EXAMPLE_OBJECT) $(LIBRARY)
	$(CC) $(WIPI_ARCH_FLAGS) -nostdlib -Wl,-r -o $@ \
		$(EXAMPLE_OBJECT) $(LIBRARY)

ifneq ($(filter $(INSTALL_PROFILE),aram-ktf sch-w8300-qpst-probe),)
$(EXAMPLE_ELF): $(EXAMPLE_OBJECT) $(KTF_METADATA_OBJECT) $(LIBRARY) ld/ktf.ld
	$(CC) $(WIPI_ARCH_FLAGS) -nostdlib -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,--strip-debug -Wl,-u,_start \
		-T ld/ktf.ld -o $@ $(EXAMPLE_OBJECT) $(KTF_METADATA_OBJECT) \
		$(LIBRARY) -lgcc

$(EXAMPLE_CLIENT): $(EXAMPLE_ELF)
	$(OBJCOPY) -O binary $< $@

$(EXAMPLE_PACKAGE): $(EXAMPLE_ELF) $(EXAMPLE_CLIENT) tools/package_ktf.py
	python3 tools/package_ktf.py --client $(EXAMPLE_CLIENT) \
		--elf $(EXAMPLE_ELF) --nm $(NM) --output $@ \
		--aid libwipi-hello --name "libwipi hello"

example: $(EXAMPLE_PACKAGE)

$(CONFORMANCE_ELF): $(CONFORMANCE_OBJECT) $(KTF_METADATA_OBJECT) \
		$(LIBRARY) ld/ktf.ld
	$(CC) $(WIPI_ARCH_FLAGS) -nostdlib -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,--strip-debug -Wl,-u,_start \
		-T ld/ktf.ld -o $@ $(CONFORMANCE_OBJECT) \
		$(KTF_METADATA_OBJECT) $(LIBRARY) -lgcc

$(CONFORMANCE_CLIENT): $(CONFORMANCE_ELF)
	$(OBJCOPY) -O binary $< $@

$(CONFORMANCE_PACKAGE): $(CONFORMANCE_ELF) $(CONFORMANCE_CLIENT) \
		tools/package_ktf.py
	python3 tools/package_ktf.py --client $(CONFORMANCE_CLIENT) \
		--elf $(CONFORMANCE_ELF) --nm $(NM) --output $@ \
		--aid libwipi-conformance --name "libwipi conformance"

ifeq ($(INSTALL_PROFILE),aram-ktf)
conformance: $(CONFORMANCE_PACKAGE)
all: conformance
else
conformance:
	@echo "conformance is unavailable for the minimal SCH-W8300 QPST probe"
	@false
endif
else ifneq ($(filter $(INSTALL_PROFILE),aram-raptor aram-wie-raptor),)
$(EXAMPLE_ELF): $(EXAMPLE_OBJECT) $(RAPTOR_METADATA_OBJECT) $(LIBRARY) ld/raptor.ld
	$(CC) $(WIPI_ARCH_FLAGS) -nostdlib -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-u,_start -T ld/raptor.ld -o $@ \
		$(EXAMPLE_OBJECT) $(RAPTOR_METADATA_OBJECT) $(LIBRARY) -lgcc

$(EXAMPLE_PACKAGE): $(EXAMPLE_ELF) tools/package_raptor.py
	python3 tools/package_raptor.py --binary $(EXAMPLE_ELF) \
		--output $@ --aid libwipi-hello --name "libwipi hello"

example: $(EXAMPLE_PACKAGE)

$(CONFORMANCE_ELF): $(CONFORMANCE_OBJECT) $(RAPTOR_METADATA_OBJECT) \
		$(LIBRARY) ld/raptor.ld
	$(CC) $(WIPI_ARCH_FLAGS) -nostdlib -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,--strip-debug -Wl,-u,_start \
		-T ld/raptor.ld -o $@ $(CONFORMANCE_OBJECT) \
		$(RAPTOR_METADATA_OBJECT) $(LIBRARY) -lgcc

$(CONFORMANCE_PACKAGE): $(CONFORMANCE_ELF) tools/package_raptor.py
	python3 tools/package_raptor.py --binary $(CONFORMANCE_ELF) \
		--output $@ --aid libwipi-conformance \
		--name "libwipi conformance"

conformance: $(CONFORMANCE_PACKAGE)
all: conformance
else
example: $(EXAMPLE_RELOC)

conformance:
	@echo "conformance package requires a Raptor emulator install profile"
	@false
endif

test-host: check-generated
	python3 -m unittest discover -s tests -p "test_*.py"

$(BUILD_DIR)/tests/layout-ktf.o: tests/target/layout.c
	@mkdir -p $(dir $@)
	$(CC) $(WIPI_CPPFLAGS) -DLIBWIPI_PROFILE_KTF_SAMSUNG=1 \
		$(WIPI_CFLAGS) -c $< -o $@

$(BUILD_DIR)/tests/layout-lgt.o: tests/target/layout.c
	@mkdir -p $(dir $@)
	$(CC) $(WIPI_CPPFLAGS) -DLIBWIPI_PROFILE_LGT_RAPTOR=1 \
		$(WIPI_CFLAGS) -c $< -o $@

$(BUILD_DIR)/tests/layout-skt.o: tests/target/layout.c
	@mkdir -p $(dir $@)
	$(CC) $(WIPI_CPPFLAGS) \
		-DLIBWIPI_PROFILE_SKT_SAMSUNG_SCH_W830_DL21=1 \
		$(WIPI_CFLAGS) -c $< -o $@

$(BUILD_DIR)/tests/headers.o: tests/target/headers.c
	@mkdir -p $(dir $@)
	$(CC) $(WIPI_CPPFLAGS) $(WIPI_PROFILE_CPPFLAGS) $(WIPI_CFLAGS) \
		-c $< -o $@

$(VENEER_DISASSEMBLY): $(VENEER_OBJECT)
	@mkdir -p $(dir $@)
	$(OBJDUMP) -dr $< > $@

$(HOST_SEMANTICS_TEST): tests/host/cstdlib_semantics.c \
		src/cstdlib/string.c src/cstdlib/stdlib.c src/cstdlib/time.c
	@mkdir -p $(dir $@)
	$(HOST_CC) $(WIPI_CPPFLAGS) -DLIBWIPI_PROFILE_HOST_SIM=1 -std=c11 \
		-Wall -Wextra -Werror -Wshadow -Wundef -fno-builtin $^ -o $@

$(HOST_KTF_BIND_TEST): tests/host/ktf_bind_semantics.c src/abi/ktf/bind.c
	@mkdir -p $(dir $@)
	$(HOST_CC) $(WIPI_CPPFLAGS) -DLIBWIPI_PROFILE_KTF_SAMSUNG=1 \
		-DLIBWIPI_ABI_TEST_HOST=1 -std=c11 \
		-Wall -Wextra -Werror -Wshadow -Wundef -fno-builtin $^ -o $@

$(HOST_RUNTIME_TEST): tests/host/runtime_semantics.c src/abi/common/missing.c
	@mkdir -p $(dir $@)
	$(HOST_CC) $(WIPI_CPPFLAGS) -DLIBWIPI_PROFILE_HOST_SIM=1 -std=c11 \
		-Wall -Wextra -Werror -Wshadow -Wundef -fno-builtin $^ -o $@

$(HOST_LGT_INPUT_TEST): tests/host/lgt_input_semantics.c src/abi/lgt/input.c
	@mkdir -p $(dir $@)
	$(HOST_CC) $(WIPI_CPPFLAGS) -DLIBWIPI_PROFILE_HOST_SIM=1 -std=c11 \
		-Wall -Wextra -Werror -Wshadow -Wundef -fno-builtin $^ -o $@

test-semantics: $(HOST_SEMANTICS_TEST) $(HOST_KTF_BIND_TEST) \
	$(HOST_RUNTIME_TEST) $(HOST_LGT_INPUT_TEST)
	$(HOST_SEMANTICS_TEST)
	$(HOST_KTF_BIND_TEST)
	$(HOST_RUNTIME_TEST)
	$(HOST_LGT_INPUT_TEST)

ifeq ($(PROFILE),ktf-samsung)
ifeq ($(INSTALL_PROFILE),aram-ktf)
test-target-profile: $(LIBRARY) $(BUILD_DIR)/tests/layout-ktf.o \
	$(BUILD_DIR)/tests/layout-lgt.o $(BUILD_DIR)/tests/headers.o \
	$(VENEER_DISASSEMBLY) $(EXAMPLE_ELF) $(EXAMPLE_CLIENT) \
	$(EXAMPLE_PACKAGE) $(CONFORMANCE_ELF) $(CONFORMANCE_CLIENT) \
	$(CONFORMANCE_PACKAGE) test-semantics
	python3 tests/check_disassembly.py $(VENEER_DISASSEMBLY)
	python3 tests/check_archive.py $(LIBRARY) $(NM) ktf-samsung aram-ktf
	python3 tests/check_ktf_image.py $(EXAMPLE_ELF) $(EXAMPLE_CLIENT) \
		$(OBJDUMP) $(NM)
	python3 tests/check_ktf_image.py $(CONFORMANCE_ELF) \
		$(CONFORMANCE_CLIENT) $(OBJDUMP) $(NM)
	python3 tools/package_ktf.py --inspect $(EXAMPLE_PACKAGE)
	python3 tools/package_ktf.py --inspect $(CONFORMANCE_PACKAGE)
else
test-target-profile: $(LIBRARY) $(BUILD_DIR)/tests/layout-ktf.o \
	$(BUILD_DIR)/tests/layout-lgt.o $(BUILD_DIR)/tests/headers.o \
	$(VENEER_DISASSEMBLY) $(EXAMPLE_RELOC) test-semantics
	python3 tests/check_disassembly.py $(VENEER_DISASSEMBLY)
	python3 tests/check_archive.py $(LIBRARY) $(NM) ktf-samsung
	python3 tests/check_reloc.py $(EXAMPLE_RELOC) $(NM)
	python3 tests/check_build_config.py
endif
else ifeq ($(PROFILE),skt-samsung-sch-w830-dl21)
test-target-profile: $(LIBRARY) $(BUILD_DIR)/tests/layout-ktf.o \
	$(BUILD_DIR)/tests/layout-skt.o $(BUILD_DIR)/tests/layout-lgt.o \
	$(BUILD_DIR)/tests/headers.o $(VENEER_DISASSEMBLY) $(EXAMPLE_RELOC) \
	test-semantics
	python3 tests/check_skt_disassembly.py $(VENEER_DISASSEMBLY)
	python3 tests/check_archive.py $(LIBRARY) $(NM) \
		skt-samsung-sch-w830-dl21 none
	python3 tests/check_reloc.py $(EXAMPLE_RELOC) $(NM)
	python3 tests/check_build_config.py
else ifeq ($(PROFILE),lgt-raptor)
test-target-profile: $(LIBRARY) $(BUILD_DIR)/tests/layout-ktf.o \
	$(BUILD_DIR)/tests/layout-lgt.o $(BUILD_DIR)/tests/headers.o \
	$(VENEER_DISASSEMBLY) $(EXAMPLE_ELF) $(EXAMPLE_PACKAGE) \
	$(CONFORMANCE_ELF) $(CONFORMANCE_PACKAGE)
	python3 tests/check_lgt_disassembly.py $(VENEER_DISASSEMBLY) $(INSTALL_PROFILE)
	python3 tests/check_archive.py $(LIBRARY) $(NM) lgt-raptor $(INSTALL_PROFILE)
	python3 tests/check_raptor_elf.py $(EXAMPLE_ELF) $(OBJDUMP)
	python3 tests/check_raptor_elf.py $(CONFORMANCE_ELF) $(OBJDUMP)
	python3 tools/package_raptor.py --inspect $(EXAMPLE_PACKAGE)
	python3 tools/package_raptor.py --inspect $(CONFORMANCE_PACKAGE)
endif

test-target-ktf:
	$(MAKE) --no-print-directory API_LEVEL=1.2.1 PROFILE=ktf-samsung \
		INSTALL_PROFILE=none test-target-profile
	$(MAKE) --no-print-directory API_LEVEL=1.2.1 PROFILE=ktf-samsung \
		INSTALL_PROFILE=aram-ktf test-target-profile
	$(MAKE) --no-print-directory test-sch-w8300-qpst-probe

test-target-skt:
	$(MAKE) --no-print-directory API_LEVEL=1.2.1 \
		PROFILE=skt-samsung-sch-w830-dl21 INSTALL_PROFILE=none \
		test-target-profile

test-sch-w8300-qpst-probe:
	$(MAKE) --no-print-directory API_LEVEL=1.2.1 PROFILE=ktf-samsung \
		INSTALL_PROFILE=sch-w8300-qpst-probe test-target-profile
	$(MAKE) --no-print-directory -C examples/handset-probe package inspect
	python3 tests/check_ktf_image.py \
		examples/handset-probe/build/wipi-1.2.1/ktf-samsung/sch-w8300-qpst-probe/client.elf \
		examples/handset-probe/build/wipi-1.2.1/ktf-samsung/sch-w8300-qpst-probe/client.bin \
		$(OBJDUMP) $(NM)
	python3 tests/check_handset_probe.py \
		examples/handset-probe/build/wipi-1.2.1/ktf-samsung/sch-w8300-qpst-probe/main.o \
		examples/handset-probe/build/wipi-1.2.1/ktf-samsung/sch-w8300-qpst-probe/client.elf \
		$(NM)

test-target-lgt:
	$(MAKE) --no-print-directory API_LEVEL=1.2.1 PROFILE=lgt-raptor \
		INSTALL_PROFILE=aram-wie-raptor test-target-profile
	$(MAKE) --no-print-directory API_LEVEL=1.2.1 PROFILE=lgt-raptor \
		INSTALL_PROFILE=aram-raptor test-target-profile
	$(MAKE) --no-print-directory test-application-template
	$(MAKE) --no-print-directory test-platformer-example
	$(MAKE) --no-print-directory test-sdk-examples
	$(MAKE) --no-print-directory test-aram-sdk-examples

test-application-template:
	$(MAKE) --no-print-directory -C examples/template package
	python3 tools/package_raptor.py --inspect \
		examples/template/build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/libwipi-starter.zip

platformer:
	$(MAKE) --no-print-directory -C examples/platformer package inspect

test-platformer-example: platformer
	python3 tests/check_raptor_elf.py \
		examples/platformer/build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/binary.mod \
		$(OBJDUMP)

sdk-examples:
	$(MAKE) --no-print-directory -C examples/graphics-gallery package inspect
	$(MAKE) --no-print-directory -C examples/memory-resource package inspect
	$(MAKE) --no-print-directory -C examples/audio-player package inspect
	$(MAKE) --no-print-directory -C examples/vibrate package inspect
	$(MAKE) --no-print-directory -C examples/system-services package inspect
	$(MAKE) --no-print-directory -C examples/image-pipeline package inspect
	$(MAKE) --no-print-directory -C examples/network-lifecycle package inspect

test-sdk-examples: sdk-examples
	python3 tests/check_raptor_elf.py \
		examples/graphics-gallery/build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/binary.mod \
		$(OBJDUMP)
	python3 tests/check_raptor_elf.py \
		examples/memory-resource/build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/binary.mod \
		$(OBJDUMP)
	python3 tests/check_raptor_elf.py \
		examples/audio-player/build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/binary.mod \
		$(OBJDUMP)
	python3 tests/check_raptor_elf.py \
		examples/vibrate/build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/binary.mod \
		$(OBJDUMP)
	python3 tests/check_raptor_elf.py \
		examples/system-services/build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/binary.mod \
		$(OBJDUMP)
	python3 tests/check_raptor_elf.py \
		examples/image-pipeline/build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/binary.mod \
		$(OBJDUMP)
	python3 tests/check_raptor_elf.py \
		examples/network-lifecycle/build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/binary.mod \
		$(OBJDUMP)

aram-sdk-examples:
	$(MAKE) --no-print-directory -C examples/graphics-gallery \
		INSTALL_PROFILE=aram-raptor package inspect
	$(MAKE) --no-print-directory -C examples/memory-resource \
		INSTALL_PROFILE=aram-raptor package inspect
	$(MAKE) --no-print-directory -C examples/audio-player \
		INSTALL_PROFILE=aram-raptor package inspect
	$(MAKE) --no-print-directory -C examples/vibrate \
		INSTALL_PROFILE=aram-raptor package inspect
	$(MAKE) --no-print-directory -C examples/system-services \
		INSTALL_PROFILE=aram-raptor package inspect
	$(MAKE) --no-print-directory -C examples/image-pipeline \
		INSTALL_PROFILE=aram-raptor package inspect
	$(MAKE) --no-print-directory -C examples/network-lifecycle \
		INSTALL_PROFILE=aram-raptor package inspect
	$(MAKE) --no-print-directory -C examples/database-crud package inspect
	$(MAKE) --no-print-directory -C examples/filesystem package inspect
	$(MAKE) --no-print-directory -C examples/media-suite package inspect

test-aram-sdk-examples: aram-sdk-examples
	python3 tests/check_aram_sdk_examples.py $(OBJDUMP)

ktf-examples:
	$(MAKE) --no-print-directory API_LEVEL=1.2.1 PROFILE=ktf-samsung \
		INSTALL_PROFILE=aram-ktf all
	$(MAKE) --no-print-directory -C examples/template PROFILE=ktf-samsung \
		INSTALL_PROFILE=aram-ktf package inspect
	$(MAKE) --no-print-directory -C examples/platformer PROFILE=ktf-samsung \
		INSTALL_PROFILE=aram-ktf package inspect
	$(MAKE) --no-print-directory -C examples/graphics-gallery PROFILE=ktf-samsung \
		INSTALL_PROFILE=aram-ktf package inspect
	$(MAKE) --no-print-directory -C examples/memory-resource PROFILE=ktf-samsung \
		INSTALL_PROFILE=aram-ktf package inspect
	$(MAKE) --no-print-directory -C examples/audio-player PROFILE=ktf-samsung \
		INSTALL_PROFILE=aram-ktf package inspect
	$(MAKE) --no-print-directory -C examples/vibrate PROFILE=ktf-samsung \
		INSTALL_PROFILE=aram-ktf package inspect
	$(MAKE) --no-print-directory -C examples/system-services PROFILE=ktf-samsung \
		INSTALL_PROFILE=aram-ktf package inspect
	$(MAKE) --no-print-directory -C examples/image-pipeline PROFILE=ktf-samsung \
		INSTALL_PROFILE=aram-ktf package inspect
	$(MAKE) --no-print-directory -C examples/network-lifecycle PROFILE=ktf-samsung \
		INSTALL_PROFILE=aram-ktf package inspect
	$(MAKE) --no-print-directory -C examples/database-crud PROFILE=ktf-samsung \
		INSTALL_PROFILE=aram-ktf package inspect
	$(MAKE) --no-print-directory -C examples/filesystem PROFILE=ktf-samsung \
		INSTALL_PROFILE=aram-ktf package inspect
	$(MAKE) --no-print-directory -C examples/media-suite PROFILE=ktf-samsung \
		INSTALL_PROFILE=aram-ktf package inspect

test-ktf-examples: ktf-examples
	python3 tests/check_ktf_examples.py $(OBJDUMP) $(NM)

test-target: test-target-ktf test-target-skt test-target-lgt

test: test-host test-target

clean:
	$(MAKE) --no-print-directory -C examples/template clean
	$(MAKE) --no-print-directory -C examples/platformer clean
	$(MAKE) --no-print-directory -C examples/graphics-gallery clean
	$(MAKE) --no-print-directory -C examples/memory-resource clean
	$(MAKE) --no-print-directory -C examples/audio-player clean
	$(MAKE) --no-print-directory -C examples/vibrate clean
	$(MAKE) --no-print-directory -C examples/system-services clean
	$(MAKE) --no-print-directory -C examples/image-pipeline clean
	$(MAKE) --no-print-directory -C examples/network-lifecycle clean
	$(MAKE) --no-print-directory -C examples/graphics-gallery \
		INSTALL_PROFILE=aram-raptor clean
	$(MAKE) --no-print-directory -C examples/memory-resource \
		INSTALL_PROFILE=aram-raptor clean
	$(MAKE) --no-print-directory -C examples/audio-player \
		INSTALL_PROFILE=aram-raptor clean
	$(MAKE) --no-print-directory -C examples/vibrate \
		INSTALL_PROFILE=aram-raptor clean
	$(MAKE) --no-print-directory -C examples/system-services \
		INSTALL_PROFILE=aram-raptor clean
	$(MAKE) --no-print-directory -C examples/image-pipeline \
		INSTALL_PROFILE=aram-raptor clean
	$(MAKE) --no-print-directory -C examples/network-lifecycle \
		INSTALL_PROFILE=aram-raptor clean
	$(MAKE) --no-print-directory -C examples/database-crud clean
	$(MAKE) --no-print-directory -C examples/filesystem clean
	$(MAKE) --no-print-directory -C examples/media-suite clean
	$(MAKE) --no-print-directory -C examples/handset-probe clean
	rm -rf build
