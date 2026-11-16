"""Read the two preserved Reed cutoffs and bind the travel fixture to source."""

import json
import sqlite3
from pathlib import Path
from candidate_common import digest, load, pin, require, write_json

PREALPHA = Path(__file__).resolve().parent.parent

MOVING_HEAT = [1, 0, 10, 4, 2, 30, 6, 4, 65, 17]
RITE = [0, 2, 82, 3, 19, 2, 7, 4, 10]
RITE_BUGFIX = [0, 2, 82, 4, 11, 1, 35, 9]
SCOPES = [
    (13718, "root"), (13133, "root"), (13133, "root/10"), (13229, "root"),
    (13626, "root"), (13626, "root/30"), (13626, "root/30/6"),
    (12821, "root"), (12994, "root"), (13765, "root"),
]
REGISTRATIONS = [(0, 0), (2, 4), (3, 2), (6, 4), (7, 65), (8, 17),
                 (7, 147), (7, 148), (7, 164), (8, 2), (9, 1)]
CAPTURES = {
    "checkpoint_execution_2185a8b5a6758511822fdab7bf4f517e.json":
        "15B5BFAE5F435AE4471490B867D156A9EC8D845EFDD40B8C549534B94B4A0295",
    "checkpoint_execution_feff5775c34c732362f886201f4b2fb7.json":
        "D519744FC3D88E28F60B0BF3E98673D2BC21283EA3A59CB72A24679036822C0D",
}


def project(out, baseline):
    sources = PREALPHA / "quest_resume_contracts_rc2_20261114_01/capture_02/providers.json"
    inventory = load(sources, "28886286289AF4C667CD1B0D64D5DDA1B5973D83B17091AB40DDE76093E97177")
    providers = {(row["archive"], row["key"]): row["sha256"] for row in inventory["providers"]}
    save_projections = PREALPHA / "quest_resume_contracts_rc2_20261114_01/analysis_06/saved_witness.json"
    witness = load(save_projections, "0ABA31C20C4D9D65F7AEC6D2031AC3FA2B63C6FC53CB50A2D6F8EA02F4DA5F21")
    stock_rite = next(c for c in witness["controls"] if c["id"] == "sts_wat_nid_05" and c["phase_address"] == RITE)
    require(stock_rite["expected_count"] == 0, "Rite save control changed")
    database = (PREALPHA / "quest_resume_registry_20261112_01/registry_02/registry.sqlite3").resolve()
    game = Path(baseline["game_root"])

    def binding_type(node):
        if node["$type"] == "questPhaseNodeDefinition":
            return node["$type"]
        condition = node["condition"]
        subtype = condition.get("type")
        return (subtype if isinstance(subtype, dict) else condition)["$type"]

    def key(text):
        result = 0xCBF29CE484222325
        for byte in text.encode("ascii"):
            result = ((result ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
        return result

    provider_rows = {}
    source_nodes = []
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as db:
        for rid in {*(rid for rid, _ in SCOPES), 6756, 11841, 2840, 10163}:
            depot, resource, archive, sha, export, export_sha = db.execute(
                "SELECT depot,key,archive,sha256,export_path,export_sha256 FROM resources WHERE rid=?", (rid,)
            ).fetchone()
            archive_path = Path(archive).relative_to(game).as_posix()
            require(providers.get((archive_path, resource)) == sha, f"Wrong stock provider for {depot}")
            pin(Path(export), export_sha)
            provider_rows[rid] = dict(depot=depot, key=int(resource), archive=archive_path,
                                      payload_sha256=sha, export_sha256=export_sha)
        for phase, node in REGISTRATIONS:
            rid, graph = SCOPES[phase]
            definition, = db.execute("SELECT parameters_json FROM nodes WHERE rid=? AND graph=? AND id=?",
                                     (rid, graph, node)).fetchone()
            node_type = binding_type(json.loads(definition))
            source_nodes.append(dict(phase=phase, node=node, type=node_type, type_key=key(node_type)))

    result = None
    observed = []
    capture_folder = game / "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1"
    for filename, expected in CAPTURES.items():
        source = capture_folder / filename
        data = load(source, expected)
        require(data["route"] == 1 and data["roots"] == ["ca034981517a576b", "c4c842994ba818e1"],
                f"Unexpected Reed route or roots: {filename}")
        phases = [next(p for p in data["phases"] if p[3] == MOVING_HEAT[:n])
                  for n in range(1, len(MOVING_HEAT) + 1)]
        require(not [p for p in data["phases"] if p[3][:8] == MOVING_HEAT[:8] and p not in phases],
                "Unexpected Moving Heat child")
        for phase, (rid, graph) in zip(phases, SCOPES, strict=True):
            require(int(phase[1], 16) == (0 if graph != "root" else provider_rows[rid]["key"]),
                    f"Moving Heat phase differs from stock provider at {phase[3]}")
        handlers = []
        for node in source_nodes:
            owner = phases[node["phase"]][0]
            expected_handler, = [h for h in data["handlers"] if h[2:4] == [owner, node["node"]]]
            require(int(expected_handler[1], 16) == node["type_key"] and expected_handler[4] == 1,
                    f"Wrong type or binding at {node}")
            handlers.append(expected_handler)
        body_ids = {row[0] for row in phases[7:]}
        require(sum(h[2] in body_ids for h in data["handlers"]) == 7 and
                not any(int(i[0], 16) >> 32 in body_ids for i in data["node_instances"]),
                "Moving Heat pending state has extra registrations or native instance data")
        slots = {h[0] for h in handlers}
        require(not slots.intersection(data["notifications"]) and not any(t[0] in slots for t in data["timings"]),
                "Moving Heat has pending notification or timer work")
        require(not {int(d, 16) for d in data["resource_requests"]}.intersection(int(p[1], 16) for p in phases),
                "Moving Heat resources were queued at cutoff")

        travel_depots = {provider_rows[rid]["key"] for rid in (6756, 11841, 2840)}
        require(not any(p[3][:len(RITE)] == RITE or int(p[1], 16) in travel_depots for p in data["phases"]),
                "Original Rite travel owner present in the capture")
        rite_phases = [
            p for p in data["phases"] if (p[3][:len(RITE_BUGFIX)] == RITE_BUGFIX
                                         or p[3] == RITE[:len(p[3])])
        ]
        bugfix_hashes = {p[0] for p in rite_phases if p[3][:len(RITE_BUGFIX)] == RITE_BUGFIX}
        rite_handlers = [h for h in data["handlers"] if h[2] in bugfix_hashes]
        require(len(rite_handlers) == 2, "Rite bug-fix control changed")
        evidence = phases, handlers, rite_phases, rite_handlers
        require(result is None or result == evidence, "Independent Reed captures disagree")
        result = evidence
        observed.append(dict(file=str(source), sha256=expected, capture_id=data["id"]))

    phases, handlers, rite_phases, rite_handlers = result
    report = out / "travel_projection.json"
    write_json(report, dict(status="PROJECTION_PASS", cutoffs=observed, provider_inventory_sha256=digest(sources),
                            providers=provider_rows, native_nodes=source_nodes, moving_heat_phases=phases,
                            moving_heat_handlers=handlers, rite_travel_owner_observed=False,
                            rite_bugfix_handlers=rite_handlers, runtime_admission="DEFERRED"))

    def phase_row(row):
        hash_, depot, count, path = row
        words = ", ".join(str(v) for v in path)
        return f"    Phase{{{{{words}}}, {len(path)}, {hash_}U, 0x{depot}ULL, {count}U}},"

    def handler_row(row):
        slot, type_, hash_, node, _ = row
        return f"    Handler{{{{0x{type_}ULL, {hash_}U, {node}U}}, {slot}U, Binding::Live}},"

    header = out / "TravelEvidence.hpp"
    lines = ["#pragma once", "namespace ptfr::resume::test", "{"]
    for name, rows, render in (("MovingHeatObservedPhases", phases, phase_row),
                               ("MovingHeatObservedHandlers", handlers, handler_row),
                               ("RiteObservedPhases", rite_phases, phase_row),
                               ("RiteObservedHandlers", rite_handlers, handler_row)):
        lines.extend([f"inline constexpr std::array {name}{{", *(render(row) for row in rows), "};"])
    lines.extend([
        "inline constexpr auto RiteTravelPath = std::to_array<std::uint16_t>({" +
        ", ".join(str(v) for v in RITE) + "});",
        f"inline constexpr auto RiteMainDepot = 0x{provider_rows[6756]['key']:016x}ULL;",
        "} // namespace ptfr::resume::test", "",
    ])
    header.write_text("\n".join(lines), encoding="ascii")
    return header, report
