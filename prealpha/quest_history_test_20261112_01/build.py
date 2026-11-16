"""Stage the local, opt-in quest-history test."""

from difflib import unified_diff
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PRE = HERE.parent
BASE = PRE / "tower_evening_recovery_20261112_01"
BASELINE = BASE / "deployment_01/installed_manifest_01.json"
BASELINE_SHA = "B8517BE830600D1832E5F1EDDC63D23450CF74612188FA8BC7234E6BDDD4FB69"
RED = "r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds"
LUA = "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua"
CHANGES = {RED, LUA}
CANDIDATE = HERE / "candidate_02"
PACKAGE = CANDIDATE / "package"
COMPILE = HERE / "compile_02"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def edit_script(text, one):
    text = one(text, "public class SnapshotStateHS1 extends ScriptableSystem {",
               (HERE / "history_test.reds").read_text(encoding="utf-8")
               + "public class SnapshotStateHS1 extends ScriptableSystem {\n"
               + (HERE / "history_test_members.reds").read_text(encoding="utf-8"))
    text = one(text, "this.jsonReadyHS2=false; this.Unregister();", "this.jsonReadyHS2=false; this.ClearTestHistory(); this.Unregister();")
    text = one(text, "public func Restored() -> Void {\n    this.jsonReadyHS2=false;",
               "public func Restored() -> Void {\n    this.jsonReadyHS2=false;this.ClearTestHistory();")
    text = one(text, 'this.previousRows=this.rows;this.ready=false;this.frozen=false;this.fileToken=n"";this.origin=n"";',
               'if NotEquals(this.origin,n"post_ending_fallback") || !this.Shape(this.previousRows) { this.previousRows=this.rows; }\n'
               '      this.ready=false;this.frozen=false;this.fileToken=n"";this.origin=n"";')
    text = one(text, "if this.frozen { this.PrepareJSONHS2(); return; }",
               "if this.frozen { this.PrepareJSONHS2(); this.CheckTestHistory(); return; }")
    text = one(text, 'NotEquals(this.origin,n"pre_ending") { return false; }',
               '(this.testHistoryRevision==0 && NotEquals(this.origin,n"pre_ending")) { return false; }')
    for start, end in (
        ("\npublic func AllowsBrendanFinalQR13", "  private persistent let schema:"),
        ("\npublic func FreshS29", "  private func IntJSON"),
    ):
        left = text.index(start)
        right = text.index(end, left)
        section = text[left:right]
        assert "this.rows[i]" in section
        text = text[:left] + section.replace("this.rows[i]", "this.AdmissionRow(i)") + text[right:]
    text = one(text, "this.SerializeRowHS2(this.jsonCursorHS2)", "this.SerializeRowHS2(this.jsonCursorHS2,this.rows[this.jsonCursorHS2])")
    return one(text, "private func SerializeRowHS2(i: Int32) -> String {\n    let row=this.rows[i];",
               "private func SerializeRowHS2(i: Int32,row: SnapshotRowHS1) -> String {")


def build():
    compiler = load_module(BASE / "build.py", "registered_compile")
    sha, read, write, one = compiler.sha, compiler.read, compiler.write, compiler.one
    assert sha(BASELINE) == BASELINE_SHA
    assert not CANDIDATE.exists() and not COMPILE.exists()
    baseline = read(BASELINE)
    game = Path(baseline["game_root"])
    for item in baseline["core_files"] + baseline["required_files"]:
        path = game / item["path"]
        compiler.common.plain(path, game)
        assert path.stat().st_size == item["bytes"] and sha(path) == item["sha256"], path
    original = {name: (game / name).read_text(encoding="utf-8") for name in CHANGES}
    lua = one(original[LUA], "function api.Status()", (HERE / "history_test.lua").read_text(encoding="utf-8") + "\nfunction api.Status()")
    edited = {RED: edit_script(original[RED], one), LUA: lua}
    patch = []
    for item in baseline["core_files"]:
        relative = item["path"]
        dest = PACKAGE / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if relative in edited:
            dest.write_text(edited[relative], encoding="utf-8", newline="\n")
            assert dest.read_text(encoding="utf-8") == edited[relative]
            patch.extend(unified_diff(original[relative].splitlines(keepends=True),
                                      edited[relative].splitlines(keepends=True), "a/" + relative, "b/" + relative))
        else:
            dest.write_bytes((game / relative).read_bytes())
            assert sha(dest) == item["sha256"]
    (CANDIDATE / "source.patch").write_text("".join(patch), encoding="utf-8", newline="\n")
    compiler.CHANGES = {RED}
    count = compiler.compile_overlay(game, PACKAGE, COMPILE)
    write(CANDIDATE / "verification.json", {
        "compile": "PASS", "registered_sources": count, "baseline_sha256": BASELINE_SHA,
        "overlay_sha256": {path: sha(PACKAGE / path) for path in sorted(CHANGES)},
    })
    print(f"Test overlay compiled with all {count} registered sources.")


if __name__ == "__main__":
    build()
