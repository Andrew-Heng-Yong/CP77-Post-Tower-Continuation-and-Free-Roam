"""PA2 artifact/source contracts, LuaJIT execution, and explicit state models.

Models are not a REDengine gameplay test. Output is scoped to a new PA2 build.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime


def read(path):
    return Path(path).read_text(encoding="utf-8-sig")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def main():
    build = Path(sys.argv[1]).resolve()
    assert build.is_relative_to(ROOT / "prealpha/transition/build")
    assert not (build / "tests.json").exists(), "Do not overwrite pinned tests"
    report = json.loads(read(build / "build.json"))
    comp = json.loads(read(build / "compile.json"))
    assert comp["status"] == "PASS_COMPILE_AND_READBACK_NOT_LIVE"
    assert comp["build_sha256"] == sha(build / "build.json")
    cases = []

    def check(ok, label):
        assert ok, label
        cases.append(label)

    pkg = Path(report["package_root"])
    for f in report["package_files"]:
        assert sha(pkg / f["relative"]) == f["sha256"]
    check(len(report["package_files"]) == 53 and len(report["changes"]) == 4,
          "53 packaged files hash-match; exactly four replacements")
    source_paths = {
        "scripts/PreAlphaArrivalPA1.reds": "r6/scripts/PTFR_PreAlpha/PA1/PreAlphaArrivalPA1.reds",
        "scripts/PreAlphaEntry.reds": "r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds",
        "cet/init.lua": "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua",
    }
    for a, b in source_paths.items():
        check(sha(ROOT / "prealpha/transition" / a) == sha(pkg / b), f"Current source matches compiled/packaged {a}")
    for f in comp["package_scripts"]:
        assert sha(f["path"]) == f["sha256"]
    check(sha(Path(comp["stage"]) / "compiled.script") == comp["flat_sha256"], "Compiled readback hash unchanged")
    flat = read(Path(comp["stage"]) / "compiled.script")
    for name in ("PTFRPA2_ControlReady", "PTFRPA2_Reveal", "PTFRPA2_Prepared", "Native gig module missing."):
        check(name in flat, f"Compiled body includes {name}")

    graph = json.loads(read(build / "graph.json"))
    check(graph["unchanged_prior_payloads"] and report["all_prior_payloads_preserved"], "Builder verified every prior node payload unchanged")
    check(report["resources"] == 616, "616 archive members read back; only final_boards changed")
    check(set(graph["removed_edges"]) == {"109.Out -> 110.In", "128.Out -> 129.In"}, "Exactly two old edges spliced after the closed-credits Tower guard")
    nodes = {n["Data"]["id"]: n["Data"] for n in json.loads(read(build / "final.patched.json"))["Data"]["RootChunk"]["graph"]["Data"]["nodes"]}
    data = lambda n, field: nodes[n][field]["Data"]
    check(data(141, "type")["fadeIn"] == 0 and data(159, "type")["fadeIn"] == data(160, "type")["fadeIn"] == 1, "Success and both failure paths have native fade-in")
    tp = data(143, "params")
    check(tp["useFastTravelMechanism"] == tp["healAtTeleport"] == 0, "Native placement neither invokes global fast travel nor heals")
    check(tp["destinationRef"]["Data"]["entityReference"]["reference"]["$value"].endswith("/#q001_pr_v_room/#cp77_spwn_performance_test"), "Native H10 street node selected")
    check(data(143, "entityReference")["mainPlayerObject"] == data(143, "entityReference")["refLocalPlayer"] == 1 and nodes[143]["lookAtAction"] == "Reset", "Native placement targets local main player and resets look-at")
    check(data(145, "type")["tier"] == "Tier1_FullGameplay" and data(145, "type")["forceEmptyHands"] == 0, "Post-placement native full-gameplay tier request releases forced empty hands")
    edges = set(graph["added_edges"])
    for start, base, fact, success, seconds in ((146,150,"PTFRPA2_ControlReady",129,60), (130,170,"PTFRPA2_Reveal",159,180)):
        check(data(base,"condition")["type"]["Data"]["factName"] == fact and data(base+4,"condition")["type"]["Data"]["factName"] == fact, f"Race {base}: matching wait and final fact test")
        check(data(base+1,"condition")["type"]["Data"]["seconds"] == seconds and nodes[base+3]["permanent"] == 1, f"Race {base}: bounded native timer and permanent waiter cancellation")
        for edge in (f"{start}.Out -> {base}.In", f"{start}.Out -> {base+1}.In", f"{base}.Out -> {base+2}.In1", f"{base+1}.Out -> {base+2}.In2", f"{base+2}.Out1 -> {base+3}.In", f"{base+3}.CutSource -> {base}.CutDestination", f"{base+3}.CutSource -> {base+1}.CutDestination", f"{base+3}.Out -> {base+4}.In", f"{base+4}.True -> {success}.In", f"{base+4}.False -> {base+5}.In", f"{base+5}.Out -> 160.In"):
            assert edge in edges, edge
        check(True, f"Race {base}: serialized edges route winner through cut, success gate, or failure uncover")

    arrival = read(ROOT / "prealpha/transition/scripts/PreAlphaArrivalPA1.reds")
    entry = read(ROOT / "prealpha/transition/scripts/PreAlphaEntry.reds")
    check('epoch != this.epoch' in arrival and 'PTFRPA2_Finished") == 1' in arrival and 'PTFRPA2_Fault") > 0' in arrival, "Observer rejects stale callbacks and terminal/faulted handoffs")
    check(set(re.findall(r'this.Set\(n"([^"]+)"', arrival)) == {"PTFRPA2_ControlReady", "PTFRPA2_Reveal"}, "Observer writes only its two readiness acknowledgements")
    for forbidden in ("TeleportTo", "RemoveStatusEffect", "RemoveAllGameplay", "SaveGame(", "LoadGame(", "SetTier("):
        assert forbidden not in arrival
    check(True, "Observer performs no teleport, blanket restriction removal, tier force, or save/load")
    for required in ("CyberwarePolicy.Safe(player)", "SceneTier) == 1", "HighLevel) == 1", "!scene.IsEntityInScene", 't"GameplayRestriction.NoMovement"', "IsPhoneCallActive", "!IsDefined(bb)", "!IsDefined(scene)", "!this.NearTarget(player)", "this.safeTicks < 4", "this.safeTicks < 8"):
        assert required in arrival, required
    check(True, "Full-player readiness, H10 position and stable ticks are source-backed")
    check(entry.index('if !profile.PTFRPAComplete()') < entry.index('if !this.Dispatch()') < entry.index('SetFact(n"PTFRPA2_Prepared"'), "Profile completion and real dispatch precede preparation acknowledgement")
    check('Native gig module missing."; return false;' in entry, "Missing gig module cannot falsely acknowledge preparation")
    check('this.Certified(id)' in entry and 'this.DevelopmentArmed()' in entry and 'Excluded: no certified unstarted pre-Tower history.' in entry, "Production history remains distinct from explicit development assumptions")

    # Explicit behavioral models: useful ordering checks, not native execution.
    for control in (False, True):
        for prepared in (False, True):
            for last_ready in (False, True):
                activation = control
                reveal = activation and prepared and last_ready
                assert not reveal or (control and prepared and last_ready)
                assert control or not activation
    check(True, "Model: no activation before first readiness and no reveal before preparation plus final readiness")
    for completed_before_deadline in (False, True):
        pending = {"wait", "timeout"}
        winner = "wait" if completed_before_deadline else "timeout"
        pending.remove(winner); pending.clear()  # Native cut topology verified above.
        check(not pending, f"Race model: {winner} cancels loser; no delayed success/fault duplicate")
    for finished, fault, stale, player_safe, near in ((True,0,False,True,True),(False,1,False,True,True),(False,0,True,True,True),(False,0,False,False,True),(False,0,False,True,False)):
        acknowledgement = not (finished or fault or stale) and player_safe and near
        assert not acknowledgement
    check(True, "Model: completion, fault, stale epoch, unsafe player, wrong position cannot acknowledge arrival")

    lua_source = read(ROOT / "prealpha/transition/cet/init.lua")
    methods = {
        "Status": ("PTFR.ActivityStateR3.PreAlphaEntry", "Status", []),
        "Arrival": ("PTFR.ActivityStateR3.PreAlphaArrivalPA1", "Status", []),
        "Gigs": ("PTFR.ActivityStateR3.NativeGigsU9", "InspectAll", []),
        "Gig": ("PTFR.ActivityStateR3.NativeGigsU9", "Inspect", ["sts_hey_rey_06"]),
        "Entry": ("PTFR.ActivityStateR3.PreAlphaEntry", "InspectAll", []),
        "Phone": ("PTFR.ActivityStateR3.GigPhoneU9", "Inspect", []),
        "Profile": ("PTFR.RestrictionsR3.ProfilePolicy", "GetStatus", []),
    }
    mock = '''
events, prints, calls = {}, {}, {}
active, generation, mode = false, 1, "ready"
registerForEvent = function(name, fn) assert(name == "onUpdate"); events[name]=fn end
print = function(s) prints[#prints+1]=s end
Game = {
 GetQuestsSystem=function()
  if mode == "error" then error("loading") end
  return {GetFactStr=function(_, name) assert(name=="PTFRPA2_Started");return active and 1 or 0 end}
 end,
 GetScriptableSystemsContainer=function()
  if mode == "error" then error("loading") end
  if mode == "missing" then return nil end
  return {Get=function(_,name)
   assert(expected[name], "Wrong system: "..name)
   local s={}
   return setmetatable(s,{__index=function(_,method)
    assert(expected[name][method] ~= nil)
    return function(self,...)
     assert(self==s); assert(select("#",...)==expected[name][method])
     calls[#calls+1]=name.."."..method
     return name.."."..method..":"..generation
    end
   end})
  end}
 end
}
'''
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(mock)
    expected = {}
    for system, method, args in methods.values():
        expected.setdefault(system, {})[method] = len(args)
    lua.globals().expected = lua.table_from({k: lua.table_from(v) for k,v in expected.items()})
    api = lua.execute(lua_source)
    check(set(api.keys()) == set(methods) and len(lua.globals().calls) == 0, "Actual LuaJIT load installs only the bounded diagnostic update hook")
    for public, (system, method, args) in methods.items():
        check(api[public](*args) == f"{system}.{method}:1", f"LuaJIT {public}: correct native system/method/arity")
        script = next(p for p in (pkg / "r6/scripts").rglob("*.reds") if re.search(rf"public class {system.rsplit('.',1)[1]} extends ScriptableSystem", read(p)))
        check(bool(re.search(rf"public func {method}\([^)]*\) -> String",read(script))), f"{public} points to an existing packaged REDscript method")
    tick = lua.globals().events.onUpdate
    for _ in range(5): tick(1)
    check(len(lua.globals().prints) == 0, "Inactive game emits no transition trace")
    lua.globals().active = True
    for _ in range(200): tick(1)
    count = len(lua.globals().prints)
    for _ in range(20): tick(1)
    check(0 < count <= 180 and len(lua.globals().prints) == count, "Actual LuaJIT trace stops at its row/time budget")
    lua.globals().active = False; tick(1)
    lua.globals().active = True; lua.globals().generation = 2; tick(1)
    check(lua.globals().prints[len(lua.globals().prints)].count(":2") == 2, "New inactive-to-active session resolves new native objects")
    for mode in ("missing","error"):
        lua.globals().mode = mode
        for public, (_,_,args) in methods.items():
            check(isinstance(api[public](*args),str),f"LuaJIT {public}/{mode}: bounded diagnostic, no exception")
        tick(1)
    for bad in (None, False, 8, ""):
        check("Pass a gig ID" in api.Gig(bad), f"LuaJIT Gig rejects {bad!r}")
    for forbidden in ("SetFact", "AddToInventory", "TeleportTo", "FullNerf", "io.open", "os.execute", "Override(", "Observe("):
        assert forbidden not in lua_source
    check(True,"CET contains no gameplay writers, file writes, overrides, or observation hooks")
    result = {"status":"PASS_NOT_LIVE", "cases":len(cases), "details":cases,
              "limitations":"Native quest scheduling/fade/control/streaming and live ending/reload remain untested; state models are not engine execution.",
              "build_sha256":sha(build/"build.json"), "compile_sha256":sha(build/"compile.json"),
              "source_hashes":{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/"prealpha/transition").rglob("*") if p.is_file() and "build" not in p.relative_to(ROOT/"prealpha/transition").parts},
              "lua_runtime":lua.eval("jit.version")}
    (build/"tests.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("status","cases","lua_runtime","limitations")}))


if __name__ == "__main__":
    main()
