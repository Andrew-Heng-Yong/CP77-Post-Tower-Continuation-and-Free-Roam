"""Review the installed baseline delta and verify the compiled arm resume ordering."""

from build import BASE_SHA, CHANGED, GAME, REDS, ROOT, read, sha, verified_baseline, write


def section(source, start, end):
    offset = source.index(start)
    return source[offset:source.index(end, offset + len(start))]


def main():
    base = verified_baseline()
    candidate = ROOT / "candidate_01"
    manifest_path = candidate / "core_manifest.json"
    manifest = read(manifest_path)
    proof_path = candidate / "compile_01/assessment.json"
    proof = read(proof_path)
    assert manifest["baseline_sha256"] == BASE_SHA
    assert proof["status"] == "PASS" and sha(proof_path) == manifest["compile_assessment_sha256"]
    assert sha(candidate / "compile_01/cache/compiled.redscripts") == proof["compiled_sha256"]
    before = {r["path"]: r for r in base["core_files"]}
    after = {r["path"]: r for r in manifest["core_files"]}
    assert before.keys() == after.keys()
    assert {p for p in before if before[p] != after[p]} == set(CHANGED)

    old = (GAME / REDS).read_text(encoding="utf-8-sig")
    new = (candidate / "package" / REDS).read_text(encoding="utf-8-sig")
    markers = (
        ("  public func CoverCreditsExit()", "  public func PhotoRefreshUpdate()"),
        ("        refresh.state = TowerPhotoRefreshState.Opening;", "    return false;\n  }\n\n  private func"),
    )
    for start, end in markers:
        assert section(old, start, end) == section(new, start, end)
    assert old.split("  private func PhotoGameplayReady(", 1)[1].split("  public let player:", 1)[1] == \
        new.split("  private func PhotoGameplayReady(", 1)[1].split("  public let player:", 1)[1]
    assert new.count(".SetFact(") == old.count(".SetFact(")

    compiled_path = candidate / "compile_01/compiled.script"
    compiled = compiled_path.read_text(encoding="utf-8-sig")
    update = section(compiled, "  public func PhotoRefreshUpdate()", "  public func QueueArmResume(")
    assert update.count(".QueueArmResume(") == update.count(".ExecuteNode(") == 1
    assert update.index("PhotoGameplayReady(") < update.index(".armResumeQueued = true")
    assert update.index(".armResumeQueued = true") < update.index(".QueueArmResume(")
    assert update.index(".QueueArmResume(") < update.index("this.Now() + 0.35")
    assert update.index("this.Now() <") < update.index(".CanPhotoModeBeEnabled()") < update.index(".ExecuteNode(")
    arm = section(compiled, "  public func QueueArmResume(", "  public func PhotoGameplayReady(")
    assert arm.count("new PSMStartStateMachine()") == arm.count(".QueueEvent(") == 3
    assert arm.count('.definitionName = n"UpperBody"') == 1
    assert arm.count('.definitionName = n"Equipment"') == 2
    assert arm.count('.referenceName = n"RightHand"') == arm.count('.referenceName = n"LeftHand"') == 1

    write(candidate / "verification.json", {
        "status": "PASS", "candidate_sha256": sha(manifest_path),
        "compiled_readback_sha256": sha(compiled_path),
        "checked": [
            "Only the loading controller changes in the full installed payload",
            "Native credits and setup admission and the existing Photo Mode cycle match the predecessor",
            "Three native events target UpperBody, Equipment RightHand and Equipment LeftHand",
            "On-foot and same-player checks precede a one-shot queue and a bounded gameplay-time wait",
            "Native Photo Mode admission still precedes entry",
        ],
        "gameplay": "PENDING",
    })
    print("Compiled readback verified the three arm events and their order before Photo Mode.")


if __name__ == "__main__":
    main()
