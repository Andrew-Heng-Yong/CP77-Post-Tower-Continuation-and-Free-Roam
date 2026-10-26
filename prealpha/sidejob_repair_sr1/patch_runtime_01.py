"""Keep S29 runtime admission aligned with its staged native Delamain guard."""
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parents[2]
O = Path(__file__).resolve().parent
plan = json.loads((O / "plan_01.json").read_text(encoding="utf-8"))
source = Path(plan["reds_s29"]["path"])
raw = source.read_bytes()
assert hashlib.sha256(raw).hexdigest().upper() == plan["reds_s29"]["sha256"]
text = raw.decode("utf-8")
predecessor = {
    "contacts/delamain/sq025_divergent_found/all_found",
    "contacts/delamain/sq025_divergent_found/all_returned_ch",
    "contacts/delamain/sq025_divergent_found/all_returned_ch/all_returned_ch_01",
    "contacts/delamain/sq025_divergent_found/all_returned_response",
    "contacts/delamain/sq025_scan_damage/sq025_scan_damaged",
    "contacts/delamain/sq025_scan_damage/sq025_scan_destroyed",
    "contacts/delamain/sq025_scan_damage/sq025_scan_left",
}
lines = text.splitlines(keepends=True)
arrays = {}
positions = {}
for i, line in enumerate(lines):
    for name in ("Paths12", "Classes12", "StatesA12", "StatesB12"):
        if f"func {name}()" not in line:
            continue
        assert name not in arrays and "return [" in line and "]; }" in line
        payload = line.split("return ", 1)[1].split("; }", 1)[0]
        arrays[name] = json.loads(payload)
        positions[name] = (i, payload)
assert len(arrays) == 4
length = len(arrays["Paths12"])
assert all(len(v) == length for v in arrays.values())
removed = [i for i, path in enumerate(arrays["Paths12"]) if path in predecessor]
assert len(removed) == 7 and {arrays["Paths12"][i] for i in removed} == predecessor
assert all(arrays["StatesA12"][i] == 1 and arrays["StatesB12"][i] == 1 for i in removed)
for name, (i, old) in positions.items():
    new_values = [v for j, v in enumerate(arrays[name]) if j not in removed]
    new = json.dumps(new_values, ensure_ascii=False, separators=(", ", ": "))
    lines[i] = lines[i].replace(old, new)
    assert len(new_values) == length - 7
text = "".join(lines)
anchor = "  private func Common() -> Bool {"
assert text.count(anchor) == 1
method = """  // The S25 fresh owner starts the persistent native Delamain phone controller.
  // Saved S25 owners from before SR1 need its shared receipt adopted once,
  // after their original completion; no native message or controller is replayed.
  private func AdoptS25DelamainPhone() -> Void {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(qs) || !this.Common() { return; }
    if qs.GetFactStr("PTFRS25_SQ025_FRESH_Issued") != 1 ||
      qs.GetFactStr("PTFRS25_SQ025_FRESH_Finished") != 1 ||
      qs.GetFactStr("PTFRS25_SQ025_FRESH_Fault") != 0 { return; }
    if qs.GetFactStr("PTFRS22_SQ025_SupportIssued") == 0 {
      qs.SetFactStr("PTFRS22_SQ025_SupportIssued", 1);
    }
  }
"""
newline = "\r\n" if "\r\n" in text else "\n"
text = text.replace(anchor, method.replace("\n", newline) + anchor)
poll_anchor = "    if ArraySize(this.previous) != SideJobDataS29.Count() { this.Restored(); return; }"
assert text.count(poll_anchor) == 1
text = text.replace(poll_anchor, poll_anchor + newline + "    this.AdoptS25DelamainPhone();")
out = O / "candidate_02/source_scripts/r6/scripts/TowerContinued_SideJobs_S29/SideJobsS29.reds"
assert not out.exists()
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(text.encode("utf-8"))
assert out.read_bytes().decode("utf-8").count("AdoptS25DelamainPhone()") == 2
proof = {
    "status": "STAGED_RUNTIME_PREDECESSOR_FILTER_AND_S25_PHONE_ADOPTION",
    "source": str(source),
    "source_sha256": plan["reds_s29"]["sha256"],
    "output": str(out.relative_to(W)).replace("\\", "/"),
    "output_sha256": hashlib.sha256(out.read_bytes()).hexdigest().upper(),
    "removed_predecessor_paths": sorted(predecessor),
    "old_paths": length,
    "new_paths": length - 7,
    "phone_receipt_adoption": "S25 Issued=1 Finished=1 Fault=0 and genuine Common=1; only PTFRS22_SQ025_SupportIssued 0->1",
    "game_writes": 0,
    "save_writes": 0,
}
p = O / "candidate_02/patch_runtime_01.json"
assert not p.exists()
p.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"removed_paths": len(removed), "old_paths": length, "new_paths": length - 7, "output_sha256": proof["output_sha256"]}))
