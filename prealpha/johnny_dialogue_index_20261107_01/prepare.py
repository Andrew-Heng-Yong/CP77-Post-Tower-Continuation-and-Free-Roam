"""Pin step 2 inputs and reconcile the full scene census with verified caches."""

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


TASK = Path(__file__).resolve().parent
WORKSPACE = TASK.parents[1]
PREVIOUS = WORKSPACE / "prealpha/johnny_dialogue_removal_20261107_01/step1_01"
OUTPUT = TASK / "evidence_01"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def write_json(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def resolve_path(value):
    path = Path(value)
    return path if path.is_absolute() else WORKSPACE / path


def identity(archive, key):
    value = str(Path(archive)).casefold() + "|" + str(key)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def main():
    if OUTPUT.exists():
        raise SystemExit("Use a fresh preparation output")
    capture_path = PREVIOUS / "capture.json"
    capture = read_json(capture_path)
    additions = read_json(PREVIOUS / "capture_additions.json")
    previous_summary = read_json(PREVIOUS / "summary.json")
    if sha256(capture_path) != previous_summary["bulk_capture_sha256"]:
        raise SystemExit("Step 1 capture hash changed")
    if sha256(PREVIOUS / "capture_additions.json") != previous_summary["supplemental_capture_sha256"]:
        raise SystemExit("Step 1 supplemental capture hash changed")
    installed_manifest = resolve_path(previous_summary["installed_manifest"])
    if sha256(installed_manifest) != previous_summary["installed_manifest_sha256"]:
        raise SystemExit("The selected installed manifest changed")
    manifest = read_json(installed_manifest)
    game = Path(manifest["game_root"])
    checks = []
    for row in manifest["core_files"] + manifest["required_files"]:
        path = game / row["path"]
        actual = sha256(path) if path.is_file() else None
        checks.append({"path": str(path), "expected": row["sha256"], "sha256": actual})
    entries = read_json(PREVIOUS / "entry_sources.json")
    for row in entries["source_files"]:
        path = Path(row["path"])
        actual = sha256(path) if path.is_file() else None
        checks.append({"path": str(path), "expected": row["sha256"], "sha256": actual})
    discrepancies = [row for row in checks if row["expected"] != row["sha256"]]
    if discrepancies:
        raise SystemExit(f"Current input discrepancies {discrepancies[:3]}")

    captured = {
        (row["archive"].casefold(), row["key"]): row
        for row in capture["resources"] + additions["resources"]
    }
    caches = defaultdict(list)
    cache_manifests = [
        WORKSPACE / "diagnostics/vanilla_parity_20261029_01/pass_05/capture.json",
        *sorted((WORKSPACE / "research/sidejobs_s29").glob("native_*/inventory.json")),
    ]
    cache_manifest_pins = []
    for path in cache_manifests:
        if not path.is_file():
            continue
        document = read_json(path)
        cache_manifest_pins.append({"path": str(path), "sha256": sha256(path)})
        for row in document.get("resources", document.get("rows", [])):
            if not row.get("depot", "").endswith(".scene"):
                continue
            if not all(row.get(key) for key in ("sha256", "raw", "json", "json_sha256")):
                continue
            caches[row["sha256"]].append(row)

    hash_cache = {}

    def checked_hash(path):
        if path not in hash_cache:
            hash_cache[path] = sha256(path) if path.is_file() else None
        return hash_cache[path]

    scenes = []
    for row in capture["graph_provider_census"]:
        if row["extension"] != ".scene":
            continue
        archive = capture["archives"][row["archive_index"]]["path"]
        source = captured.get((archive.casefold(), row["key"]))
        result = {
            "resource_id": identity(archive, row["key"]),
            "key": row["key"],
            "depot": row["depot"],
            "archive": archive,
            "archive_index": row["archive_index"],
            "provider_role": row["role"],
            "scope": "REFERENCE_CENSUS" if source else "GLOBAL_CENSUS_UNCLASSIFIED",
            "raw": source["raw"] if source else None,
            "sha256": source["sha256"] if source else None,
            "cached_json": None,
        }
        if source:
            if checked_hash(Path(source["raw"])) != source["sha256"]:
                raise SystemExit(f"Pinned raw scene changed {source['raw']}")
            for cached in caches[source["sha256"]]:
                raw_path = resolve_path(cached["raw"])
                json_path = resolve_path(cached["json"])
                if checked_hash(raw_path) != source["sha256"]:
                    continue
                if checked_hash(json_path) != cached["json_sha256"]:
                    continue
                result["cached_json"] = {
                    "path": str(json_path),
                    "sha256": cached["json_sha256"],
                    "source_raw": str(raw_path),
                    "source_raw_sha256": cached["sha256"],
                }
                break
        if Path(archive).name == "zzzz_PTFR_Combined.archive":
            result["scope"] = "CURRENT_PTFR_PAYLOAD"
        scenes.append(result)
    if len({row["resource_id"] for row in scenes}) != len(scenes):
        raise SystemExit("Duplicate scene provider identity")

    dependency_inventory = read_json(PREVIOUS / "dependency_inventory.json")
    conversations = sorted({
        row["target"] for row in dependency_inventory["references"]
        if row["target"].endswith(".conversations")
    })
    OUTPUT.mkdir()
    write_json(OUTPUT / "prepared.json", {
        "schema": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "installed_manifest": str(installed_manifest),
        "installed_manifest_sha256": sha256(installed_manifest),
        "game_root": str(game),
        "checks": checks,
        "step1_summary": str(PREVIOUS / "summary.json"),
        "step1_summary_sha256": sha256(PREVIOUS / "summary.json"),
        "cache_manifests": cache_manifest_pins,
        "scenes": scenes,
        "conversation_seeds": conversations,
        "archives": capture["archives"],
        "speech_api_candidates": entries["speech_api_candidates"],
        "speech_source_files": entries["source_files"],
        "limits": [
            "The full scene census includes pre-Tower and unavailable branches. Runtime scope remains a later review.",
            "Cached JSON is accepted only with matching current raw bytes and pinned JSON hashes.",
            "Multiple providers remain separate records.",
        ],
    })
    summary = {
        "status": "PREPARED",
        "installed_paths_verified": len(manifest["core_files"]) + len(manifest["required_files"]),
        "runtime_source_files_verified": len(entries["source_files"]),
        "scene_provider_inputs": len(scenes),
        "pinned_raw_scene_inputs": sum(bool(row["raw"]) for row in scenes),
        "verified_scene_json_caches": sum(bool(row["cached_json"]) for row in scenes),
        "scope_counts": dict(Counter(row["scope"] for row in scenes)),
        "conversation_seeds": len(conversations),
    }
    write_json(TASK / "preparation.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
