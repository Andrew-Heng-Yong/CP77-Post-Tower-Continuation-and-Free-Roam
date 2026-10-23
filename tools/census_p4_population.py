"""Summarize indexed q307 population actions without inferring runtime liveness."""
import json
from collections import Counter
from pathlib import Path

from report_q307_lifecycle import reachable

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "research/q307_analysis/analysis.json").read_text(encoding="utf-8"))
names = ("q307_despawn.questphase", "q307_09_cutscene.questphase", "q307_cleanup.questphase")
out = {}
for name in names:
    nodes = [n for n in data["nodes"] if n["resource"].endswith("\\" + name)]
    graphs = {}
    for graph in sorted({n["graph"] for n in nodes}):
        selected = [n for n in nodes if n["graph"] == graph]
        edges = [e for e in data["edges"] if e["graph"] == graph]
        inputs = [n["node_id"] for n in selected if n["node_type"] == "questInputNodeDefinition"]
        reached = set().union(*(reachable(i, edges) for i in inputs)) if inputs else set()
        actions = []
        for node in selected:
            if node["node_type"] != "questSpawnManagerNodeDefinition":
                continue
            details = node["details"]
            for key, value in details.items():
                if not key.endswith(".type.Data.action"):
                    continue
                prefix = key.rsplit("action", 1)[0]
                actions.append({"node_id": node["node_id"], "action_index": int(key.split(".")[1]),
                                "reachable_from_graph_input": node["node_id"] in reached,
                                "action": value,
                                "type": details.get(prefix + "$type"),
                                "reference": details.get(prefix + "spawnerReference", details.get(prefix + "reference")),
                                "entry": details.get(prefix + "communityEntryName", details.get(prefix + "entryName"))})
        active = [a for a in actions if a["reachable_from_graph_input"]]
        refs = sorted({a["reference"] for a in active if a["action"] == "Deactivate"
                       and a["reference"] not in (None, "0", "None", "")})
        graphs[graph] = {"inputs": inputs, "reachable_nodes": sorted(reached),
                         "action_counts_reachable": dict(Counter(a["action"] for a in active)),
                         "unique_deactivated_refs": refs, "actions": actions}
    out[name] = graphs
dest = ROOT / "research/phase2b_p4/population_actions.json"
dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
for name, graphs in out.items():
    for graph, report in graphs.items():
        print(name, graph.split("::")[-1], report["action_counts_reachable"],
              "unique deactivation refs", len(report["unique_deactivated_refs"]))
        unreachable = [a for a in report["actions"] if not a["reachable_from_graph_input"]]
        print("Unreachable action count:", len(unreachable),
              "node IDs:", sorted({a["node_id"] for a in unreachable}))
