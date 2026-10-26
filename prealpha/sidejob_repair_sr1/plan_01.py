"""Pin the installed resources and current native donors for a staged side-job repair."""
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parents[2]
O = Path(__file__).resolve().parent
inventory = json.loads((W / "diagnostics/restored_audit_20261025_01/installed_01/inventory.json").read_text(encoding="utf-8"))
installed = {r["depot"]: r for r in inventory["resources"]}
depots = [
    r"towercontinued\b0_story_eight\yoko.scene",
    r"towercontinued\sidejobs_s23\base_b\mq030.questphase",
    r"towercontinued\sidejobs_s29\entries\mq058_semimaru_crystalcoat.questphase",
    r"towercontinued\sidejobs_s25\families\sq025_fresh.questphase",
    r"towercontinued\sidejobs_s29\entries\sq025b_delamain_insurgence.questphase",
    r"towercontinued\sidejobs_s29\phone\delamain.questphase",
]
sources = []
for depot in depots:
    r = installed[depot]
    raw = W / r["raw"]
    assert raw.is_file()
    digest = hashlib.sha256(raw.read_bytes()).hexdigest().upper()
    assert digest == r["sha256"].upper(), depot
    sources.append({"depot": depot, "raw": r["raw"], "sha256": digest, "archive": r["archive"]})
yoko_proof = json.loads((W / "diagnostics/restored_audit_20261025_03/sidejobs/yoko_corrosion_02.json").read_text(encoding="utf-8"))
yoko = next(r for r in yoko_proof["current_resources"] if r["depot"] == depots[0])
assert hashlib.sha256((W / yoko["raw"]).read_bytes()).hexdigest().upper() == yoko["sha256"].upper()
assert yoko["sha256"].upper() == sources[0]["sha256"]
native_bullets = W / "research/sidejobs_s29/native_01/basegame_4_gamedata/raw/base/quest/default_dialogs.questphase"
assert native_bullets.is_file()
native_yoko = W / "diagnostics/restored_audit_20261025_03/dialogue/native_01/15651456292936307253.scene.json"
assert native_yoko.is_file()
reds = Path(r"C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/r6/scripts/TowerContinued_SideJobs_S29/SideJobsS29.reds")
assert reds.is_file()
result = {
    "status": "PINNED_STAGED_REPAIR_INPUTS_NO_GAME_WRITES",
    "installed": sources,
    "native_bullets": {"path": str(native_bullets.relative_to(W)).replace("\\", "/"), "sha256": hashlib.sha256(native_bullets.read_bytes()).hexdigest().upper()},
    "native_yoko_json": {"path": str(native_yoko.relative_to(W)).replace("\\", "/"), "sha256": hashlib.sha256(native_yoko.read_bytes()).hexdigest().upper()},
    "reds_s29": {"path": str(reds), "sha256": hashlib.sha256(reds.read_bytes()).hexdigest().upper()},
    "game_writes": 0,
    "save_writes": 0,
}
p = O / "plan_01.json"
assert not p.exists()
p.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"pinned_installed": len(sources), "native_bullets": result["native_bullets"]["sha256"], "reds": result["reds_s29"]["sha256"]}))
