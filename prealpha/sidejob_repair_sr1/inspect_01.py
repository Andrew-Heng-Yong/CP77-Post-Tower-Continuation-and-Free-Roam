"""Print bounded quest-port facts needed by the staged graph edits."""
import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "tools"))
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten

plan = json.loads((Path(__file__).parent / "plan_01.json").read_text(encoding="utf-8"))
sources = {r["depot"]: r for r in plan["installed"]}
inventory = json.loads((W / "diagnostics/restored_audit_20261025_01/installed_01/inventory.json").read_text(encoding="utf-8"))
refs = {r["depot"]: r["json"] for r in inventory["resources"]}
selected = [
    (W / "research/sidejobs_s29/native_01/basegame_4_gamedata/json/base/quest/default_dialogs.questphase.json", "root/7", [25, 26]),
    (W / refs[r"towercontinued\sidejobs_s23\base_b\mq030.questphase"], "root", [1006, 1020]),
    (W / refs[r"towercontinued\sidejobs_s29\entries\mq058_semimaru_crystalcoat.questphase"], "root", [64000, 65007]),
    (W / refs[r"towercontinued\sidejobs_s25\families\sq025_fresh.questphase"], "root", [92, 94, 95, 100]),
]
for path, graph_name, ids in selected:
    obj = json.loads(path.read_text(encoding="utf-8"))
    graph = next(g for g in flatten(SafeResource(obj), obj["Data"]["RootChunk"]) if g["path"] == graph_name)
    nodes = [n for n in graph["nodes"] if n["id"] in ids]
    edges = [e for e in graph["edges"] if e[0] in ids or e[2] in ids]
    print(json.dumps({"resource": str(path.relative_to(W)).replace("\\", "/"), "graph": graph_name, "nodes": [{"id": n["id"], "type": n["$type"], "sockets": [(s.get("name"), s.get("type")) for s in n.get("sockets", [])]} for n in nodes], "edges": edges}, indent=2))
