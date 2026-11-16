"""Build the crash repair and automatic retained-history selection."""

from difflib import unified_diff
import importlib.util
from pathlib import Path
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
PRE = HERE.parent
BASE = PRE / "quest_history_test_20261112_01"
SAFE = PRE / "tower_evening_recovery_20261112_01"
BASELINE = BASE / "deployment_01/installed_manifest_01.json"
BASELINE_SHA = "520F72F9B8E4B3E68FC39398F0972F9AB5A5B015E0F3B182818A4A4E5A65F6EA"
SAFE_MANIFEST_SHA = "B8517BE830600D1832E5F1EDDC63D23450CF74612188FA8BC7234E6BDDD4FB69"
RED = "r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds"
LUA = "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua"
CHANGES = {RED, LUA}
CANDIDATE = HERE / "candidate_01"
PACKAGE = CANDIDATE / "package"
COMPILE = HERE / "compile_01"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def edit_script(safe, one):
    text = one(safe, "public class SnapshotStateHS1 extends ScriptableSystem {",
               "public class SnapshotStateHS1 extends ScriptableSystem {\n"
               + (HERE / "retained_history.reds").read_text(encoding="utf-8"))
    text = one(text, "this.jsonReadyHS2=false; this.Unregister();",
               "this.jsonReadyHS2=false; this.ResetRetainedHistory(); this.Unregister();")
    text = one(text, "public func Restored() -> Void {\n    this.jsonReadyHS2=false;",
               "public func Restored() -> Void {\n    this.jsonReadyHS2=false;this.ResetRetainedHistory();")
    text = one(text, 'this.previousRows=this.rows;this.ready=false;this.frozen=false;this.fileToken=n"";this.origin=n"";',
               'if NotEquals(this.origin,n"post_ending_fallback") || !this.Shape(this.previousRows) { this.previousRows=this.rows; }\n'
               '      this.ready=false;this.frozen=false;this.fileToken=n"";this.origin=n"";')
    text = one(text, 'NotEquals(this.origin,n"pre_ending") { return false; }',
               '(!this.useRetainedHistory && NotEquals(this.origin,n"pre_ending")) { return false; }')
    text = one(text, 'if i<0 || i>=ArraySize(this.rows) || !this.rows[i].stable { return false; }',
               'if !this.HasAdmissionRow(i) { return false; }\n'
               '  let row=this.rows[i];\n  if this.useRetainedHistory { row=this.previousRows[i]; }')
    start = text.index("\npublic func AllowsBrendanFinalQR13")
    stop = text.index("  private persistent let schema:", start)
    brendan = text[start:stop].replace("this.rows[i].states", "row.states").replace("this.rows[i].facts", "row.facts")
    text = text[:start] + brendan + text[stop:]
    text = one(text, "    if epoch!=this.epoch || revision!=this.revision || !this.CanExport() || Equals(token,\"\") { return false; }",
               '    return this.CommitFileAck(epoch,revision,token,false);\n  }\n\n'
               '  private func CommitFileAck(epoch: Int32,revision: Int32,token: String,useRetained: Bool) -> Bool {\n'
               '    if epoch!=this.epoch || revision!=this.revision || !this.CanExport() || Equals(token,"") { return false; }\n'
               '    this.useRetainedHistory=useRetained;')
    text = one(text, 'this.fileToken=StringToName(token);this.exported=true;this.detail="Snapshot JSON verified; restoration uses this save-local baseline.";return true;',
               'this.fileToken=StringToName(token);\n'
               '    this.detail=useRetained ? "Using verified retained pre-ending history for this session." : "Snapshot JSON verified; restoration uses this save-local baseline.";\n'
               '    this.exported=true;return true;')
    text = one(text, "if !this.Ready() || i<0 || i>=ArraySize(this.rows) { return false; }\n  return this.rows[i].stable && ArraySize(this.rows[i].states)>0 && this.rows[i].states[0]==1;",
               "return this.HasAdmissionRow(i) && this.AdmissionState(i,0)==1;")
    text = one(text, "if !this.Ready() || i<0 || !this.rows[i].stable || ArraySize(this.rows[i].states)==0 { return false; }",
               "if !this.HasAdmissionRow(i) { return false; }")
    text = one(text, "return this.rows[i].states[0]==1 || this.rows[i].states[0]==2;",
               "let state=this.AdmissionState(i,0);\n    return state==1 || state==2;")
    text = one(text, 'let i=SnapshotDataHS1.Index("sts_wbr_hil_06");if !this.Ready() || i<0 || !this.rows[i].stable { return false; }',
               'let i=SnapshotDataHS1.Index("sts_wbr_hil_06");if !this.HasAdmissionRow(i) { return false; }')
    for old, new in (
        ("this.rows[i].states[indices[k]]", "this.AdmissionState(i,indices[k])"),
        ("this.rows[i].facts[indices[k]]", "this.AdmissionFact(i,indices[k])"),
        ("prepared && this.rows[i].states[0]!=1", "prepared && this.AdmissionState(i,0)!=1"),
        ("root=this.rows[i].states[k]==3", "root=this.AdmissionState(i,k)==3"),
        ("done=this.rows[i].facts[k]>=1", "done=this.AdmissionFact(i,k)>=1"),
        ("rogue=this.rows[i].facts[k]>=1", "rogue=this.AdmissionFact(i,k)>=1"),
    ):
        text = one(text, old, new)
    text = one(text, "    let budget=0;\n    while budget<16 && this.jsonCursorHS2",
               '    if this.jsonCursorHS2==0 {\n'
               '      this.retainedHistoryCandidate=Equals(this.origin,n"post_ending_fallback") && this.Tower() && this.Shape(this.previousRows);\n'
               '    }\n    let budget=0;\n    while budget<16 && this.jsonCursorHS2')
    text = one(text, "ArrayPush(this.jsonRowsHS2,this.SerializeRowHS2(this.jsonCursorHS2));",
               "ArrayPush(this.jsonRowsHS2,this.SerializeRowHS2(this.jsonCursorHS2,false));\n"
               "      if this.retainedHistoryCandidate {\n"
               "        ArrayPush(this.retainedHistoryJSON,this.SerializeRowHS2(this.jsonCursorHS2,true));\n"
               "      }")
    text = one(text, "private func SerializeRowHS2(i: Int32) -> String {\n    let row=this.rows[i];",
               "private func SerializeRowHS2(i: Int32,retained: Bool) -> String {\n"
               "    let row=this.rows[i];\n    if retained { row=this.previousRows[i]; }")
    return text


def edit_lua(safe, one):
    text = one(safe, "local function same(s, w)",
               (HERE / "retained_history.lua").read_text(encoding="utf-8") + "\nlocal function same(s, w)")
    ack = 'assert(s:AckFile(w.epoch,w.revision,token), "Snapshot changed before acknowledgement")'
    assert text.count(ack) == 2
    text = text.replace(ack, "acknowledge(s, w, token)")
    text = one(text, '      assert(work.count==158 and work.parts[1]~="","Unexpected snapshot catalogue")',
               '      assert(work.count==158 and work.parts[1]~="","Unexpected snapshot catalogue")\n'
               '      work.retained = retainedComparison(s, work)')
    return one(text, "      work.parts[#work.parts+1]=row;work.index=work.index+1;n=n+1",
               '      work.parts[#work.parts+1]=row\n'
               '      if work.retained then\n'
               '        local retained = s:RetainedHistoryRowJSON(work.index)\n'
               '        if retained == "" then work.retained = nil\n'
               '        else\n'
               '          local parts = work.retained.parts\n'
               '          if work.index > 0 then parts[#parts+1] = "," end\n'
               '          parts[#parts+1] = retained\n'
               '        end\n'
               '      end\n'
               '      work.index=work.index+1;n=n+1')


def build():
    compiler = load_module(SAFE / "build.py", "registered_compile")
    sha, read, write, one = compiler.sha, compiler.read, compiler.write, compiler.one
    safe_manifest = SAFE / "deployment_01/installed_manifest_01.json"
    assert sha(BASELINE) == BASELINE_SHA and sha(safe_manifest) == SAFE_MANIFEST_SHA
    assert not CANDIDATE.exists() and not COMPILE.exists()
    baseline = read(BASELINE)
    game = Path(baseline["game_root"])
    for item in baseline["core_files"] + baseline["required_files"]:
        source = game / item["path"]
        compiler.common.plain(source, game)
        assert source.stat().st_size == item["bytes"] and sha(source) == item["sha256"], source
    safe_files = {item["path"]: item for item in read(safe_manifest)["core_files"]}
    originals = {}
    for name in CHANGES:
        source = SAFE / "candidate_01/package" / name
        assert sha(source) == safe_files[name]["sha256"]
        originals[name] = source.read_text(encoding="utf-8")
    edited = {RED: edit_script(originals[RED], one), LUA: edit_lua(originals[LUA], one)}
    assert re.findall(r"\bpersistent let [^;]+;", edited[RED]) == re.findall(r"\bpersistent let [^;]+;", originals[RED])
    patch = []
    for item in baseline["core_files"]:
        relative = item["path"]
        source = game / relative
        dest = PACKAGE / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if relative in edited:
            dest.write_text(edited[relative], encoding="utf-8", newline="\n")
            assert dest.read_text(encoding="utf-8") == edited[relative]
            patch.extend(unified_diff(source.read_text(encoding="utf-8").splitlines(keepends=True),
                                      edited[relative].splitlines(keepends=True), "a/" + relative, "b/" + relative))
        else:
            shutil.copyfile(source, dest)
            assert sha(dest) == item["sha256"]
    (CANDIDATE / "source.patch").write_text("".join(patch), encoding="utf-8", newline="\n")
    compiler.CHANGES = {RED}
    count = compiler.compile_overlay(game, PACKAGE, COMPILE)
    write(CANDIDATE / "verification.json", {
        "compile": "PASS", "registered_sources": count, "baseline_sha256": BASELINE_SHA,
        "overlay_sha256": {path: sha(PACKAGE / path) for path in sorted(CHANGES)},
    })
    print(f"Automatic history selection compiled with all {count} registered sources.")


if __name__ == "__main__":
    build()
