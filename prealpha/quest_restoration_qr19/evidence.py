"""Bind the MQ018 reservation and message waits to the recorded save bytes."""
import base64
from collections import defaultdict
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
QR18 = HERE.parent / "quest_restoration_qr18"
QR15 = HERE.parent / "quest_restoration_qr15"
QR6 = HERE.parent / "quest_restoration_qr6/groups/A01/verification_03"
sys.path[:0] = [str(QR15 / p) for p in ("event_stage_01", "rebind_01", "latest_save_01")]
sys.path.insert(0, str(HERE.parents[1] / "tools/parity_audit"))
from analyze import decode_freezer
from analyze_components import decode_paths, phase_hash
from analyze_native_layout import native_records, cname
from compare import CURRENT_BODY, fact_key, pin, pin_save, read
from model import Resource

STEM = r"base\quest\minor_quests\mq018"
NATIVE = STEM + r"\mq018.questphase"
MESSAGES = STEM + r"\phases\mq018_01_msgs.questphase"
MINOR = r"base\quest\minor_quests\minorquests.questphase"
ENTRY = r"towercontinued\sidejobs_s29\entries\mq018_writer.questphase"
OTHER_ENTRY = r"towercontinued\sidejobs_s29\entries\mq028_stalker.questphase"
PRIVATE = r"towercontinued\sidejobs_s29\native" + "\\"
NANCY = r"towercontinued\sidejobs_s29\phone\nancy.questphase"
S29 = "r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds"
WRITER = "PTFRS29_mq018_writer"
IDS = ("01", "02", "05", "06", "07")
CONTACT = "contacts/bartmoss/bartmoss_spam/"
QR18_PIN = "F5137935D9A01E7DB9B8D531856B2DE6B3854E765923ABF6EC1C43665729A3EA"


def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(value, indent=2) + "\n")


def source(depot, pins=None):
    sources = QR6 / "source_pins.json"
    matches = [r for r in read(sources) if r.get("depot") == depot]
    row = matches[0]
    assert all(r["sha256"] == row["sha256"] for r in matches)
    selected = [pin(row["binary"], row["sha256"]), pin(row["json"], row["json_sha256"])]
    if depot.startswith("towercontinued"):
        package = QR18 / "candidate_01/package_manifest.json"
        pin(package, QR18_PIN)
        assert read(package)["source_resources"][depot] == row["sha256"]
        selected.append(pin(QR18 / "candidate_01/archive_source" / depot, row["sha256"]))
    if pins is not None:
        pins.extend(selected)
    return read(row["json"])


def model(depot, pins):
    result = Resource(source(depot, pins)).normalize()
    assert not result["errors"], (depot, result["errors"])
    return result["graphs"]


def saved_paths(events, paths, prefix, freezer=()):
    expected = {p for p in paths if p[:len(prefix)] == prefix}
    expected.add(prefix[:-1])
    by_hash = defaultdict(set)
    for p in set(paths) | expected:
        by_hash[phase_hash(p)].add(p)
    lookup = {}
    for p in expected:
        h = phase_hash(p)
        assert by_hash[h] == {p}, p
        lookup[h] = p

    def matches(h, n):
        return h in lookup and (lookup[h] != prefix[:-1] or n == prefix[-1])

    found = [{"slot": i, "path": lookup[h], "node": n, "type": f"0x{t:016X}"}
             for i, (t, h, n) in enumerate(events) if t and n != 0xFFFF and matches(h, n)]
    frozen = [{"group": i, "path": lookup[h], "node": n}
              for i, (_, owner, members) in enumerate(freezer)
              for h, n in [owner, *(key for key, _ in members)] if matches(h, n)]
    return {"native_path": prefix, "interned": sorted(expected - {prefix[:-1]}), "events": found, "freezer": frozen}


def analyze():
    pins = []
    installed_path = QR18 / "deployment_01/installed_manifest_01.json"
    installed = read(installed_path)
    pins.append(pin(installed_path))
    assert installed["core_epoch"] == "QR18"
    for row in installed["core_files"]:
        if row["path"].endswith(("zzzz_PTFR_Combined.archive", "zzzz_PTFR_Combined.archive.xl")) or row["path"] == S29:
            pins.append(pin(Path(installed["game_root"]) / row["path"], row["sha256"]))
    pins.append(pin(installed["core_source_epoch"], QR18_PIN))

    latest = QR15 / "latest_save_01/compare_01/result.json"
    pins.append(pin(latest))
    saved = read(latest)["selected_save"]
    assert saved["inputs"][0]["sha256"] == CURRENT_BODY
    for row in saved["inputs"]:
        pin_save(Path(row["path"]), row["sha256"])
    current_meta = read(saved["inputs"][1]["path"])["Data"]["metadata"]
    assert "mq028" in current_meta["finishedQuests"].split() and "mq018" not in current_meta["finishedQuests"].split()
    root_path = QR15 / "root_saved_resource_array_01/extraction.json"
    pins.append(pin(root_path))
    root = read(root_path)
    assert root["source_sha256"] == CURRENT_BODY
    pins.append(pin(root["gap_path"], root["gap_sha256"]))
    assert root["gap_sha256"] == "089255A038FA4296830F5C79DFB1F6871A33018839E59A39F0E813B7246DAE2E"
    saved_root = Path(root["gap_path"]).read_bytes()
    cap_path = QR15 / "event_stage_01/components_01/manifest.json"
    pins.append(pin(cap_path))
    cap = read(cap_path)
    assert cap["source_sha256"] == CURRENT_BODY

    def component(name):
        row, = (r for r in cap["nodes"] if r["name"] == name)
        pins.append(pin(row["path"], row["sha256"]))
        return Path(row["path"]).read_bytes(), row["id"]

    _, paths = decode_paths(*component("customArray"))
    events = native_records(*component("eventManager"))
    groups = decode_freezer(*component("questPhaseFreezer"))
    original = (0, 2, 82, 6, 37)
    other = (0, 2, 82, 6, 41)
    current = {"writer": saved_paths(events, paths, original, groups), "stalker": saved_paths(events, paths, other, groups)}
    assert all(not x["events"] and not x["freezer"] for x in current.values())

    earlier_path = QR15 / "earlier_saves_01/capture_03/wa1backup16.json"
    pins.append(pin(earlier_path))
    earlier = read(earlier_path)
    for path, digest in ((earlier["source"], earlier["source_sha256"]), (earlier["metadata"], earlier["metadata_sha256"])):
        pins.append(pin_save(Path(path), digest))
    assert saved_root == base64.b64decode(earlier["resource_array_base64"], validate=True)
    older_meta = read(earlier["metadata"])["Data"]["metadata"]
    assert older_meta["playthroughID"] == current_meta["playthroughID"]
    assert "mq028" in older_meta["finishedQuests"].split()

    def old_component(name):
        row = earlier["components"][name]
        raw = base64.b64decode(row["base64"], validate=True)
        assert len(raw) == row["bytes"]
        return raw, row["id"]

    _, old_paths = decode_paths(*old_component("customArray"))
    old_events = native_records(*old_component("eventManager"))
    historic = saved_paths(old_events, old_paths, original)
    assert {(r["path"], r["node"], r["type"]) for r in historic["events"]} == {
        (path, node, f"0x{cname(kind):016X}") for path, node, kind in (
            (original[:-1], 37, "questPhaseNodeDefinition"), (original, 7, "questPhaseNodeDefinition"),
            (original + (7,), 67, "questJournalEntryVisited_ConditionType"),
            (original + (7,), 69, "questJournalEntry_ConditionType"),
        )
    }

    facts_path = QR15 / "stores_autosave8_01/facts.json"
    pins.append(pin(facts_path))
    store = read(facts_path)
    assert store["sha256"] == CURRENT_BODY and store["metadata_sha256"] == saved["inputs"][1]["sha256"]
    table, = (r for r in store["tables"] if r["physical_child_ordinal"] == 1)
    raw = {int(r["key_u32"]): r["value_u32"] for r in table["entries"]}
    assert len(raw) == len(table["entries"])
    selected = {n: raw.get(fact_key(n)) for n in (
        "mq018_started", "mq018_active", "mq018_done", "mq018_visit_website", "mq018_web_bartmosscollective_visited",
        "mq028_started", "mq028_active", "mq028_done", "sq011_done", "sq031_done", "q307_main_game_killed",
        "PTFRS29_PHONE_nancy_Issued", *(f"{WRITER}_{n}" for n in ("Ready", "Revision", "Permit", "Issued", "Entered", "Finished", "Fault")))}
    assert selected["mq018_started"] == selected["mq018_active"] == selected["mq028_done"] == 1
    assert selected[f"{WRITER}_Issued"] is None

    parent = model(MINOR, pins)["root"]
    assert parent["nodes"]["37"]["refs"] == [NATIVE]
    assert parent["nodes"]["41"]["refs"] == [r"base\quest\minor_quests\mq028\mq028.questphase"]
    native = model(NATIVE, pins)["root"]
    msgs = model(MESSAGES, pins)["root"]
    for e in (["0", "Out", "4", "In"], ["4", "Out", "3", "In"], ["3", "Out", "7", "In1"]):
        assert e in native["edges"]
    for e in (["55", "Out", "67", "In"], ["55", "Out", "69", "In"], ["67", "Out", "71", "In2"],
              ["69", "Out", "71", "In1"], ["71", "Out1", "117", "In"], ["119", "Out", "8", "Active"]):
        assert e in msgs["edges"]
    for node, msg in zip(("50", "51", "53", "54", "55"), IDS, strict=True):
        assert msgs["nodes"][node]["journal_paths"] == [CONTACT + "msg" + msg]
        assert msgs["nodes"][node]["payload"]["type"]["sendNotification"] == 1
    for depot in (PRIVATE + NATIVE, PRIVATE + MESSAGES, NANCY, OTHER_ENTRY):
        model(depot, pins)
    gate = model(ENTRY, pins)["root"]["nodes"]
    assert all({("mq018_started", 0), ("mq018_active", 0), ("PTFRS29_PHONE_nancy_Issued", 1)} <=
               {(r["factName"], r["value"]) for r in gate[i]["reads"] if "factName" in r} for i in ("65003", "65004"))
    assert selected["PTFRS29_PHONE_nancy_Issued"] is None
    report = {"status": "MQ018_SAVED_FINAL_SMS_LISTENERS_LOST_AFTER_TOWER", "pins": pins, "latest_save": saved,
              "historical_waits": historic, "historical_body_sha256": earlier["source_sha256"],
              "current_registrations": current, "current_selected_facts": selected, "mq028_finished_in_both_metadata": True,
              "same_playthrough_id": True, "uninterrupted_ancestry_proven": False,
              "missing_named_fact": "null means no physical row", "current_message_journal_state": "UNOBSERVED"}
    for row in saved["inputs"]:
        pin_save(Path(row["path"]), row["sha256"])
    write(HERE / "evidence_01.json", report)
    print(report["status"])


if __name__ == "__main__":
    analyze()
