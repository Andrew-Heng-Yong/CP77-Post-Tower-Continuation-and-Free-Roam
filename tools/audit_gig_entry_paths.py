"""Trace authored root paths to embedded gigs without guessing a tier from its name."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ROOT / "research/gig_restoration/watson_analysis/analysis.json",
    ROOT / "research/gig_restoration/fresh_candidates/local_analysis/analysis.json",
    ROOT / "research/gig_restoration/expanded_analysis/analysis.json",
]
SOURCE_ROOTS = [
    ROOT / "research/gig_restoration/watson_sources/json",
    ROOT / "research/gig_restoration/fresh_candidates/local_sources/json",
    ROOT / "research/gig_restoration/expanded_sources/json",
]


def values(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            yield obj[key]
        for value in obj.values():
            yield from values(value, key)
    elif isinstance(obj, list):
        for value in obj:
            yield from values(value, key)


def source_file(resource):
    name = resource.replace("\\", "/") + ".json"
    matches = [root / name for root in SOURCE_ROOTS if (root / name).exists()]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one source for {resource}, got {matches}")
    return matches[0]


def paths(adj, start, end, max_length=30):
    pending = [(start, [start])]
    found = []
    while pending:
        node, path = pending.pop()
        if node == end:
            found.append(path)
            continue
        if len(path) >= max_length:
            continue
        for nxt in adj[node]:
            if nxt not in path:
                pending.append((nxt, path + [nxt]))
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_id", nargs="?", help="Exact sts_ id; omit for all indexed gigs")
    parser.add_argument("--compact", action="store_true", help="One line per candidate and distinct path fact set")
    args = parser.parse_args()
    grouped = defaultdict(lambda: {"nodes": [], "edges": []})
    for path in SOURCES:
        data = json.loads(path.read_text(encoding="utf-8"))
        for kind in ("nodes", "edges"):
            for row in data[kind]:
                if row["graph"].endswith("RootChunk.graph.Data"):
                    grouped[row["resource"]][kind].append(row)
    out = []
    for resource, graph in grouped.items():
        candidates = [row for row in graph["nodes"]
                      if row["node_type"] == "questPhaseNodeDefinition"
                      and isinstance(row.get("phase_resource"), str)
                      and "\\sts_" in row["phase_resource"]]
        if not candidates:
            continue
        raw_nodes = json.loads(source_file(resource).read_text(encoding="utf-8"))["Data"]["RootChunk"]["graph"]["Data"]["nodes"]
        node_index = {row["Data"]["id"]: i for i, row in enumerate(raw_nodes)}
        node_by_id = {int(row["node_id"]): row for row in graph["nodes"]}
        adj = defaultdict(list)
        for edge in graph["edges"]:
            adj[int(edge["source_node_id"])].append(int(edge["destination_node_id"]))
        for candidate in candidates:
            phase = candidate["phase_resource"]
            cid = next((segment for segment in phase.replace("/", "\\").split("\\")
                        if segment.startswith("sts_") and segment.count("_") >= 3), None)
            if not cid or (args.candidate_id and cid != args.candidate_id):
                continue
            candidate_id = int(candidate["node_id"])
            entries = []
            for path in paths(adj, 0, candidate_id):
                gates = []
                for node_id in path:
                    row = node_by_id[node_id]
                    raw_node = raw_nodes[node_index[node_id]]["Data"]
                    inline = (raw_node.get("phaseGraph") or {}).get("Data")
                    if inline:
                        gates.append({"root_node": node_id, "inline_fact_names": sorted(set(values(inline, "factName"))),
                                      "inline_condition_types": sorted(set(values(inline, "comparisonType")))})
                    if row["node_type"] == "questPauseConditionNodeDefinition":
                        gates.append({"root_node": node_id, "condition_fact_names": sorted(set(values(raw_node.get("condition"), "factName"))),
                                      "condition_states": sorted(set(values(raw_node.get("condition"), "state")))})
                entries.append({"nodes": path, "gates": gates})
            out.append({"id": cid, "resource": resource, "phase_resource": phase,
                        "root_node": candidate_id, "paths_from_input": entries})
    out.sort(key=lambda row: row["id"])
    if args.compact:
        for row in out:
            fact_sets = sorted({"+".join(sorted({name for gate in path["gates"]
                         for name in gate.get("inline_fact_names", []) + gate.get("condition_fact_names", [])}))
                         for path in row["paths_from_input"]})
            print(f'{row["id"]}\t{" | ".join(fact_sets)}')
    else:
        print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
