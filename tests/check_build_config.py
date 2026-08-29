#!/usr/bin/env python3
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def run_make(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["make", "--no-print-directory", "-n", "-B", "all", *arguments],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def require_failure(arguments: tuple[str, ...], message: str) -> None:
    result = run_make(*arguments)
    if result.returncode == 0:
        raise AssertionError(
            f"make {' '.join(arguments)} unexpectedly succeeded:\n{result.stdout}"
        )
    if message not in result.stdout:
        raise AssertionError(
            f"make {' '.join(arguments)} did not report {message!r}:\n"
            f"{result.stdout}"
        )


def compile_header(*definitions: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "arm-none-eabi-gcc",
            "-Iinclude",
            "-mcpu=arm7tdmi",
            "-mthumb",
            "-fsyntax-only",
            "-x",
            "c",
            *definitions,
            "-",
        ],
        cwd=ROOT,
        input="#include <wipi/wipi.h>\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


supported = run_make(
    "API_LEVEL=1.2.1", "PROFILE=ktf-samsung", "INSTALL_PROFILE=none"
)
if supported.returncode != 0:
    raise AssertionError(f"implemented build pair failed:\n{supported.stdout}")
if "build/wipi-1.2.1/ktf-samsung/none/" not in supported.stdout.replace("\\", "/"):
    raise AssertionError("build output does not keep all three selection axes")
if "-DLIBWIPI_API_LEVEL_1_2_1=1" not in supported.stdout:
    raise AssertionError("build does not define the selected source API level")

skt = run_make(
    "API_LEVEL=1.2.1",
    "PROFILE=skt-samsung-sch-w830-dl21",
    "INSTALL_PROFILE=none",
)
if skt.returncode != 0:
    raise AssertionError(f"SCH-W830 SKT library build failed:\n{skt.stdout}")
if "build/wipi-1.2.1/skt-samsung-sch-w830-dl21/none/" not in skt.stdout.replace(
    "\\", "/"
):
    raise AssertionError("SKT build output does not keep the exact profile axis")
if "-DLIBWIPI_PROFILE_SKT_SAMSUNG_SCH_W830_DL21=1" not in skt.stdout:
    raise AssertionError("SKT build does not define the exact device profile")

emulator = run_make(
    "API_LEVEL=1.2.1",
    "PROFILE=lgt-raptor",
    "INSTALL_PROFILE=aram-wie-raptor",
)
if emulator.returncode != 0:
    raise AssertionError(f"ARAM/WIE emulator build triple failed:\n{emulator.stdout}")
if "build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/" not in emulator.stdout.replace("\\", "/"):
    raise AssertionError("emulator output does not keep all three selection axes")
if "-DLIBWIPI_INSTALL_ARAM_WIE_RAPTOR=1" not in emulator.stdout:
    raise AssertionError("build does not define the selected install profile")

aram = run_make(
    "API_LEVEL=1.2.1",
    "PROFILE=lgt-raptor",
    "INSTALL_PROFILE=aram-raptor",
)
if aram.returncode != 0:
    raise AssertionError(f"ARAM emulator build triple failed:\n{aram.stdout}")
if "build/wipi-1.2.1/lgt-raptor/aram-raptor/" not in aram.stdout.replace("\\", "/"):
    raise AssertionError("ARAM output does not keep all three selection axes")
if "-DLIBWIPI_INSTALL_ARAM_RAPTOR=1" not in aram.stdout:
    raise AssertionError("build does not define the ARAM install profile")

for level in ("2.0", "2.0.1", "2.1.0", "2.2.0"):
    require_failure((f"API_LEVEL={level}", "PROFILE=ktf-samsung"), "not implemented")
require_failure(("API_LEVEL=9.9", "PROFILE=ktf-samsung"), "unknown API_LEVEL")
require_failure(
    ("API_LEVEL=1.2.1", "PROFILE=lgt-raptor", "INSTALL_PROFILE=none"),
    "unavailable build triple",
)
require_failure(
    (
        "API_LEVEL=1.2.1",
        "PROFILE=skt-samsung-sch-w830-dl21",
        "INSTALL_PROFILE=aram-ktf",
    ),
    "unavailable build triple",
)
require_failure(
    (
        "API_LEVEL=1.2.1",
        "PROFILE=ktf-samsung",
        "INSTALL_PROFILE=aram-raptor",
    ),
    "unavailable build triple",
)
require_failure(
    (
        "API_LEVEL=1.2.1",
        "PROFILE=ktf-samsung",
        "INSTALL_PROFILE=aram-wie-raptor",
    ),
    "unavailable build triple",
)
require_failure(("API_LEVEL=1.2.1", "PROFILE=host-sim"), "unavailable API/profile pair")

selected_header = compile_header(
    "-DLIBWIPI_API_LEVEL_1_2_1=1",
    "-DLIBWIPI_PROFILE_KTF_SAMSUNG=1",
)
if selected_header.returncode != 0:
    raise AssertionError(f"selected public header failed:\n{selected_header.stdout}")
unselected_header = compile_header("-DLIBWIPI_PROFILE_KTF_SAMSUNG=1")
if unselected_header.returncode == 0:
    raise AssertionError("public header accepted an absent API-level selection")
if "select exactly one implemented libwipi API level" not in unselected_header.stdout:
    raise AssertionError(
        f"public header reported the wrong selection failure:\n{unselected_header.stdout}"
    )

skt_header = compile_header(
    "-DLIBWIPI_API_LEVEL_1_2_1=1",
    "-DLIBWIPI_PROFILE_SKT_SAMSUNG_SCH_W830_DL21=1",
)
if skt_header.returncode != 0:
    raise AssertionError(f"SCH-W830 SKT selected header failed:\n{skt_header.stdout}")

lgt_header = compile_header(
    "-DLIBWIPI_API_LEVEL_1_2_1=1",
    "-DLIBWIPI_PROFILE_LGT_RAPTOR=1",
    "-DLIBWIPI_INSTALL_ARAM_WIE_RAPTOR=1",
)
if lgt_header.returncode != 0:
    raise AssertionError(f"ARAM/WIE selected header failed:\n{lgt_header.stdout}")

aram_header = compile_header(
    "-DLIBWIPI_API_LEVEL_1_2_1=1",
    "-DLIBWIPI_PROFILE_LGT_RAPTOR=1",
    "-DLIBWIPI_INSTALL_ARAM_RAPTOR=1",
)
if aram_header.returncode != 0:
    raise AssertionError(f"ARAM selected header failed:\n{aram_header.stdout}")

print("verified explicit API/profile/install build selection")
