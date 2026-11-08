"""Add the original post-Dumpster handoff to the staged QR17 wrapper."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
QR17 = HERE.parent / "quest_restoration_qr17"
sys.path.insert(0, str(QR17))
from prepare import (
    QR13, PRIVATE, SCRIPT, PENDING, TAG, COIN, DUMPSTER, SPRAY, NATIVE_FACTS, STAGE,
    EARNED, HELD, Edit, Resource, COND_SOCKETS, STANDARD, checked, journal_samples,
    read, reset, sha, unlink, value, write,
)

EARLY_FACTS = NATIVE_FACTS | {
    "mq037_post_girl_scene_on": 0,
    "mq037_01_05Sure": 0,
    "mq037_kill_token_block_loop": 0,
    "mq037_vandal_painted_brendan": 0,
}
PREDECESSOR_MANIFEST = "DC6634F48E9B03C3B22A7E082368AC723C7F4945369CC33EDA448278B10672E8"


def inputs():
    pack = read(checked(QR17 / "candidate_01/package_manifest.json", PREDECESSOR_MANIFEST))
    assert pack["status"] == "STAGED_QR17_READBACK_VERIFIED_NOT_INSTALLED"
    prior = read(QR17 / "serialized_01/manifest.json")
    assert prior["depot"] == PRIVATE and prior["sha256"] == pack["source_resources"][PRIVATE]
    checked(prior["raw"], prior["sha256"])
    wrapper = read(checked(prior["readback"], prior["readback_sha256"]))
    native, = (r for r in read(QR13 / "brendan_provider_validation_01/manifest.json")["resources"]
               if r["depot"].endswith("mq037_brendan.questphase"))
    checked(native["raw"], native["sha256"])
    original = read(checked(native["json"], native["json_sha256"]))
    leaves = {row["path"]: row["sha256"] for row in pack["files"]}
    script = checked(QR17 / "candidate_01/package" / SCRIPT, leaves[SCRIPT]).read_text(encoding="utf-8-sig")
    return wrapper, original, script


def early_journal(doc):
    later = journal_samples(doc)
    earlier = {}
    for path, (state, cls, _) in later.items():
        earlier[path] = ("Inactive" if path.startswith(SPRAY) else state, cls)
    earlier[SPRAY + "/mq037_brendan_hooligan"] = ("Inactive", "gameJournalQuestPhase")
    assert all(earlier[p][0] == "Succeeded" for p in EARNED if p.startswith(DUMPSTER))
    assert COIN in earlier
    return earlier


def script_change(script, journals):
    old = 'this.ReadBrendanHandoff(paths, sample.states, names, sample.facts)'
    assert script.count(old) == 1
    script = script.replace(old, '(' + old + ' ||\n        this.ReadBrendanAfterDumpster(paths, sample.states, names, sample.facts))')
    script = script.replace('sample.reason = "Earned Spray Paint complete. Starting the native Coin Operated Boy handoff from its six-hour wait.";',
                            'sample.reason = "Earned Brendan continuation matches a native handoff from its starting wait.";')
    terms = [f'BrendanFinalDataQR13.State(paths, states, "{p}") == {STAGE[s]}' for p, (s, _) in journals.items()]
    terms += [f'BrendanFinalDataQR13.Fact(names, facts, "{n}") == {v}' for n, v in EARLY_FACTS.items()]
    method = '  private func ReadBrendanAfterDumpster(paths: array<String>, states: array<Int32>, names: array<String>, facts: array<Int32>) -> Bool {\n'
    method += '    return ' + ' &&\n      '.join(terms) + ';\n  }\n'
    anchor = "  private func Same(a: SideJobSampleS23"
    assert script.count(anchor) == 1
    return script.replace(anchor, method + anchor)


def wrapper_change(doc, native_doc, journals):
    ed = Edit(doc)
    native = Edit(native_doc)
    root = ed.graph("root")
    old_root = ed.r.normalize()["graphs"]["root"]
    old = reset(ed, root, old_root)
    common = old_root["nodes"]["1100"]["reads"][:15]
    assert common == old_root["nodes"]["1120"]["reads"][:15]

    def gate(pending, held, permit):
        facts = {f["factName"]: f["value"] for f in common} | EARLY_FACTS | {
            TAG + "_Issued": 0, TAG + "_Entered": 0, TAG + "_Finished": 0, TAG + "_Fault": 0,
            PENDING: pending, HELD: held,
        }
        if permit:
            facts[TAG + "_Permit"] = 1
        return ed.logic("AND", [ed.fact(n, v) for n, v in facts.items()] +
                        [ed.journal(p, c, s) for p, (s, c) in journals.items()])

    def condition(i, payload):
        return ed.add(root, {"$type": "questConditionNodeDefinition", "id": i, "condition": payload}, COND_SOCKETS)

    def marker(i, name, val):
        payload = ed.h({"$type": "questSetVar_NodeType", "factName": name, "setExactValue": 1, "value": val})
        return ed.add(root, {"$type": "questFactsDBManagerNodeDefinition", "id": i, "type": payload}, STANDARD)

    def copy_node(i, source_id):
        source = native.node(native.graph("root/19"), source_id)
        payload = ed.clone(source, native.r, skip=("sockets",))
        payload["id"] = i
        sockets = [(value(s["name"]), s["type"]) for h in source["sockets"] if (s := native.r.d(h))]
        return ed.add(root, payload, sockets)

    for i in ("1002", "1004"):
        ed.r.d(old[i]["condition"])["conditions"].append(gate(0, 0, True))
    new = {
        1140: condition(1140, gate(0, 0, True)),
        1141: marker(1141, PENDING, 2),
        1142: condition(1142, ed.fact(PENDING, 2)),
        1143: copy_node(1143, 54),
        1144: copy_node(1144, 24),
        1145: copy_node(1145, 25),
        1146: condition(1146, gate(2, 1, False)),
        1147: marker(1147, TAG + "_Issued", 1),
        1148: copy_node(1148, 26),
        1149: marker(1149, TAG + "_Entered", 1),
        1150: marker(1150, PENDING, 0),
    }
    nodes = {int(k): n for k, n in old.items()} | new
    unlink(ed, nodes[1120], "False", nodes[1008], "In")
    unlink(ed, nodes[1122], "False", nodes[1101], "In")
    for a, s, b, t in (
        (1120, "False", 1140, "In"), (1140, "False", 1008, "In"),
        (1140, "True", 1141, "In"), (1141, "Out", 1110, "In1"),
        (1122, "False", 1142, "In"), (1142, "False", 1101, "In"),
        (1142, "True", 1143, "In"), (1142, "True", 1144, "In"),
        (1144, "Out", 1145, "In"), (1145, "Out", 1146, "In"),
        (1146, "False", 1131, "In"), (1146, "True", 1147, "In"),
        (1147, "Out", 1148, "In"), (1148, "Out", 1149, "In"),
        (1149, "Out", 1150, "In"), (1150, "Out", 34, "Girlfriend"),
    ):
        ed.link(nodes[a], s, nodes[b], t)
    return ed.ordered()


def main():
    out = HERE / "proposal_01"
    assert not out.exists()
    wrapper, original, script = inputs()
    journals = early_journal(wrapper)
    proposal = wrapper_change(wrapper, original, journals)
    model = Resource(proposal).normalize()
    assert not model["errors"], model["errors"]
    out.mkdir()
    resource = out / "mq037.questphase.json"
    reds = out / Path(SCRIPT).name
    write(resource, proposal)
    reds.write_text(script_change(script, journals), encoding="utf-8", newline="\n")
    write(out / "plan.json", {
        "resources": [{"depot": PRIVATE, "proposed_json": str(resource), "proposed_json_sha256": sha(resource)}],
        "script": {"path": SCRIPT, "source": str(reds), "sha256": sha(reds)},
        "policy": "Portable stage-start fallback for the native post-Dumpster wait and Theo introduction.",
    })


if __name__ == "__main__":
    main()
