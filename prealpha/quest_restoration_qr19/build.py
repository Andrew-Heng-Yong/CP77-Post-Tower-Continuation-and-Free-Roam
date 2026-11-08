"""Rearm the authored MQ018 final-SMS waits without replaying message producers."""
import sys
from pathlib import Path

from evidence import HERE, QR18, ENTRY, PRIVATE, NATIVE, MESSAGES, S29, IDS, CONTACT, WRITER, QR18_PIN, source, read, write, pin
from common import walk
from model import Resource

sys.path.insert(0, str(HERE.parent / "quest_restoration_qr13"))
from resource_edit import Edit
from finalize_brendan_holder import reset, unlink

SCRIPT = S29
DEPOTS = (ENTRY, PRIVATE + NATIVE, PRIVATE + MESSAGES)
SOCKET = "PTFRQR19_RetainedBartmoss"
EXTRA_ZERO = ("mq018_web_bartmosscollective_visited", "mq018_debug", "mq018_call_nancy_chicken", "ep1_standalone")
EXTRA_POSITIVE = ("q001_done", "q003_done", "q005_done", "q101_done", "q110_done")
RESERVATION = ("mq018_started", "mq018_active")
BRANCH = [("CutDestination", "CutDestination"), ("In", "Input"), ("True", "Output"), ("False", "Output")]


def sha(path):
    return pin(path)["sha256"]


def checked(path, expected):
    pin(path, expected)
    return Path(path)


def input_node(ed, root, node_id):
    return ed.add(root, {"$type": "questInputNodeDefinition", "id": node_id, "socketName": cname(SOCKET)},
                  [("CutDestination", "CutDestination"), ("Out", "Output")])


def cname(s):
    return {"$type": "CName", "$storage": "string", "$value": s}


def add_input(ed, node):
    assert all(ed.r.d(h)["name"]["$value"] != SOCKET for h in node["sockets"])
    node["sockets"].append(ed.h({"$type": "questSocketDefinition", "name": cname(SOCKET), "type": "Input", "connections": []}))


def entry(doc):
    ed = Edit(doc)
    root = ed.graph("root")
    previous = ed.r.normalize()["graphs"]["root"]
    nodes = reset(ed, root, previous)
    for i in ("65003", "65004"):
        node = nodes[i]
        original = node["condition"]
        cloned = ed.clone(original, ed.r)
        changed = []
        for r in walk(cloned):
            if r.get("$type") == "questVarComparison_ConditionType" and r.get("factName") in RESERVATION:
                assert r["value"] == 0 and r["comparisonType"] == "Equal"
                r["value"] = 1
                changed.append(r["factName"])
        assert set(changed) == set(RESERVATION) and len(changed) == 2
        payload = cloned["Data"]
        assert payload["operation"] == "AND"
        payload["conditions"].extend(ed.journal(CONTACT + "msg" + s, "gameJournalPhoneMessage", "Active") for s in IDS)
        payload["conditions"].extend(ed.fact(n, 0) for n in EXTRA_ZERO)
        payload["conditions"].extend(ed.fact(n, 0, "Greater") for n in EXTRA_POSITIVE)
        node["condition"] = ed.logic("OR", [original, cloned])
    select = ed.add(root, {"$type": "questConditionNodeDefinition", "id": 65008,
                           "condition": ed.logic("AND", [ed.fact(n, 1) for n in RESERVATION])}, BRANCH)
    add_input(ed, nodes["37"])
    unlink(ed, nodes["65006"], "Out", nodes["37"], "In1")
    ed.link(nodes["65006"], "Out", select, "In")
    ed.link(select, "False", nodes["37"], "In1")
    ed.link(select, "True", nodes["37"], SOCKET)
    return ed.ordered()


def handoff(doc, message_phase):
    ed = Edit(doc)
    root = ed.graph("root")
    start = input_node(ed, root, 65008)
    if message_phase:
        for i in (67, 69):
            ed.link(start, "Out", ed.node(root, i), "In")
    else:
        child = ed.node(root, 7)
        add_input(ed, child)
        ed.link(start, "Out", child, SOCKET)
    return ed.ordered()


def edit_script(text):
    text, tail = text.split("public class SideJobsS30 ", 1)
    def replace(old, new):
        nonlocal text
        assert text.count(old) == 1, old
        text = text.replace(old, new, 1)

    # Record the same extra native state in the sampled arrays so two samples
    # must agree. The existing full journal and progress checks remain in place.
    replace('    sample.valid = true; sample.reason = "Native state matches the original beginning.";',
            '''    let resumeMQ018 = i == 2 && this.HasMQ018Reservation();
    sample.valid = true; sample.reason = "Native state matches the original beginning.";
    if resumeMQ018 && !this.ReadMQ018MessageHistory(jm, qs, sample) {
      sample.valid = false;
      sample.reason = "Killing in the Name requires the retained Bartmoss messages and an untouched website objective.";
    }''')
    old = '''      actual = qs.GetFactStr(names[k]); ArrayPush(sample.facts, actual);
      if actual < minimum[k] || actual > maximum[k] {'''
    replace(old, '''      actual = qs.GetFactStr(names[k]); ArrayPush(sample.facts, actual);
      let matches = actual >= minimum[k] && actual <= maximum[k];
      if resumeMQ018 && (Equals(names[k], "mq018_started") || Equals(names[k], "mq018_active")) {
        matches = actual == 1;
      }
      if !matches {''')
    message_suffixes = ", ".join(f'"msg{x}"' for x in IDS)
    facts = ", ".join(f'"{x}"' for x in EXTRA_ZERO + EXTRA_POSITIVE)
    replace("  private func FreshOwner(i: Int32) -> Bool {", f'''  private func HasMQ018Reservation() -> Bool {{
    return this.Fact("mq018_started") == 1 && this.Fact("mq018_active") == 1;
  }}
  private func ReadMQ018MessageHistory(jm: ref<JournalManager>, qs: ref<QuestsSystem>, out sample: SideJobSampleS29) -> Bool {{
    let messages = [{message_suffixes}];
    let i = 0;
    while i < ArraySize(messages) {{
      let entry = jm.GetEntryByString("{CONTACT}" + messages[i], "gameJournalPhoneMessage");
      let state = IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1;
      ArrayPush(sample.states, state);
      if state != 2 {{ return false; }}
      i += 1;
    }}
    let facts = [{facts}];
    i = 0;
    while i < ArraySize(facts) {{
      let state = qs.GetFactStr(facts[i]);
      ArrayPush(sample.facts, state);
      if (i < {len(EXTRA_ZERO)} && state != 0) || (i >= {len(EXTRA_ZERO)} && state <= 0) {{ return false; }}
      i += 1;
    }}
    return true;
  }}
  private func Unclaimed(i: Int32) -> Bool {{
    return this.Own(i, "Ready") == 1 && this.Own(i, "Revision") == 1 && this.Own(i, "Issued") == 0 &&
      this.Own(i, "Entered") == 0 && this.Own(i, "Finished") == 0 && this.Own(i, "Fault") == 0;
  }}
  private func FreshOwner(i: Int32) -> Bool {{''')
    replace('''    return this.Own(i, "Ready") == 1 && this.Own(i, "Revision") == 1 && this.Own(i, "Issued") == 0 &&
      this.Own(i, "Entered") == 0 && this.Own(i, "Finished") == 0 && this.Own(i, "Fault") == 0;
  }
  private func Ready(i: Int32) -> Bool {
    return this.running && this.warmup == 0 && this.Common() && this.Safe() && this.FreshOwner(i);
  }''', '''    return this.Unclaimed(i);
  }
  private func Ready(i: Int32) -> Bool {
    return this.running && this.warmup == 0 && this.Common() && this.Safe() &&
      ((i == 2 && this.HasMQ018Reservation() && this.Unclaimed(i)) || this.FreshOwner(i));
  }''')
    replace("// Fresh original entries only. Existing progress is preserved; unsupported",
            "// Fresh original entries and the retained MQ018 message handoff. Unsupported")
    return text + "public class SideJobsS30 " + tail


def main():
    out = HERE / "proposal_01"
    assert not out.exists()
    assert read(HERE / "evidence_01.json")["status"] == "MQ018_SAVED_FINAL_SMS_LISTENERS_LOST_AFTER_TOWER"
    pack = read(checked(QR18 / "candidate_01/package_manifest.json", QR18_PIN))
    leaves = {r["path"]: r["sha256"] for r in pack["files"]}
    original = checked(QR18 / "candidate_01/package" / SCRIPT, leaves[SCRIPT])
    script = edit_script(original.read_text(encoding="utf-8-sig"))
    models = [entry(source(ENTRY)), handoff(source(DEPOTS[1]), False), handoff(source(DEPOTS[2]), True)]
    out.mkdir()
    rows = []
    for depot, doc in zip(DEPOTS, models, strict=True):
        n = Resource(doc).normalize()
        assert not n["errors"], (depot, n["errors"])
        p = out / (depot.split("\\")[-1] + ".json")
        write(p, doc)
        rows.append({"depot": depot, "proposed_json": str(p), "proposed_json_sha256": sha(p)})
    path = out / Path(SCRIPT).name
    path.write_text(script, encoding="utf-8", newline="\n")
    write(out / "plan.json", {"resources": rows, "script": {"path": SCRIPT, "source": str(path), "sha256": sha(path)}})


if __name__ == "__main__":
    main()
