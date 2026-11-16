"""Verify the real test command and compare the two recorded exports."""

import json
import re
import sys

from build import BASE, BASELINE, CANDIDATE, HERE, LUA, PACKAGE, RED, load_module

compiler = load_module(BASE / "build.py", "verification_helpers")
baseline = compiler.read(BASELINE)
game = compiler.Path(baseline["game_root"])
exports = (game / LUA).parent
original_token = "20261111T224622Z_159_1"
fallback_token = "20261112T155925Z_160_1"
original = exports / f"snapshot_hs1_{original_token}.json"
fallback = exports / f"snapshot_hs1_{fallback_token}.json"
assert compiler.sha(original) == "F1CBD023E336F7A4173BF3700E5FCB0B9667CE5924FBE00C35D81A253E82B0B0"
assert compiler.sha(fallback) == "DC3B2CCE654628215E9E495B7445A12391EA9BC10EADAA10508489D559CA2459"
pre, post = compiler.read(original), compiler.read(fallback)
assert pre["origin"] == "pre_ending" and pre["revision"] == 159
assert post["origin"] == "post_ending_fallback" and post["revision"] == 160
assert pre["catalogue"] == post["catalogue"]
assert [row["definition"] for row in pre["rows"]] == [row["definition"] for row in post["rows"]]
interrupted = []
for before, after in zip(pre["rows"], post["rows"], strict=True):
    if before["states"][0] == 2:
        assert after["states"][0] == 4 and before["stable"] and after["stable"]
        interrupted.append(before["definition"]["id"])
assert len(interrupted) == 13

old = (game / RED).read_text(encoding="utf-8")
new = (PACKAGE / RED).read_text(encoding="utf-8")
assert re.findall(r"\bpersistent let [^;]+;", old) == re.findall(r"\bpersistent let [^;]+;", new)
assert new.count("this.testHistoryRevision = request.revision;") == 1
assert "SerializeRowHS2(i, this.previousRows[i])" in new
assert "this.ClearTestHistory();" in new.split("public func Restored()", 1)[1].split("private func Register()", 1)[0]
assert "this.ClearTestHistory();" in new.split("private func OnDetach()", 1)[1].split("private func ResetRead()", 1)[0]
assert "this.SetFact" not in (HERE / "history_test_members.reds").read_text(encoding="utf-8")

sys.path.insert(0, str(HERE.parent / "quest_restoration_qr9/worker_b/tooling"))
from lupa.luajit21 import LuaRuntime

lua = LuaRuntime(unpack_returned_tuples=True)
files = lua.table()
for token, path in ((original_token, original), (fallback_token, fallback)):
    files[f"snapshot_hs1_{token}.json"] = path.read_bytes().decode("utf-8")
lua.globals().files = files


def decode(data):
    value = json.loads(data)
    return lua.table_from(value, recursive=True)


lua.globals().decode = decode
lua.execute("""
events = {}
registerForEvent = function(name, fn) events[name] = fn end
json = {decode = decode}
io.open = function(name)
  if not files[name] then return nil end
  return {read = function() return files[name] end, close = function() return true end}
end
local system = {
  Count = function() return 158 end,
  UsePreEndingForTest = function(_, revision, rows) selected, requested = revision, rows end,
  TestHistoryStatus = function() return "status" end,
}
Game = {
  GetPlayer = function() return {IsAttached = function() return attached end} end,
  GetSystemRequestsHandler = function() return {IsPreGame = function() return false end} end,
  GetScriptableSystemsContainer = function() return {Get = function() return system end} end,
}
""")
api = lua.execute((PACKAGE / LUA).read_text(encoding="utf-8"))
assert lua.globals().selected is None
assert "Load" in api.UsePreEndingForTest(original_token)
lua.globals().attached = True
assert "Invalid" in api.UsePreEndingForTest("../escape")
assert "missing" in api.UsePreEndingForTest("missing")
assert "pre-ending snapshot" in api.UsePreEndingForTest(fallback_token)
assert lua.globals().selected is None
assert "queued" in api.UsePreEndingForTest(original_token)
assert lua.globals().selected == 159 and api.TestHistoryStatus() == "status"
document = files[f"snapshot_hs1_{original_token}.json"]
cursor = document.index(',"rows":[') + len(',"rows":[')
for index, row in enumerate(pre["rows"], 1):
    value, end = json.JSONDecoder().raw_decode(document, cursor)
    assert value == row
    assert lua.globals().requested[index] == document[cursor:end]
    cursor = end + 1
assert lua.globals().requested[159] is None
assert document[cursor - 1:] == "]}\n"
compiler.write(CANDIDATE / "test_readback.json", {
    "status": "PASS_SOURCE_AND_LUA_BRIDGE",
    "test_export_revision": 159,
    "exact_row_strings": len(pre["rows"]),
    "interrupted_quest_roots": interrupted,
    "checks": ["exact export and catalogue pins", "reject unsafe token, missing file and fallback",
               "require attached player", "explicit opt-in", "same persisted fields",
               "verification in simulation", "session reset on restore/detach"],
    "engine_request_and_live_admission": "UNVERIFIED",
})
print("Verified the actual Lua test command against 158 exact rows and negative fixtures.")
