"""Verify the captured step 1 census and record its measured scope."""

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


TASK = Path(__file__).resolve().parent
WORKSPACE = TASK.parents[1]
OUTPUT = TASK / "step1_01"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def fnv1a64(depot):
    value = 14695981039346656037
    for byte in depot.encode("utf-8"):
        value = ((value ^ byte) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return str(value)


def main():
    capture_path = OUTPUT / "capture.json"
    capture = read_json(capture_path)
    baseline = read_json(OUTPUT / "baseline.json")
    entries = read_json(OUTPUT / "entry_sources.json")
    queries = read_json(OUTPUT / "queries.json")
    tool_inputs = read_json(OUTPUT / "tool_inputs.json")
    structured = read_json(OUTPUT / "registrations_structured.json")
    refinement = read_json(OUTPUT / "refinement.json")
    additions = read_json(OUTPUT / "capture_additions.json")
    if additions["initial_capture_sha256"] != sha256(capture_path):
        raise SystemExit("Supplemental capture used a different initial capture")
    if additions["refinement_sha256"] != sha256(OUTPUT / "refinement.json"):
        raise SystemExit("Supplemental capture used a different source refinement")
    resources = capture["resources"] + additions["resources"]
    missing = capture["missing"] + additions["missing"]
    opaque = capture["opaque"] + additions["opaque"]
    discrepancies = []
    checks = []
    protected = (
        baseline["checks"]
        + [baseline["installed_manifest"]]
        + entries["source_files"]
        + [entries["catalogue_pointer"], entries["catalogue_selection"]]
        + tool_inputs["files"]
        + [
            {"path": row["raw"], "sha256": row["sha256"]}
            for row in resources
        ]
    )
    for row in protected:
        path = Path(row["path"])
        current = sha256(path) if path.is_file() else None
        checks.append({"path": str(path), "expected": row["sha256"], "current": current})
        if current != row["sha256"]:
            discrepancies.append({"path": str(path), "kind": "INPUT_CHANGED"})

    private_expected = {row["depot"]: row["sha256"] for row in queries["private"]}
    private_actual = {row["depot"]: row["sha256"] for row in capture["private_readback"]}
    if private_expected != private_actual or len(private_actual) != len(capture["private_readback"]):
        discrepancies.append({"kind": "PRIVATE_READBACK_INVENTORY_MISMATCH"})
    bad_keys = [
        {"depot": row["depot"], "key": row["key"]}
        for row in capture["private_readback"]
        if row["key"] != fnv1a64(row["depot"])
    ]
    if bad_keys:
        discrepancies.append({"kind": "INDEPENDENT_RESOURCE_KEY_MISMATCH", "rows": bad_keys})
    write_json(OUTPUT / "baseline_after.json", {
        "status": "VERIFIED" if not discrepancies else "DISCREPANCIES",
        "checks": checks,
        "discrepancies": discrepancies,
        "archive_metadata_changes": capture["changed_archives"] + additions["changed_archives"],
    })

    providers = defaultdict(list)
    for row in resources:
        providers[row["depot"]].append(row)
    dependencies = []
    unfollowed = Counter()
    for row in resources:
        for reference in row["imports"]:
            extension = Path(reference).suffix.lower()
            target = providers.get(reference, [])
            dependencies.append({
                "source": row["depot"],
                "source_archive": row["archive"],
                "target": reference,
                "evidence": "CR2W_IMPORT",
                "captured_providers": len(target),
                "attachment_only_source": row["attachment_only"],
            })
            if not target:
                unfollowed[extension or "<unknown>"] += 1
    write_json(OUTPUT / "dependency_inventory.json", {
        "scope": "Serialized resource imports, including stored branches.",
        "references": dependencies,
    })
    collisions = [
        {
            "depot": depot,
            "providers": [
                {"archive": row["archive"], "role": row["provider_role"], "sha256": row["sha256"]}
                for row in rows
            ],
            "payloads_identical": len({row["sha256"] for row in rows}) == 1,
            "precedence": "UNRESOLVED",
        }
        for depot, rows in sorted(providers.items())
        if len(rows) > 1
    ]
    opaque_resources = {row["depot"] for row in opaque}
    native_scenes = {
        row["depot"]
        for row in resources
        if row["provider_role"] == "STOCK" and Path(row["depot"]).suffix == ".scene"
    }
    private_scenes = {depot for depot in private_expected if Path(depot).suffix == ".scene"}
    census = capture["graph_provider_census"]
    graph_unique = {row["key"] for row in census}
    scene_unique = {row["key"] for row in census if row["extension"] == ".scene"}
    captured_scene_keys = {
        row["key"] for row in resources if Path(row["depot"]).suffix == ".scene"
    }
    outside_scene_keys = scene_unique - captured_scene_keys
    write_json(OUTPUT / "scene_census_outside_closure.json", {
        "scope": "Global scene providers outside the captured reference closure. Post-Tower relevance requires later review.",
        "providers": [
            row for row in census
            if row["extension"] == ".scene" and row["key"] in outside_scene_keys
        ],
    })
    core_xl = str(Path(baseline["game_root"]) / "archive/pc/mod/zzzz_PTFR_Combined.archive.xl")
    core_bindings = [row for row in structured["phase_bindings"] if row["file"] == core_xl]
    superseded_literals = set(refinement["superseded_partial_literal_candidates"])
    actual_imports = {reference for row in resources for reference in row["imports"]}
    effective_missing = [
        row for row in missing
        if row["depot"] not in superseded_literals or row["depot"] in actual_imports
    ]
    summary = {
        "schema": 1,
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "core_epoch": baseline["core_epoch"],
        "installed_manifest": baseline["installed_manifest"]["path"],
        "installed_manifest_sha256": baseline["installed_manifest"]["sha256"],
        "installed_core_paths_verified": baseline["counts"]["INSTALLED_CORE"],
        "installed_required_paths_verified": baseline["counts"]["INSTALLED_REQUIRED"],
        "candidate_package_paths_verified": baseline["counts"]["CANDIDATE_PACKAGE"],
        "source_resources_verified": len(private_expected),
        "private_archive_members_read_back": len(private_actual),
        "private_scenes": len(private_scenes),
        "source_extensions": baseline["source_extensions"],
        "installed_runtime_source_files": len(entries["source_files"]),
        "xl_phase_bindings": len(structured["phase_bindings"]),
        "core_xl_phase_bindings": len(core_bindings),
        "xl_unparsed": len(structured["errors"]),
        "initial_xl_unparsed_resolved": len(entries["xl_unparsed"]),
        "literal_resource_references": len(refinement["literal_resource_references"]),
        "corrected_partial_literal_candidates": len(superseded_literals),
        "speech_api_candidate_lines": len(entries["speech_api_candidates"]),
        "indexed_archives": len(capture["archives"]),
        "archive_entries_without_depot_names": sum(row["unnamed_entries"] for row in capture["archives"]),
        "graph_provider_entries": len(census),
        "unique_graph_resource_keys": len(graph_unique),
        "unique_scene_resource_keys": len(scene_unique),
        "scene_keys_outside_reference_capture": len(outside_scene_keys),
        "captured_provider_payloads": len(resources),
        "captured_resource_depots": len(providers),
        "captured_native_scenes": len(native_scenes),
        "resource_queries": len({row["depot"] for row in resources + missing}) + len(additions["pending"]),
        "missing_candidates_raw": len(missing),
        "missing_candidates": len(effective_missing),
        "opaque_provider_payloads": len(opaque),
        "opaque_resource_depots": len(opaque_resources),
        "multiple_provider_depots": len(collisions),
        "pending_resource_queries": len(additions["pending"]),
        "additional_archive_locations": len(capture["additional_archive_locations"]),
        "archive_metadata_changes": len(capture["changed_archives"]) + len(additions["changed_archives"]),
        "input_discrepancies": discrepancies,
        "unfollowed_import_extensions": dict(unfollowed.most_common()),
        "bulk_capture": str(capture_path),
        "bulk_capture_sha256": sha256(capture_path),
        "supplemental_capture_sha256": sha256(OUTPUT / "capture_additions.json"),
        "task_tools": [
            {"path": str(path), "sha256": sha256(path)}
            for path in sorted(TASK.iterdir()) if path.suffix in {".py", ".ps1"}
        ],
        "game_writes": 0,
        "save_writes": 0,
    }
    summary["status"] = (
        "REFERENCE_CENSUS_COMPLETE_WITH_EXPLICIT_BOUNDARIES"
        if not discrepancies and not additions["pending"]
        and not capture["changed_archives"] and not additions["changed_archives"]
        and not structured["errors"] and not entries["text_read_errors"]
        else "REFERENCE_CENSUS_REQUIRES_FOLLOW_UP"
    )
    write_json(OUTPUT / "summary.json", summary)
    write_json(OUTPUT / "unresolved.json", {
        "missing_candidates": effective_missing,
        "superseded_partial_literal_candidates": sorted(superseded_literals),
        "opaque_provider_payloads": opaque,
        "multiple_provider_depots": collisions,
        "pending": additions["pending"],
        "xl_unparsed": structured["errors"],
        "text_read_errors": entries["text_read_errors"],
        "skipped_links": entries["skipped_links"],
        "additional_archive_locations": capture["additional_archive_locations"],
        "unfollowed_import_extensions": dict(unfollowed.most_common()),
        "limits": capture["limits"] + entries["limits"],
    })
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
