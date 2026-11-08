"""Make the retained Bartmoss thread visible for an entered MQ018 handoff."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
QR19 = HERE.parent / "quest_restoration_qr19"
SCRIPT = "r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds"
INSTALLED_PIN = "B926963B5BA85B95E8F371DBB00720A37793E5BC3E9904F770A220B8AED89784"
PACKAGE_PIN = "7259E12EABB61A8253F50A22BE6198DA7CFECA65692D99C37AE7283F2ADE942D"
METHOD = '''  private func RestoreMQ018MessageContact() -> Void {
    if this.Own(2, "Issued") != 1 || this.Own(2, "Entered") != 1 ||
       this.Own(2, "Finished") != 0 || this.Own(2, "Fault") != 0 ||
       this.Fact("PTFRS29_PHONE_nancy_Issued") != 1 || !this.HasMQ018Reservation() ||
       this.Fact("mq018_visit_website") != 0 {
      return;
    }
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    if !IsDefined(jm) {
      return;
    }
    let path = "contacts/bartmoss";
    let className = "gameJournalContact";
    let contact = jm.GetEntryByString(path, className) as JournalContact;
    if !IsDefined(contact) || !Equals(jm.GetEntryState(contact), gameJournalEntryState.Inactive) ||
       !Equals(contact.GetType(), gameContactType.Texter) || contact.IsCallable(jm) {
      return;
    }
    if this.Common() && this.Safe() && this.Read(2).valid {
      jm.ChangeEntryState(path, className, gameJournalEntryState.Active, JournalNotifyOption.DoNotNotify);
    }
  }
'''


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest().upper()


def checked(path, expected):
    path = Path(path)
    assert sha(path) == expected, path
    return path


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, content):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(content, indent=2) + "\n")


def inputs():
    installed = read(checked(QR19 / "deployment_01/installed_manifest_01.json", INSTALLED_PIN))
    assert installed["core_epoch"] == "QR19"
    base = read(checked(installed["core_source_epoch"], PACKAGE_PIN))
    assert base["files"] == installed["core_files"]
    return installed, base


def main():
    output = HERE / "proposal_02"
    assert not output.exists()
    installed, base = inputs()
    leaves = {r["path"]: r["sha256"] for r in base["files"]}
    checked(Path(installed["game_root"]) / SCRIPT, leaves[SCRIPT])
    predecessor = checked(QR19 / "candidate_01/package" / SCRIPT, leaves[SCRIPT])
    text = predecessor.read_text(encoding="utf-8-sig")
    anchor = "  private func Unclaimed(i: Int32) -> Bool {"
    tick = "    this.AdoptS25DelamainPhone();"
    assert text.count(anchor) == text.count(tick) == 1
    text = text.replace(anchor, METHOD + anchor).replace(tick, tick + "\n    this.RestoreMQ018MessageContact();")
    output.mkdir()
    path = output / Path(SCRIPT).name
    path.write_text(text, encoding="utf-8", newline="\n")
    write(output / "plan.json", {"script": {"path": SCRIPT, "source": str(path), "sha256": sha(path)}})


if __name__ == "__main__":
    main()
