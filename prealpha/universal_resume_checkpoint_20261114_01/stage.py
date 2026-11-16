"""Build a source overlay and compile the full RD10 registry in a fresh directory."""

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
LUA = "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua"
COMPILER = "engine/tools/scc.exe"
CACHE = "r6/cache/final.redscripts"
CACHE_TS = "r6/cache/final.redscripts.ts"
REGISTRY = "r6/logs/redscript_rCURRENT.log"
MANIFEST_SHA = "AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8"
ARCHIVE_SHA = "443339C64009C5DB99B1E0FD77B1EF526143C40DADDBEBB05EBEC6BB5D76BB45"
ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"
READBACK_SHA = "5BBD9BB8F04AA5CC235B9845BDE691E2D6105B70E98083B36D7A8F54A3B29B81"
GATES = {
    r"ep1\quest\main_quests\q307\phases\q307_01_pickup.questphase":
        "2D56158D0E8DA10DEE6A8706C9A8372ECC9AF650DBB3B20DB4925536ED091F14",
    r"base\quest\main_quests\part1\q115\phases\q115_00_hanako.questphase":
        "8285EDBD3F2B28A4D1EA806D559F51A7C22370E665DD52B8835AAECD228EF304",
}


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Expected one exact anchor {old!r}")
    return text.replace(old, new, 1)


def change(source, edits):
    newline = "\r\n" if b"\r\n" in source else "\n"
    text = source.decode("utf-8").replace("\r\n", "\n")
    revised = text
    for old, new in edits:
        revised = once(revised, old, new)
    reverted = revised
    for old, new in reversed(edits):
        reverted = once(reverted, new, old)
    assert text == reverted
    return revised.replace("\n", newline).encode("utf-8")


def overlay_red(source):
    declaration = (
        "public static native func ReadExecutionCheckpoint(quests: ref<QuestsSystem>, "
        "delay: ref<DelaySystem>, clock: ref<TimeSystem>, ticket: Int32, route: Int32, "
        "historyRevision: Int32, presentation: array<Uint64>) -> array<Uint64>\n"
        "public static native func DecodeExecutionCheckpoint(data: array<Uint64>) -> String\n\n"
    )
    members = (HERE / "checkpoint_members.reds").read_text(encoding="utf-8")
    anchor = "public class CaptureArchiveHS3 extends ScriptableSystem {\n"
    reset = "    this.pendingTicket=0;this.pendingRoute=0;this.cursor=0;this.pass=0;\n"
    prime = "    let budget=0;let jr: CaptureJournalHS3;let vr: CaptureValueHS3;let actual: Int32;let index: Int32;"
    admission = "    if this.revision>=2147483647 || !legacy.CaptureNativeHS3(ticket,route) { this.ResetCapture();return; }\n"
    attempt = """    if this.revision>=2147483647 { this.ResetCapture();return; }
    let execution = this.ReadExecution(ticket,route,this.revision+1,this.ReadExecutionPresentation(player));
    if ArraySize(execution)==0 && this.executionCheckpointAttempts<2 {
      this.executionCheckpointAttempts+=1;
      return;
    }
    if !this.GateOpen(ticket,route) || jm.HasAnyDelayedStateChanges() || !legacy.CaptureNativeHS3(ticket,route) {
      this.ResetCapture();return;
    }
"""
    commit = '    this.detail="Save-local history committed before native cleanup; recovery export pending.";'
    updated = change(source, [
        (anchor, declaration + anchor + members),
        (reset, reset + "    this.executionCheckpointAttempts=0;\n"),
        (prime, "    if this.pass==2 && this.cursor % 4096 == 0 { this.PrimeExecutionCheckpoint(ticket,route); }\n" + prime),
        (admission, attempt),
        (commit, "    this.StoreExecutionCheckpoint(ticket,route,execution);\n" + commit),
    ])
    before = re.findall(rb"\bpersistent let \S+:[^;]+;", source)
    after = re.findall(rb"\bpersistent let \S+:[^;]+;", updated)
    assert [line for line in after if not line.startswith(b"persistent let executionCheckpoint")] == before
    ack = b'SetFact(n"PTFRHS3_GateResult",1)'
    assert updated.count(ack) == source.count(ack) == 2
    assert updated.index(b"this.StoreExecutionCheckpoint(ticket,route,execution);") < updated.rindex(ack)
    return updated


def overlay_lua(source):
    sink = 'local function finish(c,s,w)\n'
    original_write = """    local file=assert(io.open(temp,"wb"),"Cannot create snapshot temporary file")
    local wrote,flushed
    local ok,err=pcall(function() wrote=file:write(data);flushed=file:flush() end)
    local closed=file:close()
    assert(ok and wrote and flushed and closed,tostring(err or "Snapshot write/flush/close failed"))
    assert(read(temp)==data,"Snapshot temporary readback mismatch")
    if not same(s,w) then return end
    assert(not read(path),"Snapshot destination appeared")
    assert(os.rename(temp,path),"Snapshot rename failed")
    assert(read(path)==data,"Snapshot committed readback mismatch")
"""
    update = 'registerForEvent("onUpdate",function(dt)\n'
    dispatch = "  time=time+dt;if not latestUpdate() then for _,c in ipairs(channels) do update(c) end end\n"
    return change(source, [
        (sink, (HERE / "verified_write.lua").read_text(encoding="utf-8") + sink),
        (original_write, "    if not writeVerified(path,temp,data,function() return same(s,w) end) then return end\n"),
        (update, (HERE / "checkpoint_export.lua").read_text(encoding="utf-8") + update),
        (dispatch, dispatch + "  checkpointUpdate()\n"),
    ])


def baseline():
    path = RD10 / "deployment_01/installed_manifest_01.json"
    assert sha(path) == MANIFEST_SHA
    manifest = json.loads(path.read_bytes())
    game = Path(manifest["game_root"])
    readback_path = RD10 / "archive_01/readback.json"
    assert sha(readback_path) == READBACK_SHA
    readback = json.loads(readback_path.read_bytes())
    assert readback["archive_sha256"] == manifest["archive_sha256"] == ARCHIVE_SHA
    for depot, expected in GATES.items():
        row, = (item for item in readback["members"] if item["depot"] == depot)
        assert row["sha256"] == expected == sha(RD10 / "archive_01/source" / depot)
    paths = {row["path"]: row["sha256"] for row in manifest["core_files"]}
    assert len(paths) == 51 and paths[ARCHIVE] == ARCHIVE_SHA
    required = {row["path"]: row["sha256"] for row in manifest["required_files"]}
    assert len(required) == 26 and not set(required) & set(paths)
    paths.update(required)
    assert all(sha(game / rel) == digest for rel, digest in paths.items())
    return game, paths


def run(attempt, prepare_only):
    game, core = baseline()
    out = HERE / f"compile_{attempt:02d}"
    out.mkdir(exist_ok=False)
    lua = overlay_lua((game / LUA).read_bytes())
    (out / "init.lua").write_bytes(lua)

    log = (game / REGISTRY).read_text(encoding="utf-8-sig")
    registered = {(game / "r6/scripts" / line.strip()).resolve() for line in log.splitlines()
                  if line.strip().lower().endswith(".reds")}
    sources = {path.relative_to(game).as_posix() for rel in ("r6/scripts", "red4ext/plugins")
               for path in (game / rel).rglob("*.reds")}
    assert "Compilation complete" in log and registered == {(game / path).resolve() for path in sources}
    rd9 = HERE.parent / "resume_dispatcher_rd9_kirk_20261113_01/compile_01/result.json"
    previous = json.loads(rd9.read_bytes())["staged_hashes"]
    assert sources == set(previous) and len(sources) == 148 and HISTORY in sources
    pins = {rel: sha(game / rel) for rel in sorted({REGISTRY, COMPILER, CACHE, CACHE_TS} | sources)}
    assert all(previous[rel] == pins[rel] for rel in previous)
    assert pins[HISTORY] == core[HISTORY]
    cache = out / "cache"
    cache.mkdir()
    for rel in (CACHE, CACHE_TS):
        shutil.copyfile(game / rel, cache / Path(rel).name)
    staged = {}
    for rel in sorted(sources):
        target = out / "scripts" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if rel == HISTORY:
            target.write_bytes(overlay_red((game / rel).read_bytes()))
        else:
            shutil.copyfile(game / rel, target)
        staged[rel] = sha(target)
    assert [rel for rel in staged if staged[rel] != pins[rel]] == [HISTORY]
    if prepare_only:
        return
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
    assert all(sha(game / rel) == digest for rel, digest in core.items())
    assert result.returncode == 0 and "Compilation complete" in compiler_log and assembled.is_file(), compiler_log[-6000:]
    receipt = {
        "status": "WORKSPACE_EXECUTION_CHECKPOINT_COMPILED",
        "installed_manifest_sha256": MANIFEST_SHA,
        "archive_sha256": ARCHIVE_SHA,
        "archive_readback_sha256": READBACK_SHA,
        "cutoff_members_sha256": GATES,
        "source_count": len(staged),
        "staged_redscript": {HISTORY: staged[HISTORY]},
        "staged_lua": {LUA: sha(out / "init.lua")},
        "compiled_sha256": sha(assembled),
        "compiler_inputs": pins,
        "installed_core": core,
        "game_writes": 0,
    }
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Compiled {len(staged)} sources with one changed REDscript file. Verified {len(core)} installed paths.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--prepare-only", action="store_true")
    options = parser.parse_args()
    run(options.attempt, options.prepare_only)
