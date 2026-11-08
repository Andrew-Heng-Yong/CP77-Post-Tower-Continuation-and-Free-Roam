"""Copy bounded diagnostic evidence; never contact the game or write installed files/saves."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import re
import stat
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE = "PTFR_QR9_Diagnostics"
CAPTURE = re.compile(r"QR9_capture_\d{8}T\d{6}Z_\d{4,}\.jsonl\Z")
SUPPORT = {
    "ArchiveXL": ("red4ext/plugins/ArchiveXL", "ArchiveXL-*.log"),
    "REDscript": ("r6/logs", "redscript_r*.log"),
    "CET": ("bin/x64/plugins/cyber_engine_tweaks", "cyber_engine_tweaks.log"),
    "CET_scripting": ("bin/x64/plugins/cyber_engine_tweaks", "scripting.log"),
    "RED4ext": ("red4ext/logs", "red4ext-*.log"),
}


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest().upper()


def no_links(path):
    """Reject a symlink or Windows reparse point anywhere in an existing ancestry."""
    for part in (path, *path.parents):
        if part.exists() or part.is_symlink():
            st = part.lstat()
            if stat.S_ISLNK(st.st_mode) or getattr(st, "st_file_attributes", 0) & 0x400:
                raise ValueError(f"reparse/link refused: {part}")


def bounded_read(path, limit):
    no_links(path)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        raise ValueError(f"not a bounded regular file: {path}")
    with path.open("rb") as f:
        data = f.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"file grew beyond bound: {path}")
    after = path.stat()
    stable = (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    return data, {"path": str(path), "bytes": len(data), "sha256": sha_bytes(data),
                  "mtime_utc": dt.datetime.fromtimestamp(before.st_mtime, dt.timezone.utc).isoformat(),
                  "stable_during_read": stable,
                  "limit_bytes": limit}


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def nonfinite(value):
    raise ValueError("non-finite JSON number refused: " + value)


def analyze_capture(data, filename, card, expected_metadata=None):
    problems, rows = [], []
    if len(data) > 8388608:
        problems.append("capture exceeds logger byte bound")
    lines = data.splitlines()
    if len(lines) > 2048:
        problems.append("capture exceeds logger row bound")
    for i, line in enumerate(lines[:2049], 1):
        if len(line) > 131072:
            problems.append(f"oversized row {i}")
            continue
        try:
            row = json.loads(line, object_pairs_hook=unique_pairs, parse_constant=nonfinite)
            if not isinstance(row, dict):
                raise ValueError("row must be object")
            rows.append(row)
        except (ValueError, UnicodeDecodeError) as e:
            problems.append(f"invalid row {i}: {e}")
    for i, row in enumerate(rows, 1):
        if type(row.get("schema")) is not int or row.get("schema") != 1 or row.get("module") != MODULE or type(row.get("seq")) is not int or row.get("seq") != i:
            problems.append(f"schema/sequence mismatch at row {i}")
        if row.get("run_id") != filename or row.get("profile") != card:
            problems.append(f"capture identity/profile mismatch at row {i}")
        if not isinstance(row.get("data"), dict):
            problems.append(f"data must be object at row {i}")
            row["data"] = {}
        if not isinstance(row.get("event"), str):
            problems.append(f"event must be text at row {i}")
            row["event"] = "INVALID_EVENT"
    events = [r.get("event") for r in rows]
    if not events or events[0] != "CAPTURE_START" or events.count("CAPTURE_START") != 1:
        problems.append("missing or multiple CAPTURE_START")
    if events.count("STOP") != 1 or events.count("LISTENER_CLEANUP_CALLS") != 1:
        problems.append("missing or repeated STOP/cleanup; stop capture before collecting")
    elif events[-2:] != ["STOP", "LISTENER_CLEANUP_CALLS"]:
        problems.append("STOP/cleanup not terminal")
    cleanup = [r.get("data", {}) for r in rows if r.get("event") == "LISTENER_CLEANUP_CALLS"]
    if any(r.get("failures") != 0 for r in cleanup):
        problems.append("listener cleanup call failure or missing count")
    errors = [r for r in rows if r.get("event") in {
        "API_UNAVAILABLE", "FACT_READ_FAILED", "LISTENER_CALL_FAILED", "LOG_ERROR"}]
    if errors:
        problems.append("capture contains API/listener errors")
    if "ATTACHED_BASELINE" not in events or "LISTENER_CALLS_COMPLETED" not in events:
        problems.append("attached baseline or listener setup absent")
    metadata = "NOT_CHECKED"
    if expected_metadata is not None:
        start = rows[0].get("data", {}) if rows else {}
        declared = start.get("declared_build", {})
        if not isinstance(declared, dict):
            declared = {}
        matches = (start.get("version") == expected_metadata["version"]
                   and declared.get("source_lua_sha256") == expected_metadata["source_lua_sha256"])
        metadata = "MATCHING_DECLARATION_NOT_EXECUTED_BYTE_PROOF" if matches else "STALE_OR_MISSING_DECLARATION"
        if not matches:
            problems.append("capture declares an unexpected/missing addon version or source hash")
    counts = {event: events.count(event) for event in sorted(set(e for e in events if isinstance(e, str)))}
    return {"capture_integrity": "VALID_CAPTURE" if not problems else "INCOMPLETE_OR_INVALID_CAPTURE",
            "problems": problems, "rows": len(rows), "event_counts": counts,
            "first_utc": rows[0].get("utc") if rows else None,
            "last_utc": rows[-1].get("utc") if rows else None,
            "declared_addon_metadata": metadata,
            "stop_reasons": [r.get("data", {}).get("reason") for r in rows if r.get("event") == "STOP"],
            "unsupported": {k: "NOT_OBSERVED" for k in ["actual_graph_activation", "native_owner",
                "ArchiveXL_engine_receipt", "native_clock", "phone_queue", "actual_save_identity"]},
            "gameplay_result": "NOT_TESTED",
            "interpretation": "Integrity of recorded rows only. No gameplay PASS, graph activation or owner ACK is inferred."}


def hash_observation(path, expected):
    try:
        data, info = bounded_read(path, 64 * 1024 * 1024)
        return {**info, "expected": expected,
                "status": "MATCH" if info["stable_during_read"] and info["sha256"] == expected else "MISMATCH_OR_GROWING"}
    except (OSError, ValueError) as e:
        return {"path": str(path), "status": "UNAVAILABLE", "error": str(e), "expected": expected}


def collect(baseline, addon, output, card, log_name=None, expected_metadata=None):
    """Inputs injected only by offline tests; CLI loads pinned local configuration."""
    game = Path(baseline["game_root"])
    folder = game / "bin/x64/plugins/cyber_engine_tweaks/mods" / MODULE
    no_links(folder)
    if log_name:
        if not CAPTURE.fullmatch(log_name):
            raise ValueError("--log must be an exact diagnostic basename")
        capture = folder / log_name
    else:
        candidates = [p for p in folder.glob("QR9_capture_*.jsonl") if CAPTURE.fullmatch(p.name)]
        if not candidates:
            raise ValueError("No capture found; install diagnostics, perform card and stop capture first")
        capture = max(candidates, key=lambda p: p.stat().st_mtime_ns)
    data, info = bounded_read(capture, 8388608)
    analysis = analyze_capture(data, capture.name, card, expected_metadata)
    if not info["stable_during_read"]:
        analysis["problems"].append("capture changed during read; stop and recollect")
        analysis["capture_integrity"] = "INCOMPLETE_OR_INVALID_CAPTURE"
    no_links(output)
    if output.exists():
        raise ValueError("Fresh output directory required")
    output.mkdir(parents=True)
    (output / "logs").mkdir()
    (output / "logs" / capture.name).write_bytes(data)
    info["copy_sha256"] = sha_bytes((output / "logs" / capture.name).read_bytes())
    support = []
    snippets = []
    for label, (relative, pattern) in SUPPORT.items():
        source = game / relative
        no_links(source)
        candidates = sorted(source.glob(pattern), key=lambda p: p.stat().st_mtime_ns, reverse=True)[:2]
        if not candidates:
            support.append({"component": label, "status": "MISSING"})
        for j, p in enumerate(candidates):
            try:
                blob, item = bounded_read(p, 32 * 1024 * 1024)
                dest = output / "logs" / (label + "_" + str(j) + "_" + p.name)
                dest.write_bytes(blob)
                item.update(component=label, copy=str(dest), copy_sha256=sha_bytes(dest.read_bytes()),
                            run_alignment="NOT_VERIFIED: latest bounded candidates; inspect timestamps/header, not a gameplay result")
                for n, line in enumerate(blob.decode("utf-8", errors="replace").splitlines(), 1):
                    if re.search(r"Patching phase|merge|\[error\]|\[critical\]|failed|exception", line, re.I):
                        if len(snippets) < 200:
                            snippets.append({"component": label, "source": str(p), "line": n, "text": line[:1000]})
                support.append(item)
            except (OSError, ValueError) as e:
                support.append({"component": label, "path": str(p), "status": "UNAVAILABLE", "error": str(e)})
    pins = {
        "core": [hash_observation(game / r["path"], r["after"]) for r in baseline["core_files"]],
        "external_dependencies": [hash_observation(game / r["path"], r["sha256"]) for r in baseline["external_dependencies"]],
        "diagnostics": [hash_observation(game / r["path"], r["after"]) for r in addon],
    }
    master = load(Path(baseline["selected_master"]["path"]))
    pins["untouched_master"] = [hash_observation(Path(master["path"]) / name, row["sha256"])
                                for name, row in master["files"].items()]
    save(output / "capture_analysis.json", analysis)
    save(output / "resource_observations.json", pins)
    save(output / "support_log_candidates.json", support)
    save(output / "support_line_candidates.json", {"interpretation": "Text candidates for human analysis, including historical/stale lines. No automatic defect or success finding.", "rows": snippets})
    save(output / "human_result.json", {"card": card, "result": "NOT_TESTED", "working_save_slot": None,
         "variant": None, "visible_behavior": None, "approximate_time": None,
         "allowed_results": ["PASS", "FAIL", "NOT_TESTED", "NOT_TESTABLE", "INCONCLUSIVE"],
         "note": "User supplies short observation; Codex correlates logs. Collector cannot award gameplay PASS."})
    summary = {"schema": 1, "collected_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "card": card, "capture": info, "capture_integrity": analysis["capture_integrity"],
        "runtime_results": "NOT_TESTED_PENDING_HUMAN_REPORT", "game_calls": 0, "game_writes": 0, "save_writes": 0,
        "limits": "No sav.dat parsing, no save identity inference, no cross-load continuity or exact owner trace. Current hashes do not establish hashes earlier during capture.",
        "return": "Send this fresh directory and one line: card, actual working slot, visible result and approximate time."}
    save(output / "collection.json", summary)
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--card", choices=[f"S{i:02d}" for i in range(9)], default="S00")
    ap.add_argument("--log", help="exact capture basename; default newest candidate")
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", a.run_id):
        ap.error("run-id must be a short filename-safe new label")
    config = load(HERE / "collection_config.json")
    for row in config["pins"]:
        data, info = bounded_read(Path(row["path"]), 64 * 1024 * 1024)
        if not info["stable_during_read"] or sha_bytes(data) != row["sha256"]:
            raise ValueError(f"Pinned preparation input changed: {row['path']}")
    baseline = load(HERE / "baseline.json")
    output = HERE / "observations" / a.run_id
    summary = collect(baseline, config["diagnostic_files"], output, a.card, a.log, config["expected_capture_metadata"])
    print(json.dumps({"output": str(output), "capture_integrity": summary["capture_integrity"],
                      "runtime_results": summary["runtime_results"]}))


if __name__ == "__main__":
    main()
