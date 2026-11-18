"""Verify the staged payload and read back the new handoff and loading UI."""

from build import BASE_SHA, CHANGED, GAME, REDS, ROOT, read, sha, verified_baseline, verify_rows, write


def block(script, signature):
    start = script.index(signature)
    return script[start:script.index("\n  }", start)]


def ordered(script, *markers):
    position = 0
    for marker in markers:
        position = script.index(marker, position) + len(marker)


def main():
    base = verified_baseline()
    candidate = ROOT / "candidate_01"
    manifest_path = candidate / "core_manifest.json"
    manifest = read(manifest_path)
    compile_dir = candidate / "compile_01"
    proof_path = compile_dir / "assessment.json"
    proof = read(proof_path)
    assert manifest["baseline_sha256"] == BASE_SHA
    assert proof["status"] == "PASS" and sha(proof_path) == manifest["compile_assessment_sha256"]
    assert sha(compile_dir / "cache/compiled.redscripts") == proof["compiled_sha256"]
    verify_rows(candidate / "package", manifest["core_files"])
    before = {item["path"]: item for item in base["core_files"]}
    after = {item["path"]: item for item in manifest["core_files"]}
    assert before.keys() == after.keys()
    assert {path for path in before if before[path] != after[path]} == set(CHANGED)
    assert after[REDS]["sha256"] == sha(ROOT / "source" / "PTFR_LoadingCoverLC1.reds") == proof["source_after"][REDS]

    old = (GAME / REDS).read_text(encoding="utf-8-sig")
    new = (candidate / "package" / REDS).read_text(encoding="utf-8-sig")
    for method in ("CoverCreditsExit", "MaintainCreditsCover", "Check", "Accepts", "QueueArmResume",
                   "PhotoRefreshUpdate", "PhotoGameplayReady", "HandleCreditsUIState"):
        signature = f"func {method}("
        assert block(old, signature) == block(new, signature), method
    assert new.count(".SetFact(") == old.count(".SetFact(")
    assert new.count("persistent let") == old.count("persistent let")

    compiled_path = compile_dir / "compiled.script"
    compiled = compiled_path.read_text(encoding="utf-8-sig")
    ordered(block(compiled, "func FinishPhotoRefresh("), "this.ClearPhotoRefresh()", "if gameplayCameraReady", "this.ReleaseSetup()")
    release = block(compiled, "func ReleaseSetup(")
    ordered(release, "!this.continuation", "this.creditsCoverRequested || NotEquals(this.photoRefreshResult",
            "if Equals(this.armRefreshResult", "this.armRefreshResult = this.ReapplyStockArms()",
            '"reapply-requested"', "this.EngineNow() + 0.25", "this.EngineNow() < this.armRevealAt",
            "this.released = true", "this.Drop()", 'this.EndCreditsCover(n"setup-released")')
    reapply = block(compiled, "func ReapplyStockArms(")
    ordered(reapply, ".IsAttached()", "GetLocalPlayerControlledGameObject()", "IsPhotoModeActive()",
            "PhotoMode.IsActive", "PhotoGameplayReady(", "PTFRReapplyStockArmCustomization(")
    stock = block(compiled, "func PTFRReapplyStockArmCustomization(")
    ordered(stock, "this.m_playerPuppet != player", "EquipmentSystem.GetData(player)", "this.GetSavedData()",
            ".enabled", ".switcherIndex != 0u", ".hasMaxTacApperanceEquipped", "gamedataEquipmentArea.ArmsCW)",
            "gamedataEquipmentArea.ArmsCWStyle)", 't"AttachmentSlots.RightArm"', "IsSlotSpawningAnyItem(",
            "GetItemInSlot(", 't"Items.HolsteredFists"', "this.RestoreCyberwareCustomization(true)")
    assert stock.count(".RestoreCyberwareCustomization(") == 1

    setup = compiled[compiled.index("class PTFR.LoadingCoverLC1.StartupCoverLC1 "):]
    reset = block(setup, "func Restored(")
    ordered(reset, "ArrayClear(this.setupEvents)", 'this.setupLog = ""', "this.setupLogStarted = -1.00",
            "this.armRefreshResult =", "this.armRevealAt = -1.00")
    events = block(setup, "func RecordSetupEvent(")
    ordered(events, "this.EngineNow()", "ArraySize(this.setupEvents) >= 5", "ArrayErase(this.setupEvents, 0)",
            "ArrayPush(this.setupEvents", "this.creditsView.UpdateDebugLog(this.setupLog)",
            "this.popup.UpdateDebugLog(this.setupLog)", "this.photoRefresh.UpdateDebugLog(this.setupLog)")
    for class_name, view_ref in (("TowerPhotoRefresh", "menuView"), ("SetupPopupLC1", "view")):
        view = compiled[compiled.index(f"class PTFR.LoadingCoverLC1.{class_name} "):]
        assert f"this.{view_ref}.UpdateDebugLog(value)" in block(view, "func UpdateDebugLog(")

    view = compiled[compiled.index("class PTFR.LoadingCoverLC1.SetupCoverViewLC5 "):]
    layout = block(view, "func Build(")
    ordered(layout, 'n"opaqueCover"', "32768.00, 32768.00", ".SetOpacity(1.00)",
            "this.progressWidth = 560.00", "new inkVerticalPanel()", '"Preparing Tower continuation", 34',
            '"Please wait while your save is prepared.", 20', 'n"setupProgressTrack"', 'n"setupProgressFill"',
            '"0%  |  0 / 12 setup checks", 20', '"Debug log", 17')
    ordered(block(view, "func UpdateProgress("), "Clamp(", "this.progress.SetWidth(this.progressWidth *")

    write(candidate / "verification.json", {
        "status": "PASS",
        "candidate_sha256": sha(manifest_path),
        "compiled_readback_sha256": sha(compiled_path),
        "checked": [
            "Exactly one Core script changed, and installed dependency hashes match",
            "Existing admission, credits and Photo Mode control paths retained",
            "One stock arm customization reapply with active player, equipment and appearance guards",
            "Normal Photo Mode exit precedes the reapply and covered release",
            "Five-event session log wired to all three cover views",
            "Compact shared layout, original opaque cover and proportional progress",
        ],
        "gameplay": "PENDING",
    })
    print("Verified the staged payload and compiled arm, loading layout and debug log changes.")


if __name__ == "__main__":
    main()
