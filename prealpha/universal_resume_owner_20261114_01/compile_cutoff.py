"""Compile a workspace-only history overlay against the installed RD10 inventory."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
RD10 = HERE.parent / "resume_dispatcher_rd10_kirk_20261113_01"
HISTORY = "r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds"
COMPILER = "engine/tools/scc.exe"
CACHE = "r6/cache/final.redscripts"
CACHE_TS = "r6/cache/final.redscripts.ts"
REGISTRY = "r6/logs/redscript_rCURRENT.log"
MANIFEST_SHA = "AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8"
ARCHIVE_SHA = "443339C64009C5DB99B1E0FD77B1EF526143C40DADDBEBB05EBEC6BB5D76BB45"
GATES = {
    r"ep1\quest\main_quests\q307\phases\q307_01_pickup.questphase":
        "2D56158D0E8DA10DEE6A8706C9A8372ECC9AF650DBB3B20DB4925536ED091F14",
    r"base\quest\main_quests\part1\q115\phases\q115_00_hanako.questphase":
        "8285EDBD3F2B28A4D1EA806D559F51A7C22370E665DD52B8835AAECD228EF304",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError(f"Expected one occurrence of {before!r}")
    return text.replace(before, after, 1)


def overlay(source):
    newline = "\r\n" if b"\r\n" in source else "\n"
    text = source.decode("utf-8").replace("\r\n", "\n")
    declaration = (
        "public static native func ReadNativeWaitAtCutoff(quests: ref<QuestsSystem>, "
        "ticket: Int32, node: Uint64) -> Float\n\n"
    )
    members = (HERE / "cutoff_members.reds").read_text(encoding="utf-8")
    node, = re.findall(r"let node: Uint64 = (\d+)ul;", members)
    assert int(node) == 0x9A66DFB600000045
    anchor = "public class CaptureArchiveHS3 extends ScriptableSystem {\n"
    native_commit = '    this.detail="Save-local history committed before native cleanup; recovery export pending.";'
    old_ack = '    GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(n"PTFRHS3_GateResult",1);'
    revised = replace_once(text, anchor, declaration + anchor + members)
    revised = replace_once(revised, native_commit, "    this.CaptureNativeWait(ticket,route);\n" + native_commit)
    assert revised.replace(declaration + anchor + members, anchor, 1).replace(
        "    this.CaptureNativeWait(ticket,route);\n" + native_commit, native_commit, 1
    ) == text
    assert revised.count(old_ack) == text.count(old_ack) == 2
    assert revised.index("    this.CaptureNativeWait(ticket,route);") < revised.rindex(old_ack)
    original_fields = re.findall(r"\bpersistent let \S+:[^;]+;", text)
    new_fields = re.findall(r"\bpersistent let \S+:[^;]+;", revised)
    assert [field for field in new_fields if not field.startswith("persistent let timerSample")] == original_fields
    assert len(new_fields) == len(original_fields) + 4
    previous = (HERE.parent / "universal_resume_handoff_20261114_01/cutoff_members.reds").read_text(encoding="utf-8")
    assert [field for field in new_fields if field.startswith("persistent let timerSample")] == re.findall(
        r"\bpersistent let \S+:[^;]+;", previous)
    return revised.replace("\n", newline).encode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    out = HERE / f"compile_{args.attempt:02d}"
    manifest_path = RD10 / "deployment_01/installed_manifest_01.json"
    assert sha(manifest_path) == MANIFEST_SHA
    manifest = json.loads(manifest_path.read_bytes())
    game = Path(manifest["game_root"])
    archive = game / "archive/pc/mod/zzzz_PTFR_Combined.archive"
    assert sha(archive) == manifest["archive_sha256"] == ARCHIVE_SHA
    readback = json.loads((RD10 / "archive_01/readback.json").read_bytes())
    assert readback["archive_sha256"] == ARCHIVE_SHA
    for depot, digest in GATES.items():
        member, = (row for row in readback["members"] if row["depot"] == depot)
        assert member["sha256"] == digest == sha(RD10 / "archive_01/source" / depot)

    registry = game / REGISTRY
    log = registry.read_text(encoding="utf-8-sig")
    registered = {(game / "r6/scripts" / line.strip()).resolve() for line in log.splitlines()
                  if line.strip().lower().endswith(".reds")}
    sources = {path.relative_to(game).as_posix() for root in ("r6/scripts", "red4ext/plugins")
               for path in (game / root).rglob("*.reds")}
    assert "Compilation complete" in log and registered == {(game / path).resolve() for path in sources}
    baseline = HERE.parent / "resume_dispatcher_rd9_kirk_20261113_01/compile_01/result.json"
    confirmed = json.loads(baseline.read_bytes())["staged_hashes"]
    assert sources == set(confirmed) and len(sources) == 148 and HISTORY in sources
    pins = {rel: sha(game / rel) for rel in sorted({REGISTRY, COMPILER, CACHE, CACHE_TS} | sources)}
    assert all(confirmed[rel] == pins[rel] for rel in confirmed)
    history, = (row for row in manifest["core_files"] if row["path"] == HISTORY)
    assert pins[HISTORY] == history["sha256"]

    cache = out / "cache"
    cache.mkdir(parents=True, exist_ok=False)
    for rel in (CACHE, CACHE_TS):
        shutil.copyfile(game / rel, cache / Path(rel).name)
    staged = {}
    for rel in sorted(sources):
        target = out / "scripts" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if rel == HISTORY:
            target.write_bytes(overlay((game / rel).read_bytes()))
        else:
            shutil.copyfile(game / rel, target)
        staged[rel] = sha(target)
    assert [rel for rel in staged if staged[rel] != pins[rel]] == [HISTORY]
    paths = out / "compile_paths.txt"
    paths.write_bytes(b"")
    assembled = cache / "compiled.redscripts"
    command = [game / COMPILER, "-compile", out / "scripts", "-compilePathsFile", paths,
               "-customCacheDir", cache, "-outputCacheFile", assembled, cache / "final.redscripts"]
    result = subprocess.run(list(map(str, command)), capture_output=True, encoding="utf-8", errors="replace",
                            timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    compiler_log = result.stdout + result.stderr
    (out / "scc.log").write_text(compiler_log, encoding="utf-8")
    assert all(sha(game / rel) == digest for rel, digest in pins.items())
    assert sha(archive) == ARCHIVE_SHA
    assert result.returncode == 0 and "Compilation complete" in compiler_log and assembled.is_file(), compiler_log[-6000:]
    receipt = {
        "status": "WORKSPACE_CUTOFF_OVERLAY_COMPILED",
        "manifest_sha256": MANIFEST_SHA,
        "archive_sha256": ARCHIVE_SHA,
        "gates": GATES,
        "source_count": len(staged),
        "changed_source": HISTORY,
        "source_sha256": staged[HISTORY],
        "compiled_sha256": sha(assembled),
        "input_pins": pins,
        "game_writes": 0,
    }
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Compiled the cutoff overlay against all {len(staged)} registered sources.")


if __name__ == "__main__":
    main()
