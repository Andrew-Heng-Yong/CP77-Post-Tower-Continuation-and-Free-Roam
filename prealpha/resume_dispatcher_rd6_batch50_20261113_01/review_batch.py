"""Produce an offline Step 5 review from pinned graph and history inputs."""

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from contextlib import closing
from functools import lru_cache
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTRY = HERE.parent / "quest_resume_registry_20261112_01"
RD5 = HERE.parent / "resume_dispatcher_rd5_rite_20261113_02"
sys.path.insert(0, str(HERE.parent / "resume_dispatcher_rd5_gigs_20261113_01"))
from capture import plain, read, sha, write


SOURCES = {
    "registry": ("registry_02/registry.sqlite3", "BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9"),
    "routes": ("routes_02/routes.sqlite3", "8C1E1E0F00034E0EB253D1AF6C5F2A8E0A8AF4C539EAB2DCD8B7B527AEE0C471"),
    "contexts": ("contexts_01/contexts.sqlite3", "4E7F581B2F8AFA7AF25708602EF93AA1C0E4BC8B16FDE43A333E798792A661B7"),
}
SNAPSHOTS = {
    "pre": ("snapshot_hs1_20261112T193921Z_151_2.json", "C1CFCBB5FF3BFB13D718C4FF0735D5A0E22A6C84C434E791F4F89C6C17BD26BE"),
    "post": ("snapshot_hs1_20261112T171055Z_161_1.json", "849751BD2A07EFA27D1BE09D5EB38403F59B7D7F07BDB1948CAF8C38A1BFEF6D"),
    "extended": ("snapshot_hs3_20261112T193931Z_1_3.json", "C27598B50A97F3B7D3DD4905CEF1EB8C0F8FB67DF2865933E022B58D5D13D8F0"),
}
MANIFEST = ("deployment_01/installed_manifest_01.json", "C298EA55F984CB0CAC95388848705C9B15C7CCD74958EE901C794BDFDEE28C36")
READBACK = ("archive_01/readback.json", "BDCA1C2415301C1BA2068758AE0720201F10E9D71509EA5D9041AF64EB25CDCC")
PHASE = "gameJournalQuestPhase"
OBJECTIVE = "gameJournalQuestObjective"
INTERESTING = {"PREDICATE", "LOGICAL_JOIN", "WAIT", "REWARD_OR_INVENTORY", "CLEANUP_CONTROL", "WORLD_SUPPORT"}


def pinned(parent, pin):
    path = parent / pin[0]
    plain(path)
    assert sha(path) == pin[1], path
    return path


def readonly(name):
    path = pinned(REGISTRY, SOURCES[name])
    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return closing(db)


def load_baseline():
    manifest = read(pinned(RD5, MANIFEST))
    packed = read(pinned(RD5, READBACK))
    assert manifest["core_epoch"] == "RD5_RITE_OF_PASSAGE_RESUME"
    assert len(manifest["core_files"]) == 51 and len(manifest["required_files"]) == 26
    assert packed["archive_sha256"] == manifest["archive_sha256"]
    game = Path(manifest["game_root"])
    for item in manifest["core_files"] + manifest["required_files"]:
        pinned(game, (item["path"], item["sha256"]))
    members = {item["depot"]: item["sha256"] for item in packed["members"]}
    assert len(members) == manifest["archive_payloads"] == 1745
    xl, = [row for row in manifest["core_files"] if row["path"].endswith(".archive.xl")]
    return game, members, xl


def keyed_rows(rows, key):
    indexed = {row["definition"][key]: row for row in rows}
    assert len(indexed) == len(rows)
    return indexed


class History:
    def __init__(self, game):
        folder = game / "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1"
        pre, post, extended = (read(pinned(folder, SNAPSHOTS[key])) for key in ("pre", "post", "extended"))
        assert (pre["origin"], pre["revision"]) == ("pre_ending", 151)
        assert (post["origin"], post["revision"]) == ("post_ending_fallback", 161)
        assert (extended["origin"], extended["route"], extended["ticket"], extended["revision"]) == (
            "pre_native_cleanup", 1, 1, 1)
        assert extended["catalogue"] == "C518094308849C32611EB2C471A047C548BEC668C30F873B0CCFED00DD5B08DD"
        assert len(pre["rows"]) == len(post["rows"]) == 158 and len(extended["rows"]) == 24753
        self.pre = keyed_rows(pre["rows"], "id")
        self.post = keyed_rows(post["rows"], "id")
        self.extended = keyed_rows([row for row in extended["rows"] if row["definition"]["kind"] == "journal"
                                    and row["definition"]["class"] in {"gameJournalQuest", PHASE, OBJECTIVE}], "path")

    def capture(self, quest, stages):
        qid, root = quest["id"], quest["journal_root"]
        before, after = self.pre.get(qid), self.post.get(qid)
        observations = []
        facts = {}
        if before and after:
            definition = before["definition"]
            assert definition == after["definition"]
            if before["stable"] and after["stable"]:
                entries = definition["journals"]
                values = zip(entries, before["states"], after["states"], before["counters"],
                             after["counters"], before["optional"], after["optional"], strict=True)
                observations = [{"path": path, "class": kind, "pre": a, "post": b,
                                 "counters": [count_a, count_b], "optional": [opt_a, opt_b]}
                                for (path, kind), a, b, count_a, count_b, opt_a, opt_b in values]
                facts = dict(zip(definition["fact_names"], zip(before["facts"], after["facts"], strict=True), strict=True))
        observed = {row["path"]: row for row in observations}
        current = observed.get(root)
        interrupted = bool(current and (current["pre"], current["post"]) == (2, 4))
        authored_objectives = {row["path"] for row in stages if row["class"] == OBJECTIVE}
        active = sorted(path for path in authored_objectives if observed.get(path, {}).get("pre") == 2)
        extended = sorted(path for path in authored_objectives if path in self.extended
                          and self.extended[path]["stable"] and self.extended[path]["state"] == 2)
        witness = {
            "root_pre_post": [current["pre"], current["post"]] if current else None,
            "interrupted_hs1_root": interrupted,
            "hs1_active_objectives": active,
            "hs3_active_objectives": extended,
        }
        if interrupted:
            witness["hs1_journals"] = observations
            witness["hs1_fact_pre_post"] = facts
            witness["hs3_root_and_objectives"] = [
                {"path": path, **{k: self.extended[path][k] for k in ("state", "counter", "optional", "tracked")}}
                for path in [root, *extended] if path in self.extended and self.extended[path]["stable"]
            ]
        return witness


class Sources:
    def __init__(self, db, routes, contexts, members):
        self.db, self.routes, self.contexts, self.members = db, routes, contexts, members
        self.resources = {row["rid"]: dict(row) for row in db.execute(
            "SELECT rid,depot,key,role,archive,sha256,status FROM resources")}
        self.by_depot = defaultdict(list)
        for resource in self.resources.values():
            self.by_depot[resource["depot"]].append(resource)

    @lru_cache(maxsize=None)
    def route(self, ordinal):
        row = self.routes.execute("SELECT * FROM roots WHERE ordinal=?", (ordinal,)).fetchone()
        provider, = [res for res in self.by_depot[row["depot"]] if res["role"] == "PTFR"]
        nodes = {tuple(r) for r in self.routes.execute("SELECT rid,graph,node FROM reached WHERE root=?", (ordinal,))}
        boundaries = [json.loads(r[0]) for r in self.routes.execute(
            "SELECT record_json FROM boundaries WHERE root=? ORDER BY record_json", (ordinal,))]
        return {
            "ordinal": ordinal, "provider": provider["rid"], "binding": json.loads(row["binding_json"]),
            "boundaries": boundaries, "resources": sorted({provider["rid"], *(key[0] for key in nodes)}),
        }, nodes

    def quest(self, qid, history, group):
        quest = dict(self.db.execute("SELECT id,title,selection,category,journal_root FROM quests WHERE id=?", (qid,)).fetchone())
        assert quest["selection"] == "INCLUDE", qid
        assert group == "regressions" or (quest["category"] == "gigs") == group.endswith("_gigs"), qid
        assert not group.endswith("_gigs") or qid.startswith("sts_ep1_") == (group == "ep1_gigs"), qid
        route_rows = list(self.routes.execute(
            "SELECT root,source_sites,stage_sites FROM quest_routes WHERE quest_id=? ORDER BY stage_sites DESC,root", (qid,)))
        assert route_rows, qid
        route_refs = []
        indexed = defaultdict(list)
        for ordinal, source_sites, stage_sites in route_rows:
            route, nodes = self.route(ordinal)
            route_refs.append({"root": ordinal, "journal_sites": source_sites, "stage_sites": stage_sites})
            for key in nodes:
                indexed[key].append(route["ordinal"])

        stages = [json.loads(row[0]) for row in self.contexts.execute(
            "SELECT record_json FROM stages WHERE quest_id=? AND class IN (?,?) ORDER BY path", (qid, PHASE, OBJECTIVE))]
        assert stages, qid
        observations = history.capture(quest, stages)
        stage_rows = []
        for stage in stages:
            writers = []
            for address in stage["source_sites"]:
                rid, graph, node = address
                raw = self.contexts.execute("SELECT record_json FROM sites WHERE rid=? AND graph=? AND node=?", address)
                site = json.loads(raw.fetchone()[0])
                if site["operation"] != "WRITE":
                    continue
                roles = defaultdict(set)
                for kind, relations in site["feature_relations"].items():
                    if kind in INTERESTING:
                        for relation in relations:
                            where = relation["relation"]
                            if where != "UNRELATED_LOCAL_BRANCH":
                                roles[where].add(kind)
                writers.append({"location": address, "source_role": self.resources[rid]["role"],
                                "state_sockets": site["journal_write_inputs"], "connected_roots": sorted(indexed[tuple(address)]),
                                "incoming": site["incoming_controls"], "local_input_nodes": site["structurally_reaching_local_inputs"],
                                "earlier_journals": site["nearest_predecessor_journal_sites"],
                                "local_risks": {where: sorted(kinds) for where, kinds in sorted(roles.items())}})
            stage_rows.append({"path": stage["path"], "class": stage["class"],
                               "has_journal_definition": bool(stage["definition_sources"]), "writers": writers})
        return {**quest, "group": group, "runtime_admitted_by_batch": False, "history": observations,
                "route_refs": route_refs, "stages": stage_rows}

    def provider_watch(self, quests):
        ordinals = {route["root"] for quest in quests for route in quest["route_refs"]}
        resources = {rid for ordinal in ordinals for rid in self.route(ordinal)[0]["resources"]}
        # Only ask for disconnected native writer providers on actual observed stage paths.
        for quest in quests:
            observed = set(quest["history"]["hs1_active_objectives"] + quest["history"]["hs3_active_objectives"])
            resources.update(writer["location"][0] for stage in quest["stages"] if stage["path"] in observed
                             for writer in stage["writers"])
        watched = [self.resources[rid] for rid in sorted(resources)]
        for row in watched:
            if row["role"] == "PTFR":
                row["qp2_bytes_match_rd5_archive"] = self.members.get(row["depot"]) == row["sha256"]
        return watched

    def footprints(self, quests, routes):
        route_ids = {row["ordinal"] for row in routes}
        reaching = defaultdict(set)
        for ordinal in sorted(route_ids):
            for key in self.route(ordinal)[1]:
                reaching[key].add(ordinal)
        writes, facts, rewards = (defaultdict(set) for _ in range(3))
        for rid, graph, node, path in self.db.execute("SELECT rid,graph,node,path FROM journals WHERE operation='WRITE'"):
            for ordinal in reaching.get((rid, graph, node), ()):
                writes[ordinal].add(path)
        for rid, graph, node, kind, parameters in self.db.execute(
                "SELECT rid,graph,node,type,parameters_json FROM effects WHERE type IN ('questSetVar_NodeType','questGiveReward_NodeType')"):
            ordinals = reaching.get((rid, graph, node))
            if not ordinals:
                continue
            value = json.loads(parameters)
            for ordinal in ordinals:
                if kind == "questSetVar_NodeType" and value.get("factName"):
                    facts[ordinal].add(value["factName"])
                if kind == "questGiveReward_NodeType":
                    rewards[ordinal].update(str(ref["$value"]) for ref in value.get("rewards", []) if "$value" in ref)
        return [{"root": ordinal, "journal_writes": sorted(writes[ordinal]), "fact_writes": sorted(facts[ordinal]),
                 "reward_targets": sorted(rewards[ordinal])} for ordinal in sorted(route_ids)]


def prepare(out):
    assert out.parent == HERE and out.name.startswith("evidence_") and not out.exists()
    game, members, xl = load_baseline()
    history = History(game)
    cohort = read(HERE / "cohort.json")
    selected = [qid for group, ids in cohort.items() if group != "regressions" for qid in ids]
    assert len(selected) == len(set(selected)) == 50 and not set(selected) & set(cohort["regressions"])
    with readonly("registry") as db, readonly("routes") as routes, readonly("contexts") as contexts:
        src = Sources(db, routes, contexts, members)
        quests = [src.quest(qid, history, group) for group, ids in cohort.items() for qid in ids]
        watched = src.provider_watch(quests)
        route_rows = [src.route(ordinal)[0] for ordinal in sorted({r["root"] for q in quests for r in q["route_refs"]})]
        effects = src.footprints(quests, route_rows)
    out.mkdir()
    source_file = out / "source_packets.json"
    write(source_file, {"quests": quests, "routes": route_rows, "route_footprints": effects})
    write(out / "provider_watch.json", {"game": str(game), "xl": xl, "resources": watched,
                                       "source_packets_sha256": sha(source_file)})
    print(f"Prepared {len(selected)} quests and {len(cohort['regressions'])} regression rows, {len(route_rows)} route roots, "
          f"{len(watched)} current provider checks.")


def evidence_fingerprint(quest):
    """Exact offline witness, with no default state or inferred facts."""
    history = quest["history"]
    if not history["interrupted_hs1_root"] or not history["hs1_active_objectives"]:
        return {}
    journals = {}
    for row in history["hs1_journals"]:
        if row["class"] not in (PHASE, OBJECTIVE) and row["path"] != quest["journal_root"]:
            continue
        if row["pre"] not in (1, 2, 3, 4) or row["post"] not in (1, 2, 3, 4):
            return {}
        expected = 4 if row["pre"] == 2 else row["pre"]
        if row["post"] != expected:
            return {}
        if row["class"] == OBJECTIVE:
            a, b = row["counters"]
            if a < 0 or a != b or row["optional"][0] != row["optional"][1]:
                return {}
            journals[row["path"], "counter"] = a
        journals[row["path"], "history"] = row["pre"]
        journals[row["path"], "post"] = row["post"]
    for name, (a, b) in history["hs1_fact_pre_post"].items():
        if a != b:
            return {}
        journals[name, "fact"] = a
    return journals


def matches(expected, sample):
    return bool(expected) and all(key in sample and sample[key] == value for key, value in expected.items())


def reject_alternatives(expected):
    if not expected:
        assert not matches(expected, {})
        return 1
    assert matches(expected, expected.copy())
    checked = 0
    for key, value in expected.items():
        missing = expected.copy()
        missing.pop(key)
        assert not matches(expected, missing), key
        alternatives = {-1, 1, 2, 3, 4} if key[1] in {"history", "post"} else {value + 1}
        for alternative in alternatives - {value}:
            assert not matches(expected, expected | {key: alternative}), key
            checked += 1
        checked += 1
    return checked


def kirk_fingerprint(quest):
    # HS3 is a separately observed pre-cleanup state. The read-only save
    # projections independently show the same exact paths before and after Tower.
    folder = HERE.parent / "history_capture_hs3_20261112_01/fixtures_saves_01"
    pins = [
        ("ManualSave-26.json", "B618E63DAE7C058AE71689CEF695801E911FC8D431847091D5F55EB04BBFA74B"),
        ("ManualSave-27.json", "92290F8515EC5B3BC69EAE0F90F77881EE87FBA67D268D0FB4049E50E21B507A"),
    ]
    root = quest["journal_root"]
    phase = root + "/mq017_streetkid"
    objective = phase + "/01_meet_kirk"
    assert quest["history"]["hs3_active_objectives"] == [objective]
    hs3 = {row["path"]: row for row in quest["history"]["hs3_root_and_objectives"]}
    assert hs3[root]["state"] == hs3[objective]["state"] == 2
    assert hs3[objective]["counter"] == hs3[objective]["optional"] == 0
    result = {(objective, "hs3_counter"): 0, (objective, "hs3_optional"): 0}
    for (kind, state), pin in zip((("history", 2), ("post", 4)), pins, strict=True):
        projection = read(pinned(folder, pin))
        states = {path: row["uint32_at_4"] for row in projection["journal_matches"]
                  if len(row["paths"]) == 1 for path in row["paths"]}
        for path in (root, phase, objective):
            assert states[path] == state, (path, kind, states[path])
            result[path, kind] = state
    return result


def assess_providers(watched, actual):
    by_key = defaultdict(list)
    for provider in actual:
        by_key[provider["key"]].append(provider)
    reviewed = {}
    for row in watched:
        providers = sorted(by_key[row["key"]], key=lambda p: p["archive"])
        matched = [p for p in providers if p["archive"].casefold() == row["archive"].casefold()
                   and p["sha256"] == row["sha256"]]
        if not matched:
            status = "SOURCE_PROVIDER_DRIFT"
        elif len(providers) != 1:
            status = "MULTIPLE_CURRENT_PROVIDERS"
        elif row.get("qp2_bytes_match_rd5_archive", True) is False:
            status = "SOURCE_READBACK_DRIFT"
        else:
            status = "EXACT_CURRENT_PROVIDER"
        reviewed[row["rid"]] = {"rid": row["rid"], "depot": row["depot"], "status": status, "providers": providers}
    return reviewed


def overlap_rows(quests, footprints, qualified):
    aggregated = defaultdict(lambda: defaultdict(set))
    for quest in quests:
        if quest["group"] == "regressions":
            continue
        for route in quest["route_refs"]:
            root = route["root"]
            if root not in qualified:
                continue
            for field in ("journal_writes", "fact_writes", "reward_targets"):
                aggregated[quest["id"]][field].update(footprints[root][field])
    overlaps = []
    for left, right in combinations(sorted(aggregated), 2):
        shared = {field: sorted(keys & aggregated[right][field]) for field, keys in aggregated[left].items()}
        if any(shared.values()):
            overlaps.append({"quests": [left, right], **shared})
    return overlaps


def finish(out):
    assert out.parent == HERE and out.name.startswith("evidence_") and out.is_dir()
    watch_file = out / "provider_watch.json"
    watch, actual = read(watch_file), read(out / "installed_readback.json")
    assert actual["input_sha256"] == sha(watch_file)
    source = read(pinned(out, ("source_packets.json", watch["source_packets_sha256"])))
    providers = assess_providers(watch["resources"], actual["providers"])
    current_routes = set()
    for route in source["routes"]:
        binding = route["binding"]
        current = [row for row in actual["bindings"] if row["path"] == binding["path"]]
        mismatches = [rid for rid in route["resources"] if providers[rid]["status"] != "EXACT_CURRENT_PROVIDER"]
        route["registration_exact"] = current == [binding]
        route["provider_exceptions"] = mismatches
        if route["registration_exact"] and not mismatches:
            current_routes.add(route["ordinal"])
    summaries, positive_fixtures = [], {}
    for quest in source["quests"]:
        observed = quest["history"]
        evidence_kind = "PINNED_HS1_WITNESS"
        fingerprint = evidence_fingerprint(quest)
        if quest["id"] == "mq017_streetkid":
            evidence_kind = "HS3_AND_INDEPENDENT_SAVE_PROJECTIONS"
            fingerprint = kirk_fingerprint(quest)
        if not fingerprint:
            evidence_kind = "NO_EXACT_POSITIVE_FIXTURE"
        else:
            positive_fixtures[quest["id"]] = fingerprint
        quest["offline_fixture"] = {
            "source": evidence_kind,
            "fields": [{"key": key, "field": field, "value": value} for (key, field), value in sorted(fingerprint.items())],
        }
        for stage in quest["stages"]:
            stage["current_activation_writer_locations"] = [
                writer["location"] for writer in stage["writers"] if "Active" in writer["state_sockets"]
                and current_routes.intersection(writer["connected_roots"])]
        summaries.append({
            "id": quest["id"], "title": quest["title"], "group": quest["group"],
            "fixture": evidence_kind, "negative_fixture_checks": reject_alternatives(fingerprint),
            "authored_stage_paths": len(quest["stages"]),
            "stage_paths_with_current_activation_writer": sum(bool(s["current_activation_writer_locations"]) for s in quest["stages"]),
            "observed_objectives": observed["hs1_active_objectives"] or observed["hs3_active_objectives"],
            "qualified_source_roots": [r["root"] for r in quest["route_refs"] if r["root"] in current_routes],
            "runtime_admitted_by_batch": quest["runtime_admitted_by_batch"],
        })
    footprints = {row["root"]: row for row in source["route_footprints"]}
    overlaps = overlap_rows(source["quests"], footprints, current_routes)
    batch = [row for row in summaries if row["group"] != "regressions"]
    positive_ids = {row["id"] for row in batch if row["id"] in positive_fixtures}
    mixed = {}
    for qid in sorted(positive_ids):
        for key, value in positive_fixtures[qid].items():
            assert key not in mixed or mixed[key] == value, (qid, key)
            mixed[key] = value
    mixed_checks = 0
    for qid in sorted(positive_ids):
        fixture = positive_fixtures[qid]
        assert matches(fixture, mixed), qid
        root = next(row["journal_root"] for row in source["quests"] if row["id"] == qid)
        modified = mixed | {(root, "post"): 3}
        accepted = {candidate for candidate in positive_ids if matches(positive_fixtures[candidate], modified)}
        assert accepted == positive_ids - {qid}, (qid, accepted)
        mixed_checks += 1
    report = {
        "status": "OFFLINE_STAGE_REVIEW",
        "counts": {
            "quests": len(batch), "regression_rows": len(summaries) - len(batch),
            "authored_stage_paths": sum(row["authored_stage_paths"] for row in batch),
            "stage_paths_with_current_activation_writer": sum(row["stage_paths_with_current_activation_writer"] for row in batch),
            "exact_positive_fixtures": sum(row["fixture"] != "NO_EXACT_POSITIVE_FIXTURE" for row in batch),
            "negative_fixture_checks": sum(row["negative_fixture_checks"] for row in batch),
            "combined_fixture_isolation_checks": mixed_checks,
            "archives": len(actual["archives"]), "source_resources_watched": len(providers),
            "provider_status": dict(Counter(row["status"] for row in providers.values())),
            "route_roots": len(source["routes"]), "exact_route_roots": len(current_routes),
            "route_roots_with_graph_boundaries": sum(bool(r["boundaries"]) for r in source["routes"]),
            "overlapping_pairs": len(overlaps),
            "runtime_admitted_by_batch": 0,
        },
        "quests": summaries,
        "limits": [
            "Current source roots require an exact XL binding and the expected bytes of all watched reached resources.",
            "Graph reachability allows every possible branch. Shared writes need timing, actor, reward and ownership review.",
            "An offline fingerprint checks exact historical evidence. It is not a generalized runtime guard.",
            "HS1 pre and post inputs are pinned historical observations. No same-run claim is made for HS3.",
        ],
    }
    assert len(batch) == 50
    write(out / "assessment.json", report)
    write(out / "review_packets.json", {
        "quests": source["quests"], "routes": source["routes"], "route_footprints": source["route_footprints"],
        "provider_review": list(providers.values()), "overlapping_pairs": overlaps,
    })
    write(out / "manifest.json", {
        "sources": SOURCES, "snapshots": SNAPSHOTS, "installed_manifest": MANIFEST, "archive_readback": READBACK,
        "tool": sha(__file__), "provider_reader": sha(HERE / "verify_installed.ps1"), "cohort": sha(HERE / "cohort.json"),
        "files": {path.name: sha(path) for path in sorted(out.glob("*.json"))},
    })
    print(json.dumps(report["counts"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=("prepare", "finish"))
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    {"prepare": prepare, "finish": finish}[args.step](args.evidence.resolve())
