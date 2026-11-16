"""Compare the actual serialized resume entrances for overlapping effects."""

import argparse
import json
import sys
from collections import defaultdict
from functools import lru_cache
from itertools import combinations
from pathlib import Path

from review_batch import HERE, REGISTRY, pinned, read, readonly, sha, write

sys.path.insert(0, str(REGISTRY))
from model import effects, journal_refs, load_export, normalize, value, walk
from trace_entries import Tracer


def body_source(folder, filename, raw_digest, export_digest):
    binary = pinned(folder, (filename, raw_digest))
    export = pinned(folder, (filename + ".json", export_digest))
    return {"binary": str(binary), "sha256": raw_digest, "export": str(export), "export_sha256": export_digest}


def parts():
    old = HERE.parent / "resume_dispatcher_rd6_gigs_20261113_01"
    plans = {q["id"]: q for q in read(old / "entrances.json")["quests"]}
    prior = read(old / "evidence_02/assessment.json")
    folder = old / "graph_02"
    assert sha(folder / "readback.json") == prior["graph_readback_sha256"]
    for row in read(folder / "readback.json")["bodies"]:
        qid = row["id"]
        assert row["sha256"] == prior["routes"][qid]["body_sha256"]
        if qid == "sts_bls_ina_07":
            successor = HERE / "minefield/graph_01"
            cooked = read(successor / "readback.json")
            assert cooked["prior_sha256"] == row["sha256"]
            assert cooked["archive_sha256"] == prior["baseline_archive_sha256"]
            depot = cooked["depot"]
            source = body_source(successor, qid + "_body.questphase", cooked["body_sha256"], cooked["export_sha256"])
        else:
            depot = "towercontinued\\native_gigs_u9\\resume\\" + qid + "_body.questphase"
            source = body_source(folder, qid + "_body.questphase", row["sha256"], row["export_sha256"])
        yield qid, depot, plans[qid]["socket"], {depot: source}

    for subdir, plan_name in (("base", "empathy.json"), ("ep1", "plan.json"), ("ep1/symptoms", "plan.json")):
        folder = HERE / subdir / "graph_01"
        spec = read(HERE / subdir / plan_name)
        row = read(folder / "readback.json")
        qid = spec.get("id", spec.get("quest"))
        depot = spec.get("depot", spec.get("private_depot"))
        yield qid, depot, spec["socket"], {depot: body_source(folder, qid + "_body.questphase", row["body_sha256"], row["export_sha256"])}

    spec = read(HERE / "jobs/entrance.json")
    folder = HERE / "jobs/graph_03"
    jobs_proof = read(HERE / "jobs/evidence_02/assessment.json")
    readback = read(pinned(folder, ("readback.json", jobs_proof["readback_sha256"])))
    sources = {row["depot"]: body_source(folder, row["name"] + ".questphase", row["raw_sha256"], row["export_sha256"])
               for row in readback["resources"]}
    yield spec["quest"], spec["prefix"] + "root.questphase", spec["socket"], sources


class EntranceTrace(Tracer):
    def __init__(self, db, sources):
        super().__init__(db)
        self.bodies = {}
        for index, (depot, source) in enumerate(sources.items(), 1):
            assert depot not in self.winners, depot
            self.winners[depot] = -index
            self.bodies[-index] = {g["path"]: g for g in normalize(load_export(source["export"]))["graphs"]}
        self.root_selection = None

    @lru_cache(maxsize=128)
    def graph(self, rid, path):
        if rid >= 0:
            return super().graph(rid, path)
        graph = self.bodies[rid].get(path)
        if graph is None:
            return None
        nodes = {node["id"]: node for node in graph["nodes"]}
        entries = defaultdict(list)
        for node in graph["inputs"]:
            entries[str(value(nodes[node]["parameters"].get("socketName", "")))].append(node)
        assert not graph["unresolved_connections"]
        if self.root_selection and (rid, path) == self.root_selection[:2]:
            socket = self.root_selection[2]
            assert len(entries[socket]) == 1, (rid, socket)
            entries = {socket: entries[socket]}
        fields = ("source", "source_socket", "source_type", "destination", "destination_socket", "destination_type")
        return {"kind": graph["kind"], "nodes": nodes, "entries": entries,
                "edges": [dict(zip(fields, edge, strict=True)) for edge in graph["edges"]]}

    def entrance(self, depot, socket):
        self.root_selection = self.winners[depot], "root", socket
        self.graph.cache_clear()
        return self.trace(depot)

    def footprint(self, reached):
        result = defaultdict(set)
        for rid, path, node in reached:
            params = self.graph(rid, path)["nodes"][node]["parameters"]
            if any(row.get("$type") == "questJournalNodeDefinition" for row in walk(params)):
                result["journal_writes"].update(ref for ref, _ in journal_refs(params))
            for row in effects(params):
                kind = row["$type"]
                if kind == "questSetVar_NodeType" and row.get("factName"):
                    result["fact_writes"].add(row["factName"])
                if kind == "questGiveReward_NodeType":
                    result["reward_targets"].update(str(value(target)) for target in row.get("rewards", []))
                if kind == "questAddRemoveItem_NodeTypeParams" and "itemID" in row:
                    item = value(row["itemID"])
                    if isinstance(item, (str, int)) and item not in ("0", "None", 0):
                        result["inventory_targets"].add(str(item))
        return {field: sorted(keys) for field, keys in result.items()}


def compare(out, evidence):
    assert out.parent == HERE and out.name.startswith("coordination_") and not out.exists()
    manifest = read(evidence / "manifest.json")
    packets = read(pinned(evidence, ("review_packets.json", manifest["files"]["review_packets.json"])))
    qualified = {row["rid"] for row in packets["provider_review"] if row["status"] == "EXACT_CURRENT_PROVIDER"}
    journal_roots = {row["id"]: row["journal_root"] for row in packets["quests"]}
    groups = list(parts())
    sources = {depot: body for _, _, _, bodies in groups for depot, body in bodies.items()}
    assert len(sources) == sum(len(bodies) for _, _, _, bodies in groups)
    reviews = {}
    with readonly("registry") as db:
        tracer = EntranceTrace(db, sources)
        for qid, depot, socket, _ in groups:
            contexts, reached, links, boundaries = tracer.entrance(depot, socket)
            assert (tracer.winners[depot], "root", socket) in contexts and reached
            external = {rid for rid, _, _ in reached if rid >= 0}
            footprint = tracer.footprint(reached)
            foreign = {other: [path for path in footprint.get("journal_writes", []) if path == root or path.startswith(root + "/")]
                       for other, root in journal_roots.items() if other != qid}
            reviews[qid] = {"depot": depot, "socket": socket, "reached_nodes": len(reached),
                            "interfaces": len(links), "boundaries": boundaries, "footprint": footprint,
                            "writes_to_other_reviewed_quests": {other: paths for other, paths in foreign.items() if paths},
                            "external_providers_without_exact_batch_match": sorted(external - qualified)}
    expected_quests = {row["id"] for row in packets["quests"]
                       if row["group"] != "regressions" and row["offline_fixture"]["fields"]}
    assert set(reviews) == expected_quests and len(reviews) == len(groups)
    for qid, review in reviews.items():
        assert not review["writes_to_other_reviewed_quests"], qid
        assert not review["boundaries"], (qid, review["boundaries"])
        assert not review["external_providers_without_exact_batch_match"], qid
    overlaps = []
    for left, right in combinations(sorted(reviews), 2):
        a, b = (reviews[q]["footprint"] for q in (left, right))
        shared = {key: sorted(set(values).intersection(b.get(key, []))) for key, values in a.items()}
        if any(shared.values()):
            overlaps.append({"quests": [left, right], "shared": {key: v for key, v in shared.items() if v}})
    out.mkdir()
    write(out / "assessment.json", {
        "status": "UNREGISTERED_ENTRANCE_MAY_TRACE", "input_manifest_sha256": sha(evidence / "manifest.json"),
        "tool_sha256": sha(__file__), "resources": sources, "quests": reviews, "overlaps": overlaps,
        "limits": [
            "Traversal follows local directed edges and selected child inputs. A return edge or conditional path may never execute.",
            "This starts at serialized stage inputs and excludes enclosing support and credit owners unless called from that input.",
            "No saved-owner, timing, concurrent gameplay, or runtime admission result is implied.",
        ],
    })
    print(json.dumps({"stage_entrances": len(reviews), "pairs_with_shared_effects": len(overlaps),
                      "boundaries": sum(len(r["boundaries"]) for r in reviews.values()),
                      "entrances_with_cross_quest_journal_writes": sum(bool(r["writes_to_other_reviewed_quests"]) for r in reviews.values())},
                     indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    compare(args.output.resolve(), args.evidence.resolve())
