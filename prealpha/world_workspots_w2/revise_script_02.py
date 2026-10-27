"""Avoid 1,030 quest-fact reads per unrelated NPC during periodic scans."""
from hashlib import sha256
from pathlib import Path
import json
import shutil

H = Path(__file__).resolve().parent
old = H / "candidate_01"
new = H / "candidate_02"
assert not new.exists(), "Preserve old candidate"
source = old / "script_source/PTFR_RestorationBaseline.reds"
text = source.read_text(encoding="utf-8")
before = '''    let i = 0;
    while i < ArraySize(this.groups) {
      if this.Open(q,i) {
        let j = 0;
        while j < ArraySize(this.groups[i].spawners) {
          if stub.GetSpawnerID() == this.groups[i].spawners[j] {
'''
after = '''    let sourceID = stub.GetSpawnerID();
    let i = 0;
    while i < ArraySize(this.groups) {
      let j = 0;
      while j < ArraySize(this.groups[i].spawners) {
        if sourceID == this.groups[i].spawners[j] && this.Open(q,i) {
'''
end_before = '''          }
          j += 1;
        }
      }
      i += 1;
    }
  }
  private func Proven'''
end_after = '''        }
        j += 1;
      }
      i += 1;
    }
  }
  private func Proven'''
assert text.count(before) == text.count(end_before) == 1
text = text.replace(before, after).replace(end_before, end_after)
new.mkdir()
shutil.copytree(old / "package", new / "package")
target = new / "package/r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds"
target.write_text(text, encoding="utf-8", newline="\n")
script = new / "script_source/PTFR_RestorationBaseline.reds"
script.parent.mkdir()
script.write_text(text, encoding="utf-8", newline="\n")
same = ["archive/pc/mod/zzzz_PTFR_Combined.archive", "archive/pc/mod/zzzz_PTFR_Combined.archive.xl"]
digest = lambda p: sha256(p.read_bytes()).hexdigest().upper()
assert all(digest(old / "package" / p) == digest(new / "package" / p) for p in same)
proof = {"status": "W2_SCRIPT_SCAN_ORDER_SUCCESSOR_NOT_COMPILED_OR_INSTALLED",
         "old_script_sha256": digest(source), "new_script_sha256": digest(script),
         "archive_and_xl_byte_identical": True, "package_paths": len(list((new / "package").rglob("*.*"))),
         "game_writes": 0, "save_writes": 0}
(new / "revision_01.json").write_text(json.dumps(proof,indent=2)+"\n",encoding="utf-8")
print(json.dumps(proof,indent=2))
