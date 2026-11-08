"""Pin the current installation and collect inputs for the step 1 source census."""

import hashlib
import importlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


TASK = Path(__file__).resolve().parent
WORKSPACE = TASK.parents[1]
OUTPUT = TASK / "step1_01"
MANIFEST = WORKSPACE / "prealpha/heavy_hearts_hh1/deployment_01/installed_manifest_01.json"
RESOURCE_LITERAL = re.compile(
    r'(?P<depot>(?:[A-Za-z0-9_]+\\)+[A-Za-z0-9_.-]+\.'
    r'(?:questphase|scene|quest|gamedef|ent|app|streamingblock|streamingsector|workspot))'
)
SPEECH_CALL = re.compile(
    r"\b\w*(?:PlayVoice|VoiceOver|PlayDialog|PlayScene|PlaySound|Bark|DialogLine)\w*\b",
    re.IGNORECASE,
)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def write_json(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def file_record(path):
    stat = path.stat()
    return {
        "path": str(path),
        "bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(path),
    }


def verify_file(path, expected, kind):
    if not path.is_file():
        return {"path": str(path), "kind": kind, "status": "MISSING"}
    result = file_record(path)
    result.update(kind=kind, expected_sha256=expected["sha256"])
    result["status"] = (
        "MATCH"
        if result["sha256"] == expected["sha256"]
        and ("bytes" not in expected or result["bytes"] == expected["bytes"])
        else "MISMATCH"
    )
    return result


def collect_source_files(game):
    roots = [
        (game / "r6/scripts", {".reds"}),
        (game / "red4ext/plugins", {".reds"}),
        (game / "bin/x64/plugins/cyber_engine_tweaks/mods", {".lua"}),
        (game / "archive/pc/mod", {".xl"}),
        (game / "r6/tweaks", {".yaml", ".yml"}),
        (game / "mods", {".xl"}),
    ]
    files = set()
    skipped_links = []
    for root, extensions in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.is_symlink() or path.is_junction():
                skipped_links.append(str(path))
                continue
            if path.is_file() and path.suffix.lower() in extensions:
                files.add(path)
    return sorted(files), skipped_links


def main():
    if OUTPUT.exists():
        raise SystemExit("Use a fresh step output directory")
    manifest = read_json(MANIFEST)
    package_manifest = Path(manifest["core_source_epoch"])
    package = read_json(package_manifest)
    candidate = package_manifest.parent
    game = Path(manifest["game_root"])
    checks = [
        verify_file(package_manifest, {"sha256": manifest["core_source_epoch_sha256"]}, "PACKAGE_MANIFEST"),
        verify_file(
            Path(manifest["transaction_manifest"]),
            {"sha256": manifest["transaction_manifest_sha256"]},
            "TRANSACTION_MANIFEST",
        ),
    ]
    for row in manifest["core_files"]:
        checks.append(verify_file(game / row["path"], row, "INSTALLED_CORE"))
        checks.append(verify_file(candidate / "package" / row["path"], row, "CANDIDATE_PACKAGE"))
    for row in manifest["required_files"]:
        checks.append(verify_file(game / row["path"], row, "INSTALLED_REQUIRED"))

    source_root = candidate / "archive_source"
    actual_sources = {
        str(path.relative_to(source_root)).replace("/", "\\"): path
        for path in source_root.rglob("*")
        if path.is_file()
    }
    expected_sources = package["source_resources"]
    source_rows = []
    for depot, expected_hash in sorted(expected_sources.items()):
        check = verify_file(source_root / depot, {"sha256": expected_hash}, "ARCHIVE_SOURCE")
        checks.append(check)
        source_rows.append({"depot": depot, **check})
    differences = {
        "unexpected": sorted(set(actual_sources) - set(expected_sources)),
        "missing": sorted(set(expected_sources) - set(actual_sources)),
    }
    OUTPUT.mkdir()
    baseline = {
        "schema": 1,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "installed_manifest": file_record(MANIFEST),
        "package_manifest": file_record(package_manifest),
        "game_root": str(game),
        "candidate": str(candidate),
        "core_epoch": manifest["core_epoch"],
        "archive_payloads": manifest["archive_payloads"],
        "checks": checks,
        "source_inventory_differences": differences,
        "counts": dict(Counter(row["kind"] for row in checks)),
        "source_extensions": dict(Counter(Path(row["depot"]).suffix for row in source_rows)),
    }
    baseline["status"] = (
        "VERIFIED"
        if all(row["status"] == "MATCH" for row in checks)
        and not any(differences.values())
        else "BASELINE_DISCREPANCY"
    )
    write_json(OUTPUT / "baseline.json", baseline)
    if baseline["status"] != "VERIFIED":
        raise SystemExit("Baseline discrepancy recorded. Resolve it before capturing resources")

    sys.path.insert(0, str(WORKSPACE / "tools/parity_audit"))
    registrations = importlib.import_module("engine").registrations
    bindings, binding_errors, xl_files = registrations(game)
    source_files, skipped_links = collect_source_files(game)
    source_inventory = []
    literal_references = []
    speech_calls = []
    text_errors = []
    for path in source_files:
        record = file_record(path)
        record["core_managed"] = path.relative_to(game).as_posix() in {
            row["path"] for row in manifest["core_files"]
        }
        source_inventory.append(record)
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (UnicodeError, OSError) as error:
            text_errors.append({"path": str(path), "error": str(error)})
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            normalized = line.replace("\\\\", "\\")
            for match in RESOURCE_LITERAL.finditer(normalized):
                literal_references.append(
                    {"path": str(path), "line": line_number, "depot": match["depot"]}
                )
            if SPEECH_CALL.search(line):
                speech_calls.append({"path": str(path), "line": line_number, "text": line.strip()})

    policy_pointer = WORKSPACE / "research/gig_restoration/lore_whitelist_current.json"
    policy = read_json(policy_pointer)
    selection = WORKSPACE / policy["selection_file"]
    selection_check = verify_file(selection, {"sha256": policy["sha256"]}, "CATALOGUE_SELECTION")
    write_json(OUTPUT / "entry_sources.json", {
        "schema": 1,
        "source_files": source_inventory,
        "literal_resource_references": literal_references,
        "speech_api_candidates": speech_calls,
        "xl_phase_bindings": bindings,
        "xl_unparsed": binding_errors,
        "xl_files": xl_files,
        "text_read_errors": text_errors,
        "skipped_links": skipped_links,
        "catalogue_pointer": file_record(policy_pointer),
        "catalogue_selection": selection_check,
        "limits": [
            "Lexical references and API names include stored or unreachable code.",
            "Runtime-generated paths and arbitrary source control flow require later review.",
            "External mod sources identify compatibility boundaries and possible providers.",
            "The existing XL reader reports unsupported quest binding forms explicitly.",
        ],
    })
    attachment_parents = sorted({row["parent"] for row in bindings})
    wanted = sorted(
        set(expected_sources)
        | {row["depot"] for row in literal_references}
        | {row["path"] for row in bindings}
        | set(attachment_parents)
    )
    write_json(OUTPUT / "queries.json", {
        "schema": 1,
        "game_root": str(game),
        "candidate": str(candidate),
        "private": source_rows,
        "wanted": wanted,
        "attachment_only_parents": attachment_parents,
        "scope": "Resource-reference census across all private resources, installed source literals and XL bindings.",
    })
    write_json(OUTPUT / "tool_inputs.json", {
        "files": [file_record(path) for path in [
            TASK / "prepare.py", TASK / "capture_sources.ps1",
            WORKSPACE / "tools/build_phase2a.ps1",
            *sorted((WORKSPACE / "tools/parity_audit").glob("*.py")),
        ]],
    })
    print(json.dumps({
        "status": baseline["status"],
        "installed_paths": len(manifest["core_files"]) + len(manifest["required_files"]),
        "source_resources": len(source_rows),
        "runtime_source_files": len(source_inventory),
        "xl_phase_bindings": len(bindings),
        "initial_resource_queries": len(wanted),
    }))


if __name__ == "__main__":
    main()
