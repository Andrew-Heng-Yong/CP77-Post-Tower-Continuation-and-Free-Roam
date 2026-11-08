"""Check the scoped script repair and stage the full unchanged-archive package."""
from collections import Counter
from pathlib import Path
import hashlib
import re
import shutil
import zipfile

from build import HERE, QR19, SCRIPT, checked, inputs, read, sha, write

ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"
HOOK = "    this.RestoreMQ018MessageContact();\n"


def verify_script(predecessor, source):
    start = source.index("  private func RestoreMQ018MessageContact() -> Void {")
    stop = source.index("  private func Unclaimed(i: Int32)", start)
    method = source[start:stop]
    assert source.count(HOOK) == 1
    assert (source[:start] + source[stop:]).replace(HOOK, "") == predecessor
    assert source.count("this.AdoptS25DelamainPhone();\n" + HOOK) == 1
    assert Counter(re.findall(r"\b([A-Za-z_]+)\(", method))["ChangeEntryState"] == 1
    assert 'let path = "contacts/bartmoss";' in method and 'let className = "gameJournalContact";' in method
    assert "gameJournalEntryState.Active, JournalNotifyOption.DoNotNotify" in method
    assert all(token not in method for token in ("SetFactStr(", "SetEntryVisited(", "PhoneConversation", "PhoneMessage"))
    assert set(re.findall(r'this.Own\(2, "([^"]+)"\) != (\d)', method)) == {
        ("Issued", "1"), ("Entered", "1"), ("Finished", "0"), ("Fault", "0"),
    }
    assert all(term in method for term in (
        'this.Fact("PTFRS29_PHONE_nancy_Issued") != 1', "!this.HasMQ018Reservation()",
        'this.Fact("mq018_visit_website") != 0', "!IsDefined(contact)",
        "!Equals(jm.GetEntryState(contact), gameJournalEntryState.Inactive)",
        "!Equals(contact.GetType(), gameContactType.Texter)", "contact.IsCallable(jm)",
        "this.Common() && this.Safe() && this.Read(2).valid",
    ))
    return method


def native_evidence():
    path = HERE / "native_ui_01/runtime.reds"
    manifest = read(HERE / "native_ui_01/manifest.json")
    checked(path, manifest["output_sha256"])
    checked(manifest["input"], manifest["sha256"])
    ui = path.read_text(encoding="utf-8")
    a = ui.index("  public final static func GetSimpleContactDataArray(")
    b = ui.index("  public final static func GetMessageDataArrayForContact(", a)
    helper = ui[a:b]
    assert "context.stateFilter.active = true;" in helper
    assert "journal.GetContacts(context, entries);" in helper
    assert "MessengerUtils.AddContactData(" in helper
    assert helper.index("journal.GetContacts(") < helper.index("MessengerUtils.AddContactData(")
    assert "MessengerUtils.GetSimpleContactDataArray(this.m_journalMgr, true, true, this.m_isShowingAllMessages)" in ui
    assert "public final native const func IsEntryVisited(entry: wref<JournalEntry>) -> Bool" in ui
    assert "this.m_journalManager.SetEntryVisited(entry, true);" in ui
    return {"phone_query": helper.strip(), "decompile_manifest_sha256": sha(HERE / "native_ui_01/manifest.json")}


def controls(predecessor, source):
    changes = {
        "remove held-owner gate": ('this.Own(2, "Entered") != 1', "false"),
        "allow unrelated contact": ('let path = "contacts/bartmoss";', 'let path = "contacts/nancy";'),
        "allow duplicate state writes": ("!Equals(jm.GetEntryState(contact), gameJournalEntryState.Inactive)", "false"),
        "skip retained-message history": ("this.Common() && this.Safe() && this.Read(2).valid", "this.Common() && this.Safe()"),
        "send notification": ("gameJournalEntryState.Active, JournalNotifyOption.DoNotNotify",
                              "gameJournalEntryState.Active, JournalNotifyOption.Notify"),
    }
    for name, (old, new) in changes.items():
        method = verify_script(predecessor, source)
        assert method.count(old) == 1
        damaged = source.replace(method, method.replace(old, new, 1), 1)
        try:
            verify_script(predecessor, damaged)
        except AssertionError:
            continue
        raise AssertionError(f"Mutation escaped verification: {name}")
    return list(changes)


def main():
    candidate = HERE / "candidate_01"
    assert not candidate.exists()
    installed, base = inputs()
    old_root = QR19 / "candidate_01/package"
    old = {r["path"]: r["sha256"] for r in base["files"]}
    for r in installed["core_files"] + installed["required_files"]:
        checked(Path(installed["game_root"]) / r["path"], r["sha256"])
    script = read(HERE / "proposal_02/plan.json")["script"]
    assert script["path"] == SCRIPT
    overlay = checked(script["source"], script["sha256"])
    predecessor = checked(old_root / SCRIPT, old[SCRIPT]).read_text(encoding="utf-8-sig")
    changed = overlay.read_text(encoding="utf-8-sig")
    assert "RestoreMQ018MessageContact" not in predecessor
    verify_script(predecessor, changed)
    native = native_evidence()
    rejected = controls(predecessor, changed)
    compile_file = HERE / "compile_02/result.json"
    compiled = read(compile_file)
    assert compiled["status"] == "PASS_CURRENT_INPUT_OFFLINE_COMPILE" and compiled["source_count"] == 148
    assert compiled["candidate_script_sha256"] == script["sha256"]
    checked(HERE / "compile_02/cache/compiled.redscripts", compiled["output_sha256"])
    prior_readback = QR19 / "archive_readback.json"
    archive = read(prior_readback)
    assert archive["archive_sha256"] == old[ARCHIVE]
    assert {r["depot"]: r["sha256"] for r in archive["resources"]} == base["source_resources"]
    protection = read(QR19 / "core_manifest_01.json")
    save_rows = protection["protected_saves"] + protection["working_save_files"]
    for row in save_rows:
        checked(Path(installed["save_root"]) / row["path"], row["sha256"])
    leaves = old | {SCRIPT: script["sha256"]}
    assert {p for p, v in leaves.items() if old[p] != v} == {SCRIPT}
    package = candidate / "package"
    for rel, digest in leaves.items():
        old_file = checked(old_root / rel, old[rel])
        target = package / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(overlay if rel == SCRIPT else old_file, target)
        checked(target, digest)
    zip_path = candidate / "PTFR_QR20_Staged_NotInstalled.zip"
    with zipfile.ZipFile(zip_path, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as f:
        for rel in sorted(leaves):
            item = zipfile.ZipInfo(rel, (1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            f.writestr(item, (package / rel).read_bytes(), compresslevel=6)
    with zipfile.ZipFile(zip_path) as f:
        assert f.testzip() is None and len(f.namelist()) == len(leaves) == 51 and set(f.namelist()) == set(leaves)
        assert all(hashlib.sha256(f.read(p)).hexdigest().upper() == h for p, h in leaves.items())
    write(HERE / "verification.json", {
        "status": "PASS_QR20_BOUNDED_CONTACT_VISIBILITY_REPAIR", "native": native, "rejected_mutations": rejected,
        "changed_script_sha256": script["sha256"], "compile_result_sha256": sha(compile_file),
        "archive_readback_sha256": sha(prior_readback), "runtime_test": "PENDING",
    })
    write(candidate / "package_manifest.json", {
        "status": "STAGED_QR20_SCRIPT_ONLY_NOT_INSTALLED", "predecessor": "QR19",
        "files": [{"path": p, "sha256": h, "bytes": (package / p).stat().st_size} for p, h in sorted(leaves.items())],
        "source_resources": base["source_resources"],
        "archive_source": str(QR19 / "candidate_01/archive_source"),
        "archive_readback": str(prior_readback), "archive_readback_sha256": sha(prior_readback),
        "changed_paths": [SCRIPT], "changed_depots": [], "zip": str(zip_path), "zip_sha256": sha(zip_path),
        "xl_sha256": leaves[ARCHIVE + ".xl"], "archive_sha256": leaves[ARCHIVE],
        "preservation_verified": {"installed": len(installed["core_files"]) + len(installed["required_files"]),
                                  "original_saves": len(save_rows)},
        "installed": False, "gameplay_validation": "UNTESTED",
    })
    print(f"Staged and verified {len(leaves)} files. Archive preserved: {leaves[ARCHIVE]}")


if __name__ == "__main__":
    main()
