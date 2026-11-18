"""Read back the compiled handoff and exercise the actual CET update callback."""

import hashlib
import sys
from pathlib import Path
from zipfile import ZipFile

from build import GAME, LUA, REDS, ROOT, read, sha, verified_baseline, write


def section(data: str, start: str, end: str) -> str:
    start_at = data.index(start)
    return data[start_at:data.index(end, start_at + len(start))]


def main() -> None:
    repo = ROOT.parents[1]
    candidate = ROOT / "candidate_01"
    work = repo / "diagnostics/post_tower_photo_refresh_build_20261117_01"
    base = verified_baseline()
    manifest = read(candidate / "core_manifest.json")
    compiled = candidate / "compile_01"
    compile_proof = read(compiled / "assessment.json")
    assert sha(compiled / "assessment.json") == manifest["compile_assessment_sha256"]
    assert compile_proof["compiled_sha256"] == sha(compiled / "cache/compiled.redscripts")

    old = (GAME / REDS).read_text(encoding="utf-8-sig")
    source = (candidate / "package" / REDS).read_text(encoding="utf-8-sig")
    for start, end in (
        ("  private func Check() -> Bool {", "  private func Schedule()"),
        ("  public func CoverCreditsExit()", "  private func MaintainCreditsCover()"),
        ("@wrapMethod(MenuScenario_FinalBoards)", "@wrapMethod(PopupsManager)"),
    ):
        assert section(source, start, end) == section(old, start, end)
    assert source.count(".SetFact(") == old.count(".SetFact(")
    assert source.count("private persistent let") == old.count("private persistent let")
    for path in (GAME / REDS, candidate / "package" / REDS):
        assert "ActivateTPPRepresentationEvent" not in path.read_text(encoding="utf-8-sig")

    readback_path = work / "compiled_01.script"
    readback = readback_path.read_text(encoding="utf-8-sig")
    request = section(readback, "  public func PhotoRefreshUpdate()", "  public func PhotoGameplayReady(")
    assert request.count(".ExecuteNode(") == request.count(".OnExitConfirmed(true)") == 1
    assert request.index(".CanPhotoModeBeEnabled()") < request.index(".ExecuteNode(")
    assert request.index(".PTFRPhotoPreviewReady()") < request.index(".OnExitConfirmed(true)")
    assert "lockExitUntilScreenshot = false" in request and 'factName = ""' in request
    assert "menuHidden" in request and "PhotoMode.IsActive" in request and "cameraReadySince" in request
    assert ".SetFact(" not in request
    for call in (".PhotoMenuShown(this)", ".PhotoMenuIntroFinished(this)",
                 ".PhotoMenuHidden(this)", ".PhotoPreviewSetup(this, player$"):
        assert call in readback, call
    check_restore = section(readback, "  public func Restored() -> Void {\n    this.ClearPhotoRefresh();", "  public cb func OnStarted")
    assert 'this.photoRefreshResult = n"None"' in check_restore
    masks = section(readback, "  public func AttachMenuCover()", "  public func RemoveMenuCover()")
    assert 'GetLayer(n"inkPhotoModeLayer")' in masks and "SetInteractive(false)" in masks
    assert manifest["core_files"][:2] == base["core_files"][:2]  # existing archive and its XL

    fixture = repo / "prealpha/quest_resume_cassius_snapshot_replay_20261115_01/run_03/AutoSave-16.json"
    save_readback = read(fixture)
    sav = repo / "recovery/auto16_photo_refresh_restore_20261117_01/incoming/AutoSave-16/sav.dat"
    assert sha(sav) == save_readback["sha256"]
    assert save_readback["facts"]["q307_done"] is None and save_readback["facts"]["q307_active"] == 1

    tooling = repo / "prealpha/quest_restoration_qr9/worker_b"
    provenance = read(tooling / "tooling_provenance_01/manifest.json")
    wheel = tooling / "tooling_provenance_01" / provenance["filename"]
    assert sha(wheel) == provenance["wheel_sha256"]
    with ZipFile(wheel) as bundle:
        member = next(name for name in bundle.namelist() if name.startswith("lupa/luajit21.") and name.endswith(".pyd"))
        native = tooling / "tooling" / member
        assert sha(native) == hashlib.sha256(bundle.read(member)).hexdigest().upper()
    sys.path.insert(0, str(tooling / "tooling"))
    from lupa.luajit21 import LuaRuntime
    runtime = LuaRuntime()
    runtime.execute("""
        callbacks, calls = {}, 0
        modeAvailable, pending, shouldError = true, false, false
        cover = {
            PhotoRefreshUpdate = function(self)
                calls = calls + 1
                if shouldError then error("mocked unavailable native owner") end
                return pending
            end,
            PhotoRefreshStatus = function() return "mocked status" end,
        }
        Game = {
            GetScriptableSystemsContainer = function()
                return { Get = function(_, name)
                    assert(name == "PTFR.LoadingCoverLC1.StartupCoverLC1")
                    return modeAvailable and cover or nil
                end }
            end,
            GetQuestsSystem = function() return { GetFactStr = function() return 0 end } end,
        }
        registerForEvent = function(name, cb) callbacks[name] = cb end
    """)
    api = runtime.execute((candidate / "package" / LUA).read_text(encoding="utf-8-sig"))
    runtime.globals()["api"] = api
    runtime.execute("""
        local update = callbacks.onUpdate
        update(0.01)
        for _ = 1, 20 do update(0.01) end
        assert(calls == 1 and api.PhotoRefresh() == "mocked status")
        pending = true
        update(0.31)
        assert(calls == 2)
        update(0.10)
        assert(calls == 3)
        pending = false
        update(0.10)
        assert(calls == 4)
        update(0.10)
        assert(calls == 4)
        modeAvailable = false
        update(0.50)
        assert(calls == 4)
        modeAvailable, shouldError = true, true
        update(0.60)
        assert(calls == 5)
        update(0.10)
        assert(calls == 5)
    """)
    write(candidate / "verification.json", {
        "status": "PASS", "candidate_sha256": sha(candidate / "core_manifest.json"),
        "compiled_readback_sha256": sha(readback_path),
        "source_checks": ["original setup and credits admission bodies preserved",
                          "compiled native entry and normal exit in guarded state machine",
                          "compiled menu and preview observers preserved",
                          "one session and no new persistent fields or fact writes",
                          "archive and ArchiveXL registration unchanged"],
        "fixture_autosave_16_sha256": sha(sav), "fixture_is_mid_ending": True,
        "lua_jit_fixture": "idle/active cadence, lost session and failed native callback",
        "lua_jit_version": runtime.eval("jit.version"), "runtime_gameplay": "PENDING",
    })
    print("Compiled readback and LuaJIT update fixture passed.")


if __name__ == "__main__":
    main()
