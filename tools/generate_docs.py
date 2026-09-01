#!/usr/bin/env python3
"""Generate the libwipi documentation portal from versioned repository facts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import re
import sys
from typing import Iterable

if __package__:
    from . import docs_package_assets, generate
else:
    import docs_package_assets
    import generate


ROOT = generate.ROOT
DOCS = ROOT / "docs"
GENERATED = DOCS / "generated"
RELEASE_BUNDLES = ROOT / "spec" / "releases" / "bundles.json"


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON document must be an object: {path.relative_to(ROOT)}")
    return value


def profile_binding_names(profile: dict[str, object]) -> set[str]:
    relative = profile.get("bindings")
    if not isinstance(relative, str):
        return set()
    path = generate.repository_path(relative, f"{profile['id']} bindings")
    with path.open("r", encoding="utf-8", newline="") as stream:
        return {row["name"] for row in csv.DictReader(stream)}


def table(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def code(value: object) -> str:
    return f"`{str(value).replace('`', '')}`"


def family_slug(family: str) -> str:
    if family == "CSTDLIB":
        return "cstdlib"
    return generate.FAMILY_FILES[family]


def source_api_names(rows: Iterable[dict[str, str]], source: str) -> list[str]:
    return sorted(
        row["name"]
        for row in rows
        if re.search(rf"\b{re.escape(row['name'])}\s*\(", source)
    )


def manifest_api_names(manifest: dict[str, object]) -> set[str]:
    names: set[str] = set()
    for example in manifest.get("examples", []):
        expect = example.get("expect", {})
        names.update(expect.get("required_apis", []))
        names.update(expect.get("restart", {}).get("required_apis", []))
    return names


def read_example_records(
    rows: list[dict[str, str]], bootstrap_api_level: str
) -> dict[str, dict[str, object]]:
    manifests = [
        load_json(ROOT / "examples" / "sdk-lab.json"),
        load_json(ROOT / "examples" / "sdk-lab-aram.json"),
        load_json(ROOT / "examples" / "sdk-lab-ktf.json"),
    ]
    by_example: dict[str, list[dict[str, object]]] = defaultdict(list)
    for manifest in manifests:
        for example in manifest["examples"]:
            by_example[str(example["id"])].append(
                {
                    "api_level": manifest["api_level"],
                    "abi_profile": manifest["abi_profile"],
                    "install_profile": manifest["install_profile"],
                    "expected": example["expect"],
                    "package": example["package"],
                }
            )

    records: dict[str, dict[str, object]] = {}
    for directory in sorted((ROOT / "examples").iterdir()):
        if not directory.is_dir() or not (directory / "main.c").is_file():
            continue
        example_id = directory.name
        readme = directory / "README.md"
        readme_text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
        title_match = re.search(r"^#\s+(.+)$", readme_text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else example_id.replace("-", " ").title()
        paragraphs = [
            " ".join(part.split())
            for part in re.split(r"\n\s*\n", readme_text)
            if part.strip() and not part.lstrip().startswith(("#", "```", "|"))
        ]
        summary = paragraphs[0] if paragraphs else "A checked-in libwipi application example."
        source = (directory / "main.c").read_text(encoding="utf-8")
        uses = set(source_api_names(rows, source))
        for variant in by_example.get(example_id, []):
            uses.update(variant["expected"].get("required_apis", []))
            uses.update(variant["expected"].get("restart", {}).get("required_apis", []))
        records[example_id] = {
            "id": example_id,
            "title": title,
            "summary": summary,
            "source": f"examples/{example_id}/main.c",
            "readme": f"examples/{example_id}/README.md" if readme.is_file() else None,
            "apis": sorted(uses),
            "variants": by_example.get(example_id, []),
        }

    conformance = records.get("conformance")
    if conformance is not None:
        coverage = load_json(ROOT / "examples" / "conformance" / "coverage.json")
        coverage_names = {
            name
            for category in coverage["categories"].values()
            for name in category["apis"]
        }
        catalog_names = {row["name"] for row in rows}
        conformance["apis"] = sorted(set(conformance["apis"]) | (coverage_names & catalog_names))
        conformance["variants"] = [
            {
                "api_level": coverage["api_level"],
                "abi_profile": coverage["abi_profile"],
                "install_profile": coverage["install_profile"],
                "expected": {"required_apis": sorted(coverage_names & catalog_names)},
                "package": (
                    f"build/wipi-{coverage['api_level']}/{coverage['abi_profile']}/"
                    f"{coverage['install_profile']}/examples/conformance/"
                    "libwipi-conformance.zip"
                ),
            },
            {
                "api_level": bootstrap_api_level,
                "abi_profile": "ktf-samsung",
                "install_profile": "aram-ktf",
                "expected": {"required_apis": sorted(coverage_names & catalog_names)},
                "package": (
                    f"build/wipi-{bootstrap_api_level}/ktf-samsung/aram-ktf/"
                    "examples/conformance/libwipi-conformance.zip"
                ),
            },
        ]

    defaults = {
        "hello": [
            (
                "aram-wie-raptor",
                f"build/wipi-{bootstrap_api_level}/lgt-raptor/aram-wie-raptor/"
                "examples/hello/libwipi-hello.zip",
            ),
            (
                "aram-raptor",
                f"build/wipi-{bootstrap_api_level}/lgt-raptor/aram-raptor/"
                "examples/hello/libwipi-hello.zip",
            ),
            (
                "aram-ktf",
                f"build/wipi-{bootstrap_api_level}/ktf-samsung/aram-ktf/"
                "examples/hello/libwipi-hello.zip",
            ),
        ],
        "template": [
            (
                "aram-wie-raptor",
                f"examples/template/build/wipi-{bootstrap_api_level}/lgt-raptor/"
                "aram-wie-raptor/libwipi-starter.zip",
            ),
            (
                "aram-ktf",
                f"examples/template/build/wipi-{bootstrap_api_level}/ktf-samsung/"
                "aram-ktf/libwipi-starter.zip",
            ),
        ],
        "platformer": [
            (
                "aram-wie-raptor",
                f"examples/platformer/build/wipi-{bootstrap_api_level}/lgt-raptor/"
                "aram-wie-raptor/libwipi-sky-hopper.zip",
            ),
            (
                "aram-ktf",
                f"examples/platformer/build/wipi-{bootstrap_api_level}/ktf-samsung/"
                "aram-ktf/libwipi-sky-hopper.zip",
            ),
        ],
    }
    for example_id, variants in defaults.items():
        record = records.get(example_id)
        if record is not None and not record["variants"]:
            record["variants"] = [
                {
                    "api_level": bootstrap_api_level,
                    "abi_profile": (
                        "ktf-samsung" if install_profile == "aram-ktf" else "lgt-raptor"
                    ),
                    "install_profile": install_profile,
                    "expected": {"required_apis": record["apis"]},
                    "package": package,
                }
                for install_profile, package in variants
            ]
    handset_probe = records.get("handset-probe")
    if handset_probe is not None:
        handset_probe["variants"] = [
            {
                "api_level": bootstrap_api_level,
                "abi_profile": "ktf-samsung",
                "install_profile": "sch-w8300-qpst-probe",
                "expected": {"required_apis": handset_probe["apis"]},
                "package": (
                    f"examples/handset-probe/build/wipi-{bootstrap_api_level}/"
                    "ktf-samsung/sch-w8300-qpst-probe/"
                    "libwipi-sch-w8300-probe.zip"
                ),
            }
        ]
    return records


def observed_by_install() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for name in ("sdk-lab.json", "sdk-lab-aram.json", "sdk-lab-ktf.json"):
        manifest = load_json(ROOT / "examples" / name)
        result[str(manifest["install_profile"])] = manifest_api_names(manifest)
    coverage = load_json(ROOT / "examples" / "conformance" / "coverage.json")
    conformance_names = {
        api
        for category in coverage["categories"].values()
        for api in category["apis"]
        if api.startswith("MC_")
    }
    result.setdefault(str(coverage["install_profile"]), set()).update(conformance_names)
    return result


def availability_rows(
    api_level: str,
    row: dict[str, str],
    profiles: list[dict[str, object]],
    installs: list[dict[str, object]],
    observed: dict[str, set[str]],
) -> list[tuple[str, str, str]]:
    result: list[tuple[str, str, str]] = []
    name = row["name"]
    for profile in sorted(profiles, key=lambda item: str(item["id"])):
        profile_id = str(profile["id"])
        mapping = profile["api_level_mappings"].get(api_level)
        if not mapping or not mapping.get("headers"):
            continue
        if profile_id == "host-sim":
            status = "host semantic test" if row["implementation"] == "local" else "headers only"
            result.append((profile_id, "none", status))
            continue
        install_ids = mapping.get("install_profiles", ["none"])
        for install_id in install_ids:
            if profile_id == "ktf-samsung":
                if row["implementation"] == "local":
                    status = "linkable local implementation"
                elif (
                    row["implementation"] == "table"
                    and row["ktf_samsung_confidence"] == "confirmed"
                    and row["abi_class"] != "variadic-unverified"
                ):
                    status = "linkable generated veneer"
                else:
                    status = "declared; no verified veneer"
                if install_id == "sch-w8300-qpst-probe":
                    status += "; named-device candidate"
                result.append((profile_id, str(install_id), status))
                continue
            if profile_id == "skt-samsung-sch-w830-dl21":
                if row["implementation"] == "local":
                    status = "linkable local implementation"
                elif name not in profile_binding_names(profile):
                    status = "declared; no direct SCH binding"
                elif row["abi_class"] == "variadic-unverified":
                    status = "declared; variadic SCH call is not forwarded"
                else:
                    status = "linkable exact-device fixed-root veneer"
                result.append((profile_id, str(install_id), status))
                continue
            install = next(
                (item for item in installs if item["id"] == install_id), None
            )
            methods = (
                install.get("imports", {}).get("confirmed_public_methods", {})
                if install is not None
                else {}
            )
            if name not in methods:
                status = "declared; no confirmed adapter"
            elif name in observed.get(str(install_id), set()):
                status = "observed in the scoped emulator suite"
            else:
                status = "linkable for the scoped install profile"
            result.append((profile_id, str(install_id), status))
    return result


def render_api_symbol(
    api_level: str,
    row: dict[str, str],
    documentation: dict[str, object] | None,
    profiles: list[dict[str, object]],
    installs: list[dict[str, object]],
    observed: dict[str, set[str]],
    example_records: dict[str, dict[str, object]],
) -> str:
    if documentation is not None:
        for example_id in documentation.get("examples", []):
            record = example_records.get(str(example_id))
            if record is None or row["name"] not in record["apis"]:
                raise ValueError(
                    f"documented example {example_id} does not exercise {row['name']}"
                )
    summary = (
        str(documentation["summary"])
        if documentation is not None
        else "Detailed public semantics for this cataloged symbol have not yet been reviewed."
    )
    status = str(documentation["status"]) if documentation is not None else "cataloged"
    family = row["family"]
    lines = [
        "---",
        "myst:",
        "  html_meta:",
        f"    description: {json.dumps(summary)}",
        "---",
        "",
        "<!-- Generated by tools/generate_docs.py. Do not edit. -->",
        "",
        f"# `{row['name']}`",
        "",
        summary,
        "",
        "## Prototype",
        "",
        "```c",
        row["prototype"] + ";",
        "```",
        "",
        "```{doxygenfunction} " + row["name"],
        ":project: libwipi",
        "```",
        "",
        "## Catalog identity",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| API level | {code(api_level)} |",
        f"| Family | [{code(family)}](../families/{family_slug(family)}.md) |",
        f"| Ordinal | {row['ordinal']} |",
        f"| Documentation | {code(status)} |",
        f"| Implementation class | {code(row['implementation'])} |",
        f"| ABI class | {code(row['abi_class'])} |",
        "",
    ]
    if documentation is not None:
        lines.extend(["## Usage", ""])
        if documentation.get("details"):
            lines.extend([str(documentation["details"]), ""])
        parameters = documentation.get("parameters", {})
        if parameters:
            lines.extend(["### Parameters", "", "| Name | Meaning |", "|---|---|"])
            for name, description in parameters.items():
                lines.append(f"| {code(name)} | {table(description)} |")
            lines.append("")
        if documentation.get("returns"):
            lines.extend(["### Return value", "", str(documentation["returns"]), ""])
        if documentation.get("ownership"):
            lines.extend(["### Ownership", "", str(documentation["ownership"]), ""])
        if documentation.get("notes"):
            lines.extend(["### Notes", ""])
            lines.extend(f"- {note}" for note in documentation["notes"])
            lines.append("")
    else:
        lines.extend(
            [
                "## Usage",
                "",
                "> This page intentionally preserves unknown semantics as unknown. The catalog",
                "> proves membership and the prototype; it does not by itself prove behavior.",
                "",
            ]
        )

    lines.extend(
        [
            "## Profile availability",
            "",
            "API membership, device ABI, and install profile are independent. The rows below",
            "describe libwipi implementation evidence, not platform-wide WIPI requirements.",
            "",
            "| ABI profile | Install profile | Current evidence |",
            "|---|---|---|",
        ]
    )
    for profile_id, install_id, availability in availability_rows(
        api_level, row, profiles, installs, observed
    ):
        lines.append(
            f"| {code(profile_id)} | {code(install_id)} | {table(availability)} |"
        )
    lines.append("")

    examples = sorted(
        example_id
        for example_id, record in example_records.items()
        if row["name"] in record["apis"]
    )
    if examples:
        lines.extend(["## Compiled examples", ""])
        for example_id in examples:
            record = example_records[example_id]
            lines.append(
                f"- [{record['title']}](../../../examples/{example_id}.md)"
            )
        lines.append("")
    lines.extend(
        [
            "## Evidence boundary",
            "",
            (
                "Samsung/KTF selector confidence: "
                f"{code(row['ktf_samsung_confidence'])}. "
                f"Catalog evidence: {code(row['evidence'])}."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def render_api_family(
    api_level: str,
    family: str,
    rows: list[dict[str, str]],
    family_docs: dict[str, str],
    symbol_docs: dict[str, dict[str, object]],
) -> str:
    reviewed = sum(name in symbol_docs for name in (row["name"] for row in rows))
    lines = [
        "<!-- Generated by tools/generate_docs.py. Do not edit. -->",
        f"# {family_docs['title']} ({code(family)})",
        "",
        family_docs["summary"],
        "",
        f"This WIPI-C {api_level} family contains **{len(rows)}** cataloged APIs; "
        f"**{reviewed}** currently have reviewed or draft semantic notes.",
        "",
        "| Symbol | Prototype | Documentation |",
        "|---|---|---|",
    ]
    for row in rows:
        status = symbol_docs.get(row["name"], {}).get("status", "cataloged")
        lines.append(
            f"| [{code(row['name'])}](../symbols/{row['name']}.md) | "
            f"{code(row['prototype'])} | {code(status)} |"
        )
    lines.extend(["", "```{toctree}", ":hidden:", ":maxdepth: 1", ""])
    lines.extend(f"../symbols/{row['name']}" for row in rows)
    lines.extend(["```", ""])
    return "\n".join(lines)


def render_api_index(
    api_level: str,
    level: dict[str, object],
    rows: list[dict[str, str]],
    api_docs: dict[str, object],
) -> str:
    counts = Counter(row["family"] for row in rows)
    lines = [
        "<!-- Generated by tools/generate_docs.py. Do not edit. -->",
        f"# WIPI-C {api_level} API reference",
        "",
        f"This reference is generated from the **{len(rows)}-row** canonical catalog and",
        "version-scoped semantic documentation. A declaration is not automatically a",
        "claim that every profile links, packages, or runs the symbol.",
        "",
        f"Reference revision: {code(level['reference_revision'])}.",
        "",
        "| Family | APIs | Description |",
        "|---|---:|---|",
    ]
    for family in sorted(counts):
        docs = api_docs["families"][family]
        lines.append(
            f"| [{code(family)}](families/{family_slug(family)}.md) | "
            f"{counts[family]} | {table(docs['summary'])} |"
        )
    lines.extend(["", "```{toctree}", ":hidden:", ""])
    lines.extend(
        f"families/{family_slug(family)}" for family in sorted(counts)
    )
    lines.extend(["```", ""])
    return "\n".join(lines)


def render_support_matrix(
    bootstrap_api_level: str,
    levels: list[dict[str, object]],
    profiles: list[dict[str, object]],
    installs: list[dict[str, object]],
    catalogs: dict[str, list[dict[str, str]]],
    observed: dict[str, set[str]],
) -> str:
    rows = catalogs[bootstrap_api_level]
    public_names = {row["name"] for row in rows}
    ktf_linkable = sum(
        (row["implementation"] == "local")
        or (
            row["implementation"] == "table"
            and row["ktf_samsung_confidence"] == "confirmed"
            and row["abi_class"] != "variadic-unverified"
        )
        for row in rows
    )
    skt_profile = next(
        profile
        for profile in profiles
        if profile["id"] == "skt-samsung-sch-w830-dl21"
    )
    skt_linkable = int(skt_profile["coverage"]["linkable_public_symbols"])
    lines = [
        "<!-- Generated by tools/generate_docs.py. Do not edit. -->",
        "# Support and compatibility matrix",
        "",
        "The source API level, device ABI profile, and executable/install profile are",
        "separate selections. The strongest verified milestone is reported for each exact",
        "combination; no row implies compatibility with an unnamed handset.",
        "",
        "| API / ABI / install | Strongest current result | Observed or linkable surface | Real device |",
        "|---|---|---:|---|",
        f"| {code(bootstrap_api_level + '/ktf-samsung/none')} | Headers, generated adapter, relocatable link, and object-code tests; no package profile | {ktf_linkable} linkable APIs | No |",
        f"| {code(bootstrap_api_level + '/skt-samsung-sch-w830-dl21/none')} | Exact SCH-W830 DL21 fixed-root adapter, relocatable link, archive audit, and per-veneer object-code tests; no package/load claim | {skt_linkable} linkable APIs | No |",
    ]
    for install in sorted(installs, key=lambda item: str(item["id"])):
        install_id = str(install["id"])
        combination = (
            f"{install['api_level']}/{install['abi_profile']}/{install_id}"
        )
        claims = install.get("claims", {})
        milestones = [
            name.replace("_", " ")
            for name in ("packages", "loads", "entry", "first_frame", "interactive")
            if claims.get(name)
        ]
        if not milestones:
            evidence_claims: dict[str, object] = {}
            evidence_paths = {
                str(value)
                for key, value in claims.items()
                if key.endswith("_evidence") and isinstance(value, str)
            }
            for evidence_path in sorted(evidence_paths):
                evidence_claims.update(
                    load_json(ROOT / evidence_path).get("claims", {})
                )
            milestones = [
                name.replace("_", " ")
                for name in ("packages", "loads", "entry", "first_frame", "interactive")
                if evidence_claims.get(name)
            ]
        result = milestones[-1] if milestones else str(install.get("status", "scoped"))
        observed_count = len(observed.get(install_id, set()) & public_names)
        surface = f"{observed_count} observed APIs"
        if observed_count == 0 and isinstance(claims.get("first_frame_evidence"), str):
            evidence = load_json(ROOT / str(claims["first_frame_evidence"]))
            package_count = evidence.get("coverage", {}).get("packages")
            if isinstance(package_count, int):
                surface = f"{package_count} first-frame packages"
        target_device = install.get("target_device")
        if isinstance(target_device, dict):
            required = install.get("imports", {}).get("required_public_apis", [])
            if observed_count == 0 and isinstance(required, list):
                surface = f"{len(required)} linkable candidate APIs; 0 observed"
            scope = "for an unverified named-device probe"
        else:
            scope = "on the named emulator contract"
        lines.append(
            f"| {code(combination)} | {table(result)} {scope} | "
            f"{surface} | No |"
        )
    lines.extend(
        [
            "",
            "## API version line",
            "",
            "| WIPI-C level | Catalog | SDK status |",
            "|---|---|---|",
        ]
    )
    for level in levels:
        lines.append(
            f"| {code(level['api_level'])} | {code(level['catalog_status'])} | "
            f"{code(level['sdk_status'])} |"
        )
    lines.extend(
        [
            "",
            "> Emulator evidence is additive. A real-device result must name the carrier, OEM,",
            "> model, firmware, install path, and tested package hash.",
            "",
        ]
    )
    return "\n".join(lines)


def render_example_index(records: dict[str, dict[str, object]]) -> str:
    lines = [
        "<!-- Generated by tools/generate_docs.py. Do not edit. -->",
        "# Compiled example gallery",
        "",
        "Every page below is backed by an ordinary application source that is compiled by",
        "the repository gates. API lists are derived from source and suite manifests.",
        "",
        "Use **Run in ARAM** beside a compiled package to open it in the nightly web",
        "emulator. The player downloads the published HTTPS package directly, verifies",
        "the documented SHA-256 digest, and passes the bytes to ARAM locally; the package is",
        "not uploaded to an application server.",
        "",
        "| Example | Cataloged APIs used | Tested install profiles |",
        "|---|---:|---|",
    ]
    for example_id, record in sorted(records.items()):
        installs = sorted(
            {str(variant["install_profile"]) for variant in record["variants"]}
        )
        lines.append(
            f"| [{record['title']}]({example_id}.md) | {len(record['apis'])} | "
            f"{', '.join(code(item) for item in installs) or 'source-only'} |"
        )
    lines.extend(["", "```{toctree}", ":hidden:", ""])
    lines.extend(example_id for example_id in sorted(records))
    lines.extend(["```", ""])
    return "\n".join(lines)


def render_example_page(record: dict[str, object]) -> str:
    api_levels = sorted(
        {str(variant["api_level"]) for variant in record["variants"]}
    )
    api_level = api_levels[0] if len(api_levels) == 1 else None
    lines = [
        "<!-- Generated by tools/generate_docs.py. Do not edit. -->",
        f"# {record['title']}",
        "",
        str(record["summary"]),
        "",
        "## Source",
        "",
        f"- {{download}}`Application source <../../../{record['source']}>`",
    ]
    if record["readme"]:
        lines.append(
            f"- {{download}}`Example guide <../../../{record['readme']}>`"
        )
    if record["variants"]:
        lines.extend(
            [
                "",
                "## Build and runtime axes",
                "",
                "| API level | ABI profile | Install profile | Package |",
                "|---|---|---|---|",
            ]
        )
        for variant in record["variants"]:
            package_record = {
                "example_id": str(record["id"]),
                "api_level": str(variant["api_level"]),
                "abi_profile": str(variant["abi_profile"]),
                "install_profile": str(variant["install_profile"]),
                "package": str(variant["package"]),
            }
            package = (
                docs_package_assets.package_marker(package_record)
                if variant["package"]
                else "build from source"
            )
            lines.append(
                f"| {code(variant['api_level'])} | {code(variant['abi_profile'])} | "
                f"{code(variant['install_profile'])} | {package} |"
            )
        if any(variant["package"] for variant in record["variants"]):
            lines.extend(
                [
                    "",
                    "> Compiled downloads are checked into the SDK with their exact build",
                    "> revision, inspected against the selected package profile, and published",
                    "> with SHA-256",
                    "> hashes. Compatibility is limited to the milestones recorded for each",
                    "> exact install profile.",
                ]
            )
    lines.extend(
        [
            "",
            "## APIs demonstrated",
            "",
        ]
    )
    if record["apis"]:
        for name in record["apis"]:
            if api_level is None:
                lines.append(f"- {code(name)} (shown by more than one API-level variant)")
            else:
                lines.append(
                    f"- [{code(name)}](../api/{api_level}/symbols/{name}.md)"
                )
    else:
        lines.append("No canonical catalog call was detected in this source.")
    lines.extend(
        [
            "",
            "> The application source remains profile-independent. Emulator orchestration and",
            "> expected observations live in manifests and the owning test repository.",
            "",
        ]
    )
    return "\n".join(lines)


def render_downloads(bundle_manifest: dict[str, object]) -> str:
    lines = [
        "<!-- Generated by tools/generate_docs.py. Do not edit. -->",
        "# Test suites and downloads",
        "",
        "Versioned bundles are built from a clean tag by the pinned GNU Arm toolchain,",
        "checked with the repository gates, hashed, attested, and attached to GitHub Releases.",
        "Workflow artifacts are not the public distribution channel.",
        "",
        "[Open GitHub Releases](https://github.com/mirusu400/libwipi/releases)",
        "",
        "## Individual compiled examples",
        "",
        "Each [Compiled example gallery](examples/index.md) page publishes a",
        "profile-specific checked-in compiled ZIP together with its build revision and",
        "SHA-256 hash. Use the API, ABI, and install-profile columns to choose the",
        "intended emulator contract.",
        "",
        "## Download and verify",
        "",
        "Choose an existing `v...` SDK tag in Releases. With the GitHub CLI:",
        "",
        "```powershell",
        '$tag = "vX.Y.Z"',
        'gh release download $tag --repo mirusu400/libwipi `',
        '  --pattern "libwipi-*.zip" --pattern "SHA256SUMS"',
        "Get-Content SHA256SUMS",
        "Get-FileHash -Algorithm SHA256 .\\libwipi-*.zip",
        "```",
        "",
        "On a POSIX host, verify every downloaded asset automatically with",
        "`sha256sum --check SHA256SUMS`. After extracting one bundle, verify its",
        "inner `SHA256SUMS` before loading a package and read `bundle-manifest.json`",
        "for the exact API level, ABI profile, install profile, source revision, and",
        "evidence boundary.",
        "",
    ]
    for bundle in bundle_manifest["bundles"]:
        lines.extend(
            [
                f"## {bundle['title']}",
                "",
                str(bundle["description"]),
                "",
                "| Field | Value |",
                "|---|---|",
                f"| Bundle ID | {code(bundle['id'])} |",
                f"| API level | {code(bundle['api_level'])} |",
                f"| ABI profile | {code(bundle['abi_profile'])} |",
                f"| Install profile | {code(bundle['install_profile'])} |",
                f"| Build target | {code(bundle['build_target'])} |",
                f"| Suite manifest | [{code(bundle['suite_manifest'])}](../../{bundle['suite_manifest']}) |",
                f"| Evidence | [{code(bundle['evidence'])}](../../{bundle['evidence']}) |",
                f"| Real-device claim | {code(str(bundle['real_device']).lower())} |",
                "",
                f"Release asset pattern: {code('libwipi-' + str(bundle['id']) + '-<sdk-version>.zip')}.",
                "",
            ]
        )
    lines.extend(
        [
            "## Bundle contract",
            "",
            "Each archive contains its WIPI packages, original fixture source, suite and",
            "evidence manifests, a machine-readable bundle manifest, license, and SHA-256",
            "inventory. Compatibility orchestration remains owned by `aram-test`.",
            "",
            "The `ktf-samsung/aram-ktf` downloads use the observed KTF archive shape and",
            "have reached first frame in the pinned ARAM runtime. They are emulator fixtures,",
            "not interactive or real-device-verified handset packages.",
            "",
        ]
    )
    return "\n".join(lines)


def generated_docs_files() -> dict[Path, str]:
    manifest, levels = generate.read_version_manifest()
    _, profiles, installs = generate.read_build_metadata()
    catalogs = generate.read_catalogs(levels)
    observed = observed_by_install()
    result: dict[Path, str] = {}

    bootstrap = str(manifest["bootstrap_api_level"])
    example_records = read_example_records(catalogs[bootstrap], bootstrap)
    for level in levels:
        if level.get("catalog_status") != "implemented":
            continue
        api_level = str(level["api_level"])
        rows = catalogs[api_level]
        api_docs = generate.read_api_docs(level, rows)
        api_root = GENERATED / "api" / api_level
        result[api_root / "index.md"] = render_api_index(api_level, level, rows, api_docs)
        by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            by_family[row["family"]].append(row)
            result[api_root / "symbols" / f"{row['name']}.md"] = render_api_symbol(
                api_level,
                row,
                api_docs["symbols"].get(row["name"]),
                profiles,
                installs,
                observed,
                example_records,
            )
        for family, family_rows in by_family.items():
            result[api_root / "families" / f"{family_slug(family)}.md"] = (
                render_api_family(
                    api_level,
                    family,
                    family_rows,
                    api_docs["families"][family],
                    api_docs["symbols"],
                )
            )

    result[GENERATED / "support-matrix.md"] = render_support_matrix(
        bootstrap, levels, profiles, installs, catalogs, observed
    )
    result[GENERATED / "examples" / "index.md"] = render_example_index(
        example_records
    )
    for example_id, record in example_records.items():
        result[GENERATED / "examples" / f"{example_id}.md"] = render_example_page(
            record
        )
    result[GENERATED / "downloads.md"] = render_downloads(load_json(RELEASE_BUNDLES))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        return generate.update_files(generated_docs_files(), args.check)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
