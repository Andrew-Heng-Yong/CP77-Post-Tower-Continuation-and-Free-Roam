"""Map caller-connected phase addresses, scene callers, and ArchiveXL bindings."""

import argparse
import json
import sys
from binascii import crc_hqx
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

from prepare_review import HERE, PRIOR, REG, ROOT, ROOTS, db_readonly, depot_key, read, sha, write
from review_sources import COMBINED, require, verify_providers

sys.path.insert(0, str(REG))
from model import journal_refs, load_export, normalize, value, walk  # noqa: E402

PHASE = "questPhaseNodeDefinition"
START = "questStartNodeDefinition"
INPUT = "questInputNodeDefinition"
CUTOFFS = ("\\q115_00_hanako.questphase", "\\q307_01_pickup.questphase")


def by_name(value_in):
    return str(value(value_in))


def ref_value(data):
    return by_name(data.get("DepotPath", "0")).lower().replace("/", "\\")


def node_refs(items):
    return sorted({by_name(item) for item in walk(items)
                   if item.get("$type") == "NodeRef" and by_name(item) not in {"0", "", "None"}})


class Sources:
    def __init__(self, db, plan, seen, review):
        self.db = db
        self.rows = {row["rid"]: row for row in plan["qp2_providers"]}
        self.by_key = defaultdict(list)
        for row in self.rows.values():
            self.by_key[row["key"]].append(row["rid"])
        self.locations = {
            rid: Path(row["archive"]).relative_to(Path(plan["game_root"])).as_posix()
            for rid, row in self.rows.items()
        }
        self.seen = seen
        self.known_equivalent = {depot_key(row["depot"]) for row in review["graph_variants"]
                                 if row["contract_input"] == "SAME_GRAPH_AND_PREFAB_REFERENCES"}
        self.deltas = {}
        manifest = read(PRIOR / "delta_capture_01/manifest.json")
        item_hashes = {row["key"]: row["sha256"] for row in plan["rd10_members"]}
        for index, row in enumerate(manifest["rows"], 1):
            key = depot_key(row["depot"])
            require(seen[key, COMBINED] == row["sha256"] == item_hashes[key], "RD10 delta changed")
            source = Path(row["export"])
            require(sha(source) == row["export_sha256"], "RD10 graph export changed")
            data = normalize(load_export(source))
            rid = -index
            self.rows[rid] = {"depot": row["depot"], "key": key, "sha256": row["sha256"],
                              "status": "RD10_EXACT_DELTA", "role": "PTFR"}
            self.by_key[key].append(rid)
            self.locations[rid] = COMBINED
            self.deltas[rid] = data

    @lru_cache(maxsize=None)
    def select(self, name, authored_only=False):
        key = depot_key(name)
        candidates = [rid for rid in self.by_key.get(key, ())
                      if self.seen.get((key, self.locations[rid])) == self.rows[rid]["sha256"]]
        combined = [rid for rid in candidates if self.locations[rid] == COMBINED]
        stock = [rid for rid in candidates if self.rows[rid]["role"] == "STOCK"]
        external = [rid for rid in candidates if self.rows[rid]["role"] == "OTHER_MOD"]
        if authored_only:
            candidates = stock
        elif combined and not external:
            candidates = combined
        if not candidates:
            return None, "UNVERIFIED_PROVIDER"
        same_bytes = len({self.rows[rid]["sha256"] for rid in candidates}) == 1
        if not same_bytes and key not in self.known_equivalent:
            return None, "DISTINCT_PROVIDER_VARIANTS"
        return candidates[0], ("SAME_PAYLOAD" if same_bytes else "EQUIVALENT_NORMALIZED_PHASE_VARIANTS")

    @lru_cache(maxsize=384)
    def graph(self, rid, graph):
        if rid < 0:
            data = next((g for g in self.deltas[rid]["graphs"] if g["path"] == graph), None)
            if data is None:
                return None
            return (data["kind"], {n["id"]: n for n in data["nodes"]}, tuple(data["edges"]))
        raw = self.db.execute("SELECT kind FROM graphs WHERE rid=? AND path=?", (rid, graph)).fetchone()
        if raw is None:
            return None
        nodes = {row["id"]: {"id": row["id"], "type": row["type"],
                            "parameters": json.loads(row["parameters_json"]), "sockets": json.loads(row["sockets_json"])}
                 for row in self.db.execute("SELECT * FROM nodes WHERE rid=? AND graph=?", (rid, graph))}
        edges = self.db.execute("""SELECT source,source_socket,source_type,destination,destination_socket,destination_type
                                  FROM edges WHERE rid=? AND graph=?""", (rid, graph))
        return (raw["kind"], nodes, tuple(map(tuple, edges)))

    @lru_cache(maxsize=384)
    def support(self, rid, graph):
        if rid < 0:
            root = self.deltas[rid]["support"]
        else:
            raw = self.db.execute("SELECT support_json FROM resources WHERE rid=?", (rid,)).fetchone()[0]
            root = json.loads(raw) if raw else {}
        owner = root
        for item in root.get("embedded_resources", []):
            name = item["depot"]
            if graph == f"embedded/{name}/root" or graph.startswith(f"embedded/{name}/root/"):
                owner = item["parameters"]
                break
        return owner

    @lru_cache(maxsize=None)
    def embedded(self, rid, target):
        if rid < 0:
            candidates = [g["path"] for g in self.deltas[rid]["graphs"] if g["path"].startswith("embedded/")]
        else:
            candidates = [r[0] for r in self.db.execute(
                "SELECT path FROM graphs WHERE rid=? AND path LIKE 'embedded/%/root'", (rid,))]
        matches = [path for path in candidates if path.endswith("/root")
                   and depot_key(path.removeprefix("embedded/").removesuffix("/root")) == depot_key(target)]
        return matches[0] if len(matches) == 1 else None

    def has_graph(self, rid, graph):
        if rid < 0:
            return any(g["path"] == graph for g in self.deltas[rid]["graphs"])
        return self.db.execute("SELECT 1 FROM graphs WHERE rid=? AND path=?", (rid, graph)).fetchone() is not None


def registrations(sources, bindings):
    """The generated ID is local to the graph containing the input node."""
    indexed = defaultdict(list)
    missing = []
    collisions = []
    ids = {}
    rows = []
    for record in bindings:
        binding = record["binding"]
        parent, reason = sources.select(binding["parent"])
        raw = binding.get("input", binding.get("connection", []))
        if parent is None:
            missing.append({**record, "reason": reason})
            continue
        raw_path = raw["node"] if isinstance(raw, dict) else raw
        input_socket = raw.get("socket", "Out") if isinstance(raw, dict) else "Out"
        path = tuple(map(int, raw_path))
        if not path:
            graph = sources.graph(parent, "root")
            starters = () if graph is None else tuple(n for n, row in graph[1].items() if row["type"] == START)
            if len(starters) != 1:
                missing.append({**record, "reason": "PARENT_START_NODE_UNRESOLVED"})
                continue
            path = starters
        graph_name = "/".join(("root", *map(str, path[:-1])))
        graph = sources.graph(parent, graph_name)
        if graph is None or path[-1] not in graph[1]:
            missing.append({**record, "reason": "PARENT_CONNECTION_NODE_UNRESOLVED"})
            continue
        child_id = crc_hqx(f"{binding['path']}:{path[-1]}".encode("utf-8"), 0xFFFF)
        identity = parent, graph_name, child_id
        row = {**record, "parent_rid": parent, "graph": graph_name,
               "input_node": path[-1], "input_socket": input_socket, "generated_node": child_id}
        rows.append(row)
        if child_id in graph[1] or identity in ids:
            collisions.append({"registration": row, "authored_node": child_id in graph[1],
                               "preceding_registration": ids.get(identity)})
        else:
            ids[identity] = row
            indexed[parent, graph_name, path[-1]].append(row)
    return indexed, rows, collisions, missing


def local_reach(sources, rid, graph, entry):
    body = sources.graph(rid, graph)
    if body is None:
        return None, "UNDECODED_GRAPH"
    kind, nodes, edges = body
    if kind == "quest":
        seeds = [nid for nid, row in nodes.items() if
                 (entry is None and row["type"] == START) or
                 (entry is not None and row["type"] == INPUT and by_name(row["parameters"].get("socketName")) == entry)]
    else:
        support = sources.support(rid, graph)
        seeds = [value(row["nodeId"]) for row in support.get("entryPoints", [])
                 if by_name(row["name"]) == entry]
    if len(seeds) != 1:
        return None, "MISSING_INPUT" if not seeds else "AMBIGUOUS_INPUT"
    flow = defaultdict(list)
    for src, output, src_type, dest, port, dest_type in edges:
        if src_type == "Output" and dest_type == "Input":
            flow[src].append((output, dest, port))
    reached = set(seeds)
    pending = list(seeds)
    incoming = defaultdict(set)
    used_outputs = defaultdict(set)
    while pending:
        src = pending.pop()
        for output, dest, port in flow[src]:
            if dest not in nodes:
                continue
            incoming[dest].add(port)
            used_outputs[src].add(output)
            if dest not in reached:
                reached.add(dest)
                pending.append(dest)
    return (reached, incoming, used_outputs, seeds[0]), None


class Trace:
    def __init__(self, sources, hooks):
        self.sources = sources
        self.hooks = hooks
        self.scopes = []
        self.boundaries = []
        self.by_location = defaultdict(set)
        self.native_by_address = defaultdict(set)
        self.visited = set()
        self.reach = lru_cache(maxsize=256)(lambda rid, graph, entry: local_reach(sources, rid, graph, entry))

    def run(self):
        pending = []
        for root_number, depot in enumerate(ROOTS):
            rid, reason = self.sources.select(depot)
            require(rid is not None, f"Root provider {depot}: {reason}")
            pending.append((rid, "root", None, (root_number,), (), None, None, (), ()))
        while pending:
            rid, graph, entry, address, scene, parent, incoming_call, host_resources, ancestors = pending.pop()
            state = rid, graph, entry
            if state in ancestors:
                self.boundaries.append({"reason": "CYCLIC_RESOURCE_ENTRY", "state": state, "parent": parent})
                continue
            scope_key = rid, graph, entry, address, scene, parent
            if scope_key in self.visited:
                continue
            self.visited.add(scope_key)
            reached, reason = self.reach(rid, graph, entry)
            if reached is None:
                self.boundaries.append({"reason": reason, "state": state, "address": address,
                                        "scene": scene, "parent": parent, "incoming": incoming_call})
                continue
            kind, nodes, edges = self.sources.graph(rid, graph)
            active_nodes, inputs, outputs, seed = reached
            idx = len(self.scopes)
            owner = self.sources.rows[rid]
            scope = {"index": idx, "rid": rid, "depot": owner["depot"], "sha256": owner["sha256"],
                     "graph": graph, "entry": entry, "entry_node": seed, "kind": kind,
                     "address": address if not scene else None, "scene_callers": scene,
                     "parent": parent, "incoming": incoming_call}
            self.scopes.append(scope)
            if not scene:
                self.native_by_address[address].add(idx)
            physical_parents = (rid, *tuple(r for r in host_resources if r != rid))
            next_ancestors = (*ancestors, state)

            def enter(target_rid, child_graph, socket, child_address, child_scene, node, leg):
                pending.append((target_rid, child_graph, socket, child_address, child_scene, idx,
                                {"node": node, "input": socket, "kind": leg},
                                physical_parents, next_ancestors))

            for nid in sorted(active_nodes):
                self.by_location[rid, graph, nid].add(idx)
                row = nodes[nid]
                params = row["parameters"]
                condition_inputs = inputs[nid]
                if kind == "scene" and row["type"] == "scnQuestNode":
                    mappings = params.get("isockMappings", [])
                    condition_inputs = {
                        by_name(mappings[stamp["ordinal"]]) for raw in condition_inputs
                        if (stamp := json.loads(raw)).get("name") == 0 and 0 <= stamp.get("ordinal", -1) < len(mappings)
                    }
                    params = params.get("questNode") or {}
                if params.get("$type") == PHASE:
                    self.phase_child(enter, idx, physical_parents, rid, graph, params, nid,
                                     condition_inputs, address, scene)
                if "sceneFile" in params:
                    target = ref_value(params["sceneFile"])
                    self.scene_child(enter, idx, nid, target, condition_inputs, address, scene)
                for binding in self.hooks.get((rid, graph, nid), ()):
                    outport = binding["input_socket"]
                    # ArchiveXL can add an output socket absent from vanilla.
                    # No condition is assumed true by indexing this source edge.
                    target, reason = self.sources.select(binding["binding"]["path"])
                    child_id = binding["generated_node"]
                    if target is None:
                        self.boundaries.append({"reason": reason, "parent": idx, "node": nid,
                                                "target": binding["binding"]["path"], "output": outport})
                    else:
                        enter(target, "root", "In1", (*address, child_id), scene, nid, "ArchiveXL:" + outport)

    def phase_child(self, enter, idx, physical, rid, graph, params, nid, inputs, address, scene):
        resource = params.get("phaseResource", {})
        target = ref_value(resource)
        if target in {"0", "", "none"}:
            child_rid, child_graph, reason = rid, f"{graph}/{nid}", "INLINE_PHASE_UNDECODED"
            if not self.sources.has_graph(child_rid, child_graph):
                child_rid = None
        elif resource.get("Flags") == "Embedded":
            match = next(((host, sub) for host in physical if (sub := self.sources.embedded(host, target))), None)
            child_rid, child_graph = match or (None, "root")
            reason = "EMBEDDED_PHASE_UNBOUND"
        else:
            child_rid, reason = self.sources.select(target)
            child_graph = "root"
        if child_rid is None:
            self.boundaries.append({"reason": reason, "parent": idx, "node": nid, "target": target})
            return
        for socket in sorted(inputs):
            enter(child_rid, child_graph, socket, (*address, nid), scene, nid, "phase")

    def scene_child(self, enter, idx, nid, target, inputs, address, scene):
        if target in {"0", "", "none"}:
            return
        child, reason = self.sources.select(target)
        if child is None:
            self.boundaries.append({"reason": reason, "parent": idx, "node": nid, "target": target})
            return
        for socket in sorted(inputs):
            enter(child, "scene", socket, address, (*scene, (idx, nid, socket)), nid, "scene")


def ancestry(scopes, index):
    while index is not None:
        row = scopes[index]
        yield row
        index = row["parent"]


def category(scopes, index):
    rows = tuple(ancestry(scopes, index))
    if any(row["depot"].lower().endswith(CUTOFFS) for row in rows):
        return "TOWER_CUTOFF"
    if any((row["incoming"] or {}).get("kind", "").startswith("ArchiveXL:") for row in rows):
        return "INSTALLED_XL"
    return "NATIVE"


def stage_links(trace, prior):
    by_digest = {(r["depot"], r["sha256"]): rid for rid, r in trace.sources.rows.items()}
    equivalent = defaultdict(set)
    for key in trace.sources.known_equivalent:
        for rid in trace.sources.by_key[key]:
            equivalent[rid].update(trace.sources.by_key[key])
    output = []
    for q in prior:
        stages = []
        for s in q["stages"]:
            matches = []
            for site in s["current_source_sites"]:
                rid = by_digest.get((site["depot"], site["sha256"]))
                if rid is None:
                    continue
                scopes = set()
                for alias in equivalent.get(rid, {rid}):
                    scopes.update(trace.by_location.get((alias, site["graph"], site["node"]), ()))
                for idx in sorted(scopes):
                    matches.append({"scope": idx, "node": site["node"], "operation": site["operation"],
                                    "route": category(trace.scopes, idx)})
            matches = sorted({tuple(row.items()) for row in matches}, key=lambda row: tuple(value for _, value in row))
            stages.append({"path": s["path"], "sites": [dict(m) for m in matches]})
        output.append({"id": q["id"], "stages": stages})
    return output


def collect_support(trace, used):
    included = {row["index"] for idx in used for row in ancestry(trace.scopes, idx)}
    output = {}
    for idx in sorted(included):
        scope = trace.scopes[idx]
        src = trace.sources
        root = src.support(scope["rid"], scope["graph"])
        entered_by = scope["incoming"]
        parent_idx = scope["parent"]
        instance = []
        callers = []
        if entered_by is not None and parent_idx is not None:
            parent = trace.scopes[parent_idx]
            node = src.graph(parent["rid"], parent["graph"])[1][entered_by["node"]]
            params = node["parameters"].get("questNode") or node["parameters"]
            instance = node_refs(params.get("phaseInstancePrefabs", []))
            callers = node_refs(params)
        output[idx] = {"source": scope, "root_prefab_node_refs": node_refs(root.get("phasePrefabs", [])),
                       "calling_instance_prefab_node_refs": instance, "calling_node_refs": callers,
                       "scene_has_actor_bindings": scope["kind"] == "scene" and bool(root.get("actors", []))}
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=int, default=1)
    parser.add_argument("--sources", type=int, default=2)
    parser.add_argument("--out", type=int, required=True)
    args = parser.parse_args()
    out = HERE / f"analysis_{args.out:02d}"
    require(not out.exists(), "Fresh owner-map output required")
    capture_path = HERE / f"capture_{args.capture:02d}/providers.json"
    source_path = HERE / f"analysis_{args.sources:02d}/source_review.json"
    capture, review = read(capture_path), read(source_path)
    require(review["provider_capture_sha256"] == sha(capture_path), "Wrong review for capture")
    plan, seen = verify_providers(capture)
    prior = read(PRIOR / "current_stage_index_01.json")
    with db_readonly(REG / "registry_02/registry.sqlite3") as db:
        sources = Sources(db, plan, seen, review)
        hooks, bindings, collisions, missing = registrations(sources, capture["phase_bindings"])
        trace = Trace(sources, hooks)
        trace.run()
        stage_rows = stage_links(trace, prior)
        used = {site["scope"] for row in stage_rows for stage in row["stages"] for site in stage["sites"]}
        supports = collect_support(trace, used)
    route_counts = Counter()
    quest_counts = Counter()
    for q in stage_rows:
        routes = set()
        for stage in q["stages"]:
            present = {site["route"] for site in stage["sites"]}
            route_counts.update(present or {"NO_REACHED_SITE"})
            routes.update(present)
        quest_counts.update(routes or {"NO_REACHED_SITE"})
    summary = {"quests": len(stage_rows), "scopes": len(trace.scopes), "selected_support_scopes": len(supports),
               "stage_route_counts": dict(route_counts), "quest_route_counts": dict(quest_counts),
               "boundary_counts": dict(Counter(row["reason"] for row in trace.boundaries)),
               "xl_generated_checked": len(bindings), "xl_generated_collisions": len(collisions),
               "xl_unbound": len(missing)}
    out.mkdir()
    write(out / "owner_map.json", {
        "summary": summary, "source_review_sha256": sha(source_path),
        "limits": ["Caller inputs and output-to-input socket topology are evaluated structurally.",
                   "Condition truth, returning call outputs and live ownership require separate evidence.",
                   "Embedded phases resolve in their containing resource. Scene callers do not supply native phase addresses."],
        "scopes": trace.scopes, "selected_scope_support": supports, "quests": stage_rows,
        "boundaries": trace.boundaries,
        "xl_bindings": bindings, "xl_id_collisions": collisions, "xl_unbound": missing,
    })
    print(summary)


if __name__ == "__main__":
    main()
