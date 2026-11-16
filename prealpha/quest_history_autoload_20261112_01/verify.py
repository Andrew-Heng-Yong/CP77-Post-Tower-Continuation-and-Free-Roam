"""Exercise the installed exporter protocol and guard the faulting source path."""

import json
import re
import sys
from pathlib import Path

from build import BASELINE, CANDIDATE, HERE, LUA, PACKAGE, RED, SAFE, load_module

helper = load_module(SAFE / "build.py", "verification_helpers")
game = Path(helper.read(BASELINE)["game_root"])
exports = (game / LUA).parent
pre_name = "snapshot_hs1_20261111T224622Z_159_1.json"
pre_file = exports / pre_name
fallback_file = exports / "snapshot_hs1_20261112T171055Z_161_1.json"
assert helper.sha(pre_file) == "F1CBD023E336F7A4173BF3700E5FCB0B9667CE5924FBE00C35D81A253E82B0B0"
before = (game / RED).read_text(encoding="utf-8")
staged = (PACKAGE / RED).read_text(encoding="utf-8")
assert "this.AdmissionRow(i).states[0]" in before
assert "func AdmissionRow(" not in staged and "this.AdmissionRow(" not in staged
assert "return this.previousRows[i].states[field];" in staged
assert "return this.rows[i].states[field];" in staged
assert "return this.previousRows[i].facts[field];" in staged
assert "return this.rows[i].facts[field];" in staged
assert re.findall(r"\bpersistent let [^;]+;", before) == re.findall(r"\bpersistent let [^;]+;", staged)
assert 'Equals(this.origin,n"post_ending_fallback") && this.Tower() && this.Shape(this.previousRows)' in staged
commit = staged.split("private func CommitFileAck(", 1)[1].split("public func ReportIOFailure", 1)[0]
assert commit.index("this.useRetainedHistory=useRetained;") < commit.index("this.exported=true;")
assert "private func ResetRetainedHistory()" in staged and staged.count("this.ResetRetainedHistory()") == 2

sys.path.insert(0, str(HERE.parent / "quest_restoration_qr9/worker_b/tooling"))
from lupa.luajit21 import LuaRuntime

lua_source = (PACKAGE / LUA).read_text(encoding="utf-8")
assert "UsePreEndingForTest" not in lua_source
pre = pre_file.read_bytes().decode("utf-8")
fallback = fallback_file.read_bytes().decode("utf-8")


def raw_rows(document):
    start = document.index(',"rows":[') + len(',"rows":[')
    header = document[:start]
    rows = []
    while document[start] == "{":
        _, end = json.JSONDecoder().raw_decode(document, start)
        rows.append(document[start:end])
        if document[end] != ",":
            assert document[end:] == "]}\n"
            return header, rows
        start = end + 1
    raise AssertionError("Export has no rows")


def fixture(canonical=fallback, retained=pre, offered=pre, candidate=True, token=""):
    header, rows = raw_rows(canonical)
    retained_rows = raw_rows(retained)[1]
    lua = LuaRuntime(unpack_returned_tuples=True)
    globals_ = lua.globals()
    globals_.files = lua.table()
    if offered is not None:
        globals_.files[pre_name] = offered
    if token:
        globals_.files["snapshot_hs1_" + token + ".json"] = canonical
    globals_.header = header
    globals_.rows = lua.table_from(rows)
    globals_.retainedRows = lua.table_from(retained_rows)
    globals_.revision = json.loads(canonical)["revision"]
    globals_.token = token
    globals_.candidate = candidate
    globals_.decode = lambda data: lua.table_from(json.loads(data), recursive=True)
    lua.execute("""
events, messages, acknowledgements = {}, {}, {}
epoch, attached, pregame, exported, canExport = 4, true, false, false, true
registerForEvent = function(name, fn) events[name] = fn end
print = function(msg) messages[#messages+1] = msg end
json = {decode = decode}
os.date = function() return "20261112T170000Z" end
os.rename = function(src, dst) files[dst], files[src] = files[src], nil return true end
io.open = function(name, mode)
  if mode == "wb" then
    return {write = function(_, data) files[name] = data return true end,
      flush = function() return true end, close = function() return true end}
  end
  if not files[name] then return nil end
  return {read = function() return files[name] end, close = function() return true end}
end
local function ack(ackEpoch, ackRevision, ackToken, previous)
  assert(ackEpoch == epoch and ackRevision == revision)
  assert(files["snapshot_hs1_" .. ackToken .. ".json"])
  acknowledgements[#acknowledgements+1] = previous or false
  exported = true
  return true
end
local s = {
  Epoch = function() return epoch end,
  Revision = function() return revision end,
  Count = function() return 158 end,
  CanExport = function() return canExport end,
  Exported = function() return exported end,
  HeaderJSON = function() return header end,
  RowJSON = function(_, i) return rows[i+1] end,
  FileToken = function() return token end,
  CanCompareRetainedHistory = function() return candidate end,
  RetainedHistoryRowJSON = function(_, i) return retainedRows[i+1] end,
  AckFile = function(_, ...) return ack(...) end,
  AckFileWithRetainedHistory = function(_, ...) return ack(...) end,
  ReportIOFailure = function() failures = (failures or 0)+1 end,
}
Game = {
  GetPlayer = function() return {IsAttached = function() return attached end} end,
  GetSystemRequestsHandler = function() return {IsPreGame = function() return pregame end} end,
  GetScriptableSystemsContainer = function() return {Get = function() return s end} end,
}
""")
    lua.execute(lua_source)
    return globals_


def drive(g, ticks=12):
    for _ in range(ticks):
        g.events["onUpdate"](0.1)


checks = []
g = fixture()
g.canExport = False
drive(g)
assert len(g.acknowledgements) == 0
g.canExport = True
drive(g, 9)
assert len(g.acknowledgements) == 0
drive(g, 1)
assert len(g.acknowledgements) == 1 and g.acknowledgements[1] == 159
assert "Using verified pre-ending revision 159" in g.messages[1]
assert g.files["snapshot_hs1_20261112T170000Z_161_1.json"] == fallback
assert g.files[pre_name] == pre and g.failures is None
checks.append("auto select revision 159 on first canonical acknowledgement, before admissions")

g = fixture(token="existing")
drive(g)
assert len(g.acknowledgements) == 1 and g.acknowledgements[1] == 159 and g.failures is None
assert g.files["snapshot_hs1_20261112T170000Z_161_1.json"] is None
checks.append("matching existing fallback export reused")

for name, g in (
    ("retained row differs", fixture(retained=fallback)),
    ("pre-ending export missing", fixture(offered=None)),
    ("pre-ending catalogue differs", fixture(offered=pre.replace(json.loads(pre)["catalogue"], "different", 1))),
    ("unrelated load has no retained candidate", fixture(candidate=False)),
    ("ordinary pre-ending export", fixture(canonical=pre, candidate=False, token="20261111T224622Z_159_1")),
):
    drive(g)
    assert len(g.acknowledgements) == 1 and g.acknowledgements[1] is False and g.failures is None, name
    checks.append(name)

g = fixture()
g.pregame = True
drive(g)
assert len(g.acknowledgements) == 0
g.pregame = False
drive(g, 5)
g.epoch += 1
g.candidate = False
drive(g, 5)
assert len(g.acknowledgements) == 0
drive(g, 5)
assert len(g.acknowledgements) == 1 and g.acknowledgements[1] is False and g.failures is None
checks.append("reload during comparison discards prior rows and restarts export")

helper.write(CANDIDATE / "test_readback.json", {
    "status": "PASS_SOURCE_AND_LUA_BRIDGE",
    "test_export_revision": 159,
    "exact_row_strings": 158,
    "checks": checks + ["scalar direct indexing removes crash expression", "saved fields preserved"],
    "engine_request_and_live_admission": "UNVERIFIED",
})
print(f"Verified the exporter and automatic selection in {len(checks)} offline fixtures.")
