"""Derive the two-script body-view revert from the exact installed LC5 source."""

from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "source_02"
ROOT = HERE.parents[1]
GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
MANIFEST = ROOT / "prealpha/credits_cover_lc5_20261116_01/work/deployment_01/installed_manifest_01.json"
RELATIVES = (
    "r6/scripts/PTFR_Consolidated/PTFR_LoadingCoverLC1.reds",
    "r6/scripts/PTFR_Consolidated/PTFR_RestrictionsR1.reds",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def remove_span(text: str, start: str, end: str) -> str:
    assert text.count(start) == 1, start
    assert text.count(end) == 1, end
    left = text.index(start)
    right = text.index(end)
    assert left < right, (start, end)
    return text[:left] + text[right:]


def replace_span(text: str, start: str, end: str, replacement: str) -> str:
    assert text.count(start) == 1, start
    assert text.count(end) == 1, end
    left = text.index(start)
    right = text.index(end)
    assert left < right, (start, end)
    return text[:left] + replacement + text[right:]


def remove_line(text: str, line: str, newline: str) -> str:
    target = line + newline
    assert text.count(target) == 1, line
    return text.replace(target, "", 1)


def update_cover(text: str, newline: str) -> str:
    text = remove_span(text,
        "    if this.travelSampleAt>0.0 && this.EngineNow()>=this.travelSampleAt {",
        "    if this.leaving || this.released { return; }")
    text = remove_line(text, "    this.FinishBodyReturnTP3();", newline)
    text = remove_line(text,
        "    if !this.FinishPresentationTP2() { this.stableSince=-1.0;this.Heartbeat();return; }", newline)
    text = remove_line(text, "    this.presentationAt=this.EngineNow()+3.0;", newline)
    text = remove_span(text,
        "  private func TracePresentation(reason: CName) -> Void {",
        "  // Native arrival, job and control checks have passed before this is called.")
    pause_handler = "\n".join((
        "  // Preserve credits-cover pause handling without presentation repair.",
        "  public func HandleCreditsUIState(current: CName) -> Void {",
        "    if !this.running || !this.creditsCoverRequested { return; }",
        "    if Equals(current,n\"inkPauseMenuState\") { this.EndCreditsCover(n\"pause-opened\"); }",
        "    else { this.MaintainCreditsCover(); }",
        "  }",
        "",
    )).replace("\n", newline)
    text = replace_span(text,
        "  // Native arrival, job and control checks have passed before this is called.",
        "  public func Status() -> String { return \"LC3 visible/released=\"",
        pause_handler)
    text = remove_span(text,
        "// Record native progress and the owned cover state around a post-Tower trip.",
        "// TP1 reads presentation state only.")
    text = replace_span(text,
        "// TP1 reads presentation state only.",
        "@wrapMethod(gameuiInGameMenuGameController)",
        "// Keep the existing credits-cover pause behavior.\n".replace("\n", newline))
    assert text.count("cover.TraceUIStateTP2(previousStateName,currentStateName);") == 1
    text = text.replace("cover.TraceUIStateTP2(previousStateName,currentStateName);",
                        "cover.HandleCreditsUIState(currentStateName);", 1)
    assert "ActivateTPPRepresentationEvent" not in text
    assert "DeactivateTPPRepresentationEvent" not in text
    assert "TryEndingLoadingCleanup" not in text
    assert "TracePresentation" not in text
    assert "TraceFastTravel" not in text
    assert "TraceUIStateTP2" not in text
    assert "PresentationTraceTP1" not in text
    assert "CoverCreditsExit" in text and "PTFRLC1_CoverReady" in text
    assert "HandleCreditsUIState" in text and "pause-opened" in text
    assert "if !this.Check()" in text
    return text


def update_restrictions(text: str, newline: str) -> str:
    text = remove_line(text,
        "    // TP2 performs the full representation cycle under the setup cover after", newline)
    text = remove_line(text,
        "    // this attachment pass settles; do not race it with a standalone return.", newline)
    text = remove_line(text,
        "  // Transient attachment work only; does not infer visual success from an item.", newline)
    text = remove_line(text,
        "  public func PTFRTP2HandsSettled() -> Bool { return this.handRefreshAttempts == 0; }", newline)
    assert "DeactivateTPPRepresentationEvent" not in text
    assert "PTFRTP2HandsSettled" not in text
    assert "PTFRRefreshPostTowerHands" in text
    return text


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    assert manifest["core_epoch"] == "LC5_CREDITS_COVER"
    core = {row["path"]: row for row in manifest["core_files"]}
    assert len(core) == 51
    OUTPUT.mkdir(exist_ok=False)
    for relative in RELATIVES:
        source = GAME / relative
        data = source.read_bytes()
        assert len(data) == core[relative]["bytes"] and digest(data) == core[relative]["sha256"]
        newline = "\r\n" if b"\r\n" in data else "\n"
        text = data.decode("utf-8-sig")
        updated = (update_cover(text, newline) if relative == RELATIVES[0]
                   else update_restrictions(text, newline))
        output = OUTPUT / Path(relative).name
        with output.open("xb") as stream:
            stream.write(updated.encode("utf-8"))
        print(f"{relative}: {digest(data)} -> {digest(output.read_bytes())}")


if __name__ == "__main__":
    main()
