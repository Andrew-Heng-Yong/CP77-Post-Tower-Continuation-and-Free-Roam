"""Check exact JB3 inputs and PS1's REDscript wiring without writing game files."""

import hashlib
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
JB3 = HERE.parent / "johnny_batch4_jb3"
HUNK = re.compile(rb"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def read_patch(path):
    files = {}
    for section in re.split(rb"(?m)^diff --git ", path.read_bytes())[1:]:
        lines = section.splitlines(keepends=True)
        name = lines[1].removeprefix(b"--- a/").rstrip().decode()
        assert name not in files and lines[2].rstrip() == b"+++ b/" + name.encode()
        offsets = [i for i, line in enumerate(lines) if line.startswith(b"@@")]
        files[name] = [(lines[a].rstrip(), lines[a + 1:b]) for a, b in zip(offsets, offsets[1:] + [len(lines)])]
    return files


def apply(source, hunks, *, exact=True):
    lines = source.splitlines(keepends=True)
    result, cursor = [], 0
    for header, body in hunks:
        old_line, old_count, new_line, new_count = (int(n or 1) for n in HUNK.fullmatch(header).groups())
        before = [line[1:] for line in body if line[:1] != b"+"]
        after = [line[1:] for line in body if line[:1] != b"-"]
        assert len(before) == old_count and len(after) == new_count
        start = old_line - 1 if old_count else old_line
        if not exact:
            matches = [i for i in range(cursor, len(lines) - old_count + 1) if lines[i:i + old_count] == before]
            assert len(matches) == 1, header
            start = matches[0]
        assert start >= cursor and lines[start:start + old_count] == before, header
        result.extend(lines[cursor:start])
        if exact:
            assert len(result) == (new_line - 1 if new_count else new_line)
        result.extend(after)
        cursor = start + old_count
    return b"".join(result + lines[cursor:])


def segment(source, start, end):
    return source.split(start, 1)[1].split(end, 1)[0]


def ordered(source, *expressions):
    cursor = 0
    for expression in expressions:
        cursor = source.index(expression, cursor) + len(expression)


def source_checks(original, changed):
    old_r3, r3 = (source["PTFR_RestrictionsR3.reds"] for source in (original, changed))
    entry = changed["PTFR_ActivityStateR3.reds"]
    cover = changed["PTFR_LoadingCoverLC1.reds"]
    for filename, old in original.items():
        protected = r"(?m)^.*(?:\bpersistent let\b|\.SetFact\().*$"
        assert re.findall(protected, old) == re.findall(protected, changed[filename]), filename
    for start, end in [
        ("public class ProfilePhysical", "public class ProfilePolicy"),
        ("func PTFRR3SellPerk", "func PTFRR3MoveTattooToFirst"),
        ("func EmptyNativeSideEffectSlots", "func FullNerf"),
        ("func PTFRPAConfigured", "private func Fail"),
    ]:
        assert segment(old_r3, start, end) == segment(r3, start, end), start

    move = segment(r3, "func PTFRR3ClearSecondHand", "private final func PTFRR3TattooRetained")
    assert "return this.PTFRR3ClearSecondHand(false);" in r3
    ordered(move, "ProfilePolicy.OwnHand", "this.IsEquipPending()", "!= 2",
            "!ProfilePolicy.ApprovedHandTattoo(id)", "first == id", "!ProfilePolicy.ApprovedHandTattoo(first)",
            'item.HasTag(n"UnequipBlocked")', "if count <= 0", "equipped.GetItemParts(firstParts)",
            "this.ptfrr1PreserveParts = id;", "this.UnequipItem(area, 1, false);",
            "if !keepFirst && !ItemID.IsValid", "this.EquipItem(id, 0, false, false);",
            "this.ptfrr1PreserveParts = ItemID.None();", "let expectedFirst = keepFirst ? first : id;",
            "GetItemInEquipSlot(area, 0) != expectedFirst", "ItemID.IsValid(this.GetItemInEquipSlot(area, 1))",
            "PTFRR3TattooRetained(id, count, before)", "PTFRR3TattooRetained(first, firstCount, firstParts)")
    assert move.count(".UnequipItem(") == move.count(".EquipItem(") == 1
    assert not re.search(r"\.(?:RemoveItem|GiveItem|TransferItem)", move)
    retained = segment(r3, "func PTFRR3TattooRetained", "\n}\n")
    ordered(retained, "readback.GetID() != id", "GetItemQuantity(this.m_owner, id) != count",
            "ArraySize(before) != ArraySize(after)", "InnerItemData.GetItemID", "InnerItemData.GetSlotID",
            "ArrayErase(after, j)")
    journal = segment(r3, "if ItemID.IsValid(second)", "if this.stage == 3")
    ordered(journal, "if this.handAttempted", "this.handAttempted = true; this.inflight = true;",
            "if !equipment.PTFRR3ClearSecondHand(true)", "this.Fail(", "return;",
            "this.inflight = false;", "return;", "this.stage = 2")
    assert "ripperdoc" not in journal

    health = segment(r3, "func LC1HealthFailure", "func LC1InitializationStatus")
    ordered(health, "this.enabled && this.vitalsRequested", "this.stage >= 3 && this.stage <= 4",
            "IsDefined(this.physical) && this.physical.Faulted()", "return this.physical.Status();")
    ordered(entry, "let healthFailure = profile.LC1HealthFailure()", 'this.Fact(n"PTFRPA2_Prepared") != 1',
            "this.detail = healthFailure; return;", "this.detail = profile.BeginCoveredSetup();",
            'SetFact(n"PTFRPA2_Prepared", 1)')
    ordered(cover, "entry.SnapshotInitializationHealthy()", "profile.LC1HealthFailure()",
            'this.SetStage("Health setup stopped",healthFailure);return false;',
            "profile.PTFRPAFaulted() ? profile.GetStatus()", "profile.LC1InitializationStatus()",
            '!profile.PTFRPAConfigured() && NotEquals(initialization,"")', "profile.LC1InitializationHeld()",
            "initialization);return false;", "profile.LC1Progress()")
    assert "this.stage+\"\\n\"+this.detail" in cover

    setup = segment(r3, "func BeginCoveredSetup", "func LC1HealthFailure")
    ordered(setup, "if !this.initializationHeld { this.initializationStatus = this.FullNerf(); }",
            "return this.initializationStatus;", "this.initializationHeld = true;", "func Apply",
            'this.initializationStatus = ""; this.initializationHeld = false;', "CyberwarePolicy.Completed(game)",
            'HoldInitialization("Refused: saved profile differs;', 'HoldInitialization("Refused: unsupported perk catalogue.")',
            'return "Refused: progression data unavailable.";', 'return "Refused: invalid progression snapshot.";',
            'HoldInitialization("Refused: obsolete perk ownership.")', "legacy.PTFRR3StartBodyRelic()")
    ordered(r3, "public func Restored()", 'this.initializationStatus = ""; this.initializationHeld = false;',
            "if this.inflight { this.Fail(")


def main():
    pins = json.loads((HERE / "provenance.json").read_bytes())
    manifest_raw = (JB3 / "deployment_01/installed_manifest_01.json").read_bytes()
    assert sha(manifest_raw) == pins["installed_manifest_sha256"]
    manifest = json.loads(manifest_raw)
    for key in ("archive_sha256", "core_epoch"):
        assert manifest[key] == pins[key]
    exact_files = {row["path"]: row["sha256"] for row in manifest["core_files"]}
    patch = read_patch(HERE / "source.patch")
    assert set(patch) == set(pins["files"])
    original, changed = {}, {}
    for path, hunks in patch.items():
        raw = (JB3 / "candidate_01/package" / path).read_bytes()
        assert sha(raw) == pins["files"][path]["before"] == exact_files[path]
        result = apply(raw, hunks)
        assert sha(result) == pins["files"][path]["after"]
        name = Path(path).name
        original[name] = raw.decode().replace("\r\n", "\n")
        changed[name] = result.decode().replace("\r\n", "\n")
    source_checks(original, changed)
    print("PASS: exact JB3 hashes, tattoo guards and readback, setup diagnostics, preserved journals and facts")

    th1 = HERE.parent / "tower_handoff_th1"
    if (th1 / "source.patch").is_file():
        earlier_patch = read_patch(th1 / "source.patch")
        path = next(path for path in patch if path.endswith("/PTFR_LoadingCoverLC1.reds"))
        assert set(patch) & set(earlier_patch) == {path}
        raw = (JB3 / "candidate_01/package" / path).read_bytes()
        earlier = apply(raw, earlier_patch[path])
        th1_pins = json.loads((th1 / "provenance.json").read_bytes())
        assert sha(earlier) == th1_pins["files"][path]["after"]
        layered = apply(earlier, patch[path], exact=False).decode().replace("\r\n", "\n")
        ordered(layered, "CyberwarePolicy.CompletionBlocker(game)", "profile.LC1HealthFailure()",
                "profile.LC1InitializationStatus()", "SnapshotRecoveryHS1.Get(game)", "profile.LC1Progress()")
        print("PASS: PS1 cover changes apply after TH1 in memory")


if __name__ == "__main__":
    main()
