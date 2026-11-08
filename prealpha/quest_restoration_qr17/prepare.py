"""Prepare a portable, earned post-Spray Paint handoff from the pinned Core."""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
QR13 = HERE.parent / "quest_restoration_qr13"
sys.path.insert(0, str(QR13))
from resource_edit import Edit, Resource, STANDARD, value
from finalize_brendan_holder import reset

PRIVATE = r"towercontinued\sidejobs_s23\base_b\mq037.questphase"
SCRIPT = "r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds"
PENDING = "PTFRQR17_MQ037_HandoffPending"
HELD = "PTFRQR13_MQ037_FinalSupportHeld"
TAG = "PTFRS23_MQ037"
COIN = "quests/minor_quest/mq037_brendan"
DUMPSTER = COIN + "_dumpster"
SPRAY = COIN + "_hooligan001"
EARNED = (
    DUMPSTER,
    DUMPSTER + "/mq037_brendan_dumpster/00_push_dumpster",
    DUMPSTER + "/mq037_brendan_dumpster/01_talk_brendan",
    SPRAY,
    SPRAY + "/mq037_brendan_hooligan/00_deal_with_the_hooligan",
    SPRAY + "/mq037_brendan_hooligan/01_talk_with_brendan",
)
NATIVE_FACTS = {
    "mq037_brendan_introduced": 1,
    "mq037_clerk_aggroed": 0,
    "mq037_clerk_convinced": 0,
    "mq037_done": 0,
    "mq037_final_scene_active": 0,
}
STAGE = {"Inactive": 1, "Succeeded": 3}
COND_SOCKETS = [("CutDestination", "CutDestination"), ("In", "Input"), ("True", "Output"), ("False", "Output")]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest().upper()


def checked(path, expected):
    path = Path(path)
    assert sha(path) == expected, path
    return path


def write(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent=2) + "\n")


def journal_samples(doc):
    root = Resource(doc)
    graph = root.d(root.root["graph"])
    n1002 = next(root.d(h) for h in graph["nodes"] if root.d(h)["id"] == 1002)
    outer = root.d(n1002["condition"])
    fresh = root.d(outer["conditions"][0])
    samples = {}
    for h in fresh["conditions"]:
        obj = root.d(h)
        if obj["$type"] != "questLogicalCondition":
            continue
        assert obj["operation"] == "OR" and len(obj["conditions"]) == 1
        child = root.d(obj["conditions"][0])
        payload = root.d(child["type"])
        assert payload["state"] == "Inactive"
        path = root.d(payload["path"])
        samples[path["realPath"]] = (value(path["className"]), h)
    assert len(samples) == 18 and set(EARNED) <= samples.keys()
    return {p: ("Inactive", c, h) for p, (c, h) in samples.items() if p == COIN or p.startswith(COIN + "/")} | {
        p: ("Succeeded", *samples[p]) for p in EARNED
    }


def edit_script(src, journal):
    def replace(old, new):
        nonlocal src
        assert src.count(old) == 1, old
        src = src.replace(old, new, 1)

    # Preserve the prior certificate rule on the original paths. The new path
    # only uses the current two consecutive settled samples and Common/Safe.
    replace('    if i == 13 && SnapshotStateHS1.AdmitsBrendanFinalQR13',
            '    if i == 13 && !SnapshotStateHS1.Admits(this.GetGameInstance(), SideJobDataS23.ID(i)) {\n'
            '      sample.valid = false; sample.reason = "Earlier Brendan routes require the existing history gate.";\n'
            '    }\n'
            '    if i == 13 && SnapshotStateHS1.Admits(this.GetGameInstance(), SideJobDataS23.ID(i)) && SnapshotStateHS1.AdmitsBrendanFinalQR13')
    replace('    if jm.HasAnyDelayedStateChanges() { sample.valid = false;', 
            '    if i == 13 && this.Own(i, "Entered") == 0 && this.ReadBrendanHandoff(paths, sample.states, names, sample.facts) {\n'
            '      sample.valid = true;\n'
            '      sample.reason = "Earned Spray Paint complete. Starting the native Coin Operated Boy handoff from its six-hour wait.";\n'
            '    }\n'
            '    if jm.HasAnyDelayedStateChanges() { sample.valid = false;')
    lines = ['  private func ReadBrendanHandoff(paths: array<String>, states: array<Int32>, names: array<String>, facts: array<Int32>) -> Bool {']
    terms = [f'BrendanFinalDataQR13.State(paths, states, "{p}") == {STAGE[s]}' for p, (s, _, _) in journal.items()]
    terms += [f'BrendanFinalDataQR13.Fact(names, facts, "{n}") == {v}' for n, v in NATIVE_FACTS.items()]
    lines.extend([('    return ' if i == 0 else '      ') + t + (';' if i + 1 == len(terms) else ' &&')
                  for i, t in enumerate(terms)])
    lines += ['  }', '']
    replace('  private func Same(a: SideJobSampleS23', '\n'.join(lines) + '  private func Same(a: SideJobSampleS23')
    replace('    if !SnapshotStateHS1.Admits(this.GetGameInstance(),SideJobDataS23.ID(i)) { return false; }',
            '    if i != 13 && !SnapshotStateHS1.Admits(this.GetGameInstance(),SideJobDataS23.ID(i)) { return false; }')
    return src


def unlink(editor, a, source, b, target):
    _, left = editor.socket(a, source)
    dest, right = editor.socket(b, target)
    cid, = (editor.r.hid(h) for h in left["connections"]
            if editor.r.hid(editor.r.d(h)["destination"]) == str(dest))
    for socket in (left, right):
        socket["connections"] = [h for h in socket["connections"] if editor.r.hid(h) != cid]


def edit_wrapper(doc, native, journal):
    editor = Edit(doc)
    root = editor.graph("root")
    baseline = Resource(doc).normalize()["graphs"]["root"]
    # The readback can store a socket definition inside an edge. Rebuild the
    # root's socket handles before unlinking so retained edges keep both ends.
    reset(editor, root, baseline)
    old = {i: editor.node(root, i) for i in (34, 1002, 1004, 1008, 1100, 1101, 1110)}
    # The first 15 terms are the shared Tower, PA2, and support guard. Keep
    # their checked payloads identical, including the killed and PONR terms.
    common = baseline["nodes"]["1100"]["reads"][:15]
    assert [r["factName"] for r in common] == [
        "PostTowerFreeRoamActive", "PTFRP0_DR13", "PTFRPA2_Finished", "PTFRPA2_Fault",
        "q307_done", "q307_finished", "q307_2079", "q307_main_game_killed", "q307_ep1_killed",
        "q307_active", "q307_debug_reset", "q115_point_of_no_return", "q305_johnny_scene_active",
        "PTFRU9_Support_Issued", "PTFRU9_Support_Fault",
    ]

    def handoff_gate(pending, held, permit):
        facts = {r["factName"]: r["value"] for r in common} | NATIVE_FACTS | {
            TAG + "_Issued": 0, TAG + "_Entered": 0, TAG + "_Finished": 0, TAG + "_Fault": 0,
            PENDING: pending, HELD: held,
        }
        if permit:
            facts[TAG + "_Permit"] = 1
        return editor.logic("AND", [editor.fact(n, v) for n, v in facts.items()] +
                            [editor.journal(p, cls, s) for p, (s, cls, _) in journal.items()])

    for node in (1002, 1004):
        editor.r.d(old[node]["condition"])["conditions"].append(handoff_gate(0, 0, True))

    def condition(i, cond):
        return editor.add(root, {"$type": "questConditionNodeDefinition", "id": i, "condition": cond}, COND_SOCKETS)

    def marker(i, name, v):
        payload = {"$type": "questSetVar_NodeType", "factName": name, "setExactValue": 1, "value": v}
        return editor.add(root, {"$type": "questFactsDBManagerNodeDefinition", "id": i, "type": editor.h(payload)}, STANDARD)

    def native_copy(i, source):
        payload = editor.clone(source, native.r, skip=("sockets",))
        payload["id"] = i
        sockets = [(value(s["name"]), s["type"]) for h in source["sockets"] if (s := native.r.d(h))]
        return editor.add(root, payload, sockets)

    original = native.graph("root/25")
    nodes = {
        1120: condition(1120, handoff_gate(0, 0, True)),
        1121: marker(1121, PENDING, 1),
        1122: condition(1122, editor.fact(PENDING, 1)),
        1123: native_copy(1123, native.node(original, 38)),
        1124: native_copy(1124, native.node(original, 39)),
        1125: condition(1125, handoff_gate(1, 1, False)),
        1126: native_copy(1126, native.node(original, 40)),
        1127: native_copy(1127, native.node(original, 36)),
        1128: marker(1128, TAG + "_Issued", 1),
        1129: marker(1129, TAG + "_Entered", 1),
        1130: marker(1130, PENDING, 0),
        1131: marker(1131, PENDING, 0),
    } | old
    unlink(editor, old[1100], "False", old[1008], "In")
    unlink(editor, old[1110], "Ready", old[1101], "In")
    for a, s, b, t in (
        (1100, "False", 1120, "In"), (1120, "False", 1008, "In"),
        (1120, "True", 1121, "In"), (1121, "Out", 1110, "In1"),
        (1110, "Ready", 1122, "In"), (1122, "False", 1101, "In"),
        (1122, "True", 1123, "In"), (1123, "Out", 1124, "In"),
        (1124, "Out", 1125, "In"), (1125, "False", 1131, "In"),
        (1131, "Out", 1110, "Release"), (1125, "True", 1128, "In"),
        (1128, "Out", 1126, "In"), (1126, "Out", 1127, "Inactive"),
        (1127, "Out", 1129, "In"), (1129, "Out", 1130, "In"),
        (1130, "Out", 34, "brendan_gone"),
    ):
        editor.link(nodes[a], s, nodes[b], t)
    return editor.ordered()


def main():
    out = HERE / "proposal_01"
    assert not out.exists()
    manifest = read(HERE.parent / "quest_restoration_qr14/deployment_01/installed_manifest_01.json")
    source = read(checked(manifest["core_source_epoch"], manifest["core_source_epoch_sha256"]))
    previous = read(QR13 / "coordinator/brendan_06/serialized_01/manifest.json")["resources"][0]
    assert previous["depot"] == PRIVATE and previous["raw_sha256"] == source["source_resources"][PRIVATE]
    checked(previous["raw"], previous["raw_sha256"])
    doc = read(checked(previous["readback_json"], previous["readback_json_sha256"]))
    native, = (r for r in read(QR13 / "brendan_provider_validation_01/manifest.json")["resources"]
               if r["depot"].endswith("mq037_brendan.questphase"))
    checked(native["raw"], native["sha256"])
    new_native = Edit(read(checked(native["json"], native["json_sha256"])))
    package = {r["path"]: r["sha256"] for r in source["package_files"]}
    script_input = checked(Path(source["candidate"]) / "package" / SCRIPT, package[SCRIPT])
    journal = journal_samples(doc)
    result = edit_wrapper(doc, new_native, journal)
    model = Resource(result).normalize()
    assert not model["errors"], model["errors"]
    script = edit_script(script_input.read_text(encoding="utf-8-sig"), journal)
    out.mkdir()
    wrapper = out / "mq037.questphase.json"
    script_file = out / Path(SCRIPT).name
    write(wrapper, result)
    script_file.write_text(script, encoding="utf-8", newline="\n")
    write(out / "plan.json", {
        "resources": [{"depot": PRIVATE, "proposed_json": str(wrapper), "proposed_json_sha256": sha(wrapper)}],
        "script": {"path": SCRIPT, "source": str(script_file), "sha256": sha(script_file)},
        "policy": "Portable runtime-earned post-Spray fallback; restart native six-hour wait only.",
    })


if __name__ == "__main__":
    main()
