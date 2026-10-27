"""Keep W2's proven scan ordering in the 237-owner W3 successor."""
from hashlib import sha256
from pathlib import Path
import json

H=Path(__file__).resolve().parent
src=H/"candidate_03/script_source/PTFR_RestorationBaseline.reds"
dst=H/"candidate_04/script_source/PTFR_RestorationBaseline.reds"
assert not dst.exists(),"Preserve previous script"
text=src.read_text(encoding="utf-8")
before='''    let i = 0;
    while i < ArraySize(this.groups) {
      if this.Open(q,i) {
        let j = 0;
        while j < ArraySize(this.groups[i].spawners) {
          if stub.GetSpawnerID() == this.groups[i].spawners[j] {
'''
after='''    let sourceID = stub.GetSpawnerID();
    let i = 0;
    while i < ArraySize(this.groups) {
      let j = 0;
      while j < ArraySize(this.groups[i].spawners) {
        if sourceID == this.groups[i].spawners[j] && this.Open(q,i) {
'''
tail='''          }
          j += 1;
        }
      }
      i += 1;
    }
  }
  private func Proven'''
newtail='''        }
        j += 1;
      }
      i += 1;
    }
  }
  private func Proven'''
assert text.count(before)==text.count(tail)==1
text=text.replace(before,after).replace(tail,newtail)
dst.parent.mkdir(parents=True)
dst.write_text(text,encoding="utf-8",newline="\n")
proof={"status":"W3_237_GROUP_SCRIPT_STAGED_NOT_COMPILED_OR_INSTALLED",
 "before_sha256":sha256(src.read_bytes()).hexdigest().upper(),
 "after_sha256":sha256(dst.read_bytes()).hexdigest().upper(),
 "group_count":237,"spawner_count":245,"game_writes":0,"save_writes":0}
(dst.parent/"build_01.json").write_text(json.dumps(proof,indent=2)+"\n",encoding="utf-8")
print(json.dumps(proof,indent=2))
