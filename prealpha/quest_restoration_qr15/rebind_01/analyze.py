"""Bind saved freezer records to the exact selected save and installed entry graph."""
from collections import defaultdict
from pathlib import Path
import argparse
import binascii
import json
import struct
import sys

HERE = Path(__file__).resolve().parent
QR15 = HERE.parent
WORK = HERE.parents[2]
sys.path[:0] = [str(QR15 / p) for p in ("latest_save_01", "event_stage_01", "saved_graph_state_01")]
sys.path.insert(0, str(WORK / "tools/parity_audit"))
from analyze_components import TARGET, decode_paths, phase_hash
from analyze_native_layout import cname, native_records
from compare import CURRENT_BODY, pin, pin_save, read
from inspect_native import EXE, Image
from model import Resource

DEPOT = r"towercontinued\native_gigs_u9\sts_ep1_03_entry.questphase"
PARENT = r"ep1\quest\ep1.quest"
STATUS = "SELECTED_SAVE_NATIVE_THAW_REBIND_UNAVAILABLE"


def decode_freezer(data, node_id):
    cursor = 0

    def take(fmt):
        nonlocal cursor
        layout = struct.Struct("<" + fmt)
        if layout.size > len(data) - cursor:
            raise ValueError("Truncated freezer record")
        fields = layout.unpack_from(data, cursor)
        cursor += layout.size
        return fields

    def key(packed):
        if packed & 0xFFFF0000:
            raise ValueError("Nonzero node bits discarded by pinned native load")
        return packed >> 32, packed & 0xFFFF

    actual, size, count = take("III")
    if actual != node_id or size != len(data) - 8 or count > (len(data) - cursor) // 20:
        raise ValueError("Invalid freezer header")
    groups = []
    for _ in range(count):
        trigger, owner, members = take("QQI")
        if members > (len(data) - cursor) // 12:
            raise ValueError("Invalid freezer member count")
        entries = []
        for _ in range(members):
            member, words = take("QI")
            if words > (len(data) - cursor) // 8:
                raise ValueError("Invalid deferred input count")
            entries.append((key(member), take(f"{words}Q")))
        groups.append((trigger, key(owner), entries))
    if cursor != len(data):
        raise ValueError("Trailing freezer bytes")
    return groups


def decoder_controls(data, node_id):
    rejected = []
    # Offsets here come from the native writer and the first group in the actual capture.
    for label, offset, value in (
        ("node ID", 0, node_id ^ 1),
        ("blob size", 4, len(data)),
        ("group count", 8, 0xFFFFFFFF),
        ("owner bits lost on native load", 22, 1),
        ("member count", 28, 0xFFFFFFFF),
        ("deferred count", 40, 0xFFFFFFFF),
    ):
        broken = bytearray(data)
        struct.pack_into("<H" if offset == 22 else "<I", broken, offset, value)
        rejected.append((label, bytes(broken)))
    rejected.extend([("truncated", data[:-1]), ("trailing byte", data + b"\0")])
    for label, broken in rejected:
        try:
            decode_freezer(broken, node_id)
        except ValueError:
            continue
        raise AssertionError(f"Accepted malformed capture: {label}")
    # One independent minimal encoding from the documented field widths.
    payload = bytes.fromhex(
        "01000000 2c000000 01000000 0100000000000000 0300000002000000 "
        "01000000 0500000004000000 01000000 0807060504030201"
    )
    assert decode_freezer(payload, 1) == [(1, (2, 3), [((4, 5), (0x0102030405060708,))])]
    return {"rejected": [label for label, _ in rejected], "nonempty_reference_decoded": True}


def native_evidence():
    image = Image()
    tables = {0x306F9B0: {0x18: 0xBEB194, 0x88: 0x2CD98E0, 0x90: 0x2CD9978, 0x98: 0x7398A0},
              0x30BCE78: {0x240: 0xBEA6CC}}
    for table, slots in tables.items():
        for slot, expected in slots.items():
            assert struct.unpack_from("<Q", image.data, image.off(table + slot))[0] - image.base == expected
    assert image.data[image.off(0x3077FC8):image.off(0x3077FC8) + 18] == b"questPhaseFreezer\0"
    ranges = [
        (0x6976F2, 0x69771C), (0x697743, 0x69774F), (0x738AB4, 0x738ABB),
        (0x2C9F4BC, 0x2C9F4CF), (0x7396BF, 0x7396D2), (0x2CD99BA, 0x2CD99E5),
        (0x2CD9AB6, 0x2CD9B3A), (0x2CD9B4B, 0x2CD9BA1), (0x739960, 0x739979),
        (0x43891B, 0x438934), (0x438947, 0x4389EE), (0x438A94, 0x438AA8),
        (0xBEB4E7, 0xBEB4F0), (0xBEB5A9, 0xBEB5D7), (0xBEA6FD, 0xBEA716),
        (0xBEA72D, 0xBEA7A4), (0xBEA81D, 0xBEA83F),
    ]
    instructions = {}
    for start, stop in ranges:
        rows = image.disasm(start)["instructions"]
        selected = [row for row in rows if start <= int(row["rva"], 16) < stop]
        assert selected, hex(start)
        instructions[hex(start)] = selected
    return {"exe": {"path": str(EXE), "sha256": image.sha}, "vtables_rva": tables,
            "instructions_by_range_start": instructions}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = HERE / args.out
    if out.parent != HERE or out.exists():
        raise ValueError("Use a fresh output directory next to this script")

    prior = QR15 / "latest_save_01/completion.json"
    comparison_pin = read(prior)["result"]
    pins = [pin(prior), pin(comparison_pin["path"], comparison_pin["sha256"])]
    comparison = read(comparison_pin["path"])
    save = comparison["selected_save"]
    assert save["slot"] == "AutoSave-8" and save["inputs"][0]["sha256"] == CURRENT_BODY
    for row in save["inputs"]:
        pin_save(Path(row["path"]), row["sha256"])
    assert comparison["registrations"]["current_jason_slots"] == 0

    capture_path = QR15 / "event_stage_01/components_01/manifest.json"
    capture = read(capture_path)
    assert capture["source_sha256"] == CURRENT_BODY
    pins.append(pin(capture_path))
    rows = {row["name"]: row for row in capture["nodes"]}

    def component(name):
        row = rows[name]
        pins.append(pin(row["path"], row["sha256"]))
        return Path(row["path"]).read_bytes(), row["id"]

    _, paths = decode_paths(*component("customArray"))
    by_hash = defaultdict(set)
    for path in paths:
        by_hash[phase_hash(path)].add(path)
    events = native_records(*component("eventManager"))
    freezer, node_id = component("questPhaseFreezer")
    groups = decode_freezer(freezer, node_id)

    earlier_path = QR15 / "earlier_saves_01/analysis_02/result.json"
    pins.append(pin(earlier_path))
    native_targets = read(earlier_path)["native_query_bindings"]
    exact = {(tuple(row["path"]), row["node"]): name for name, row in native_targets.items()}
    native_contexts = {path for path in paths if path[:len(TARGET)] == TARGET}
    for path in native_contexts | {path for path, _ in exact}:
        assert by_hash[phase_hash(path)] == {path}, path
    native_hashes = {phase_hash(path) for path in native_contexts}
    assert not any(h in native_hashes and token and node != 0xFFFF for token, h, node in events)

    baseline_path = QR15 / "preservation.json"
    pins.append(pin(baseline_path))
    installed = read(baseline_path)["checks"]
    xl, = (row for row in installed if Path(row["path"]).name == "zzzz_PTFR_Combined.archive.xl")
    archive, = (row for row in installed if Path(row["path"]).name == "zzzz_PTFR_Combined.archive")
    pins.extend(pin(row["path"], row["expected"]) for row in (xl, archive))
    lines = Path(xl["path"]).read_text(encoding="utf-8-sig").splitlines()
    header, = (i for i, line in enumerate(lines) if line.strip() == f"- path: {DEPOT}")
    assert [line.strip() for line in lines[header + 1:header + 5]] == [
        f"parent: {PARENT}", "input:", "node: [1]", "socket: Out"]
    private_id = binascii.crc_hqx((DEPOT + ":1").encode("ascii"), 0xFFFF)
    assert private_id == 48952
    crc_source = WORK / "research/framework_pr63_01/archivexl/src/App/Extensions/QuestPhase/Extension.cpp"
    source_text = crc_source.read_text(encoding="utf-8")
    assert 'aPhaseMod.phasePath + ":" + std::to_string(aParentID)' in source_text
    assert 'uint16_t crc = 0xFFFF;' in source_text
    pins.append(pin(crc_source))

    def normalize_provider(folder, depot, archive_path=None):
        manifest = QR15 / folder / "manifest.json"
        pins.append(pin(manifest))
        provider, = (row for row in read(manifest)["resources"] if row["depot"] == depot)
        if archive_path is not None:
            assert Path(provider["archive"]) == Path(archive_path)
        pins.extend([pin(provider["raw"], provider["sha256"]), pin(provider["json"], provider["json_sha256"])])
        normal = Resource(read(provider["json"])).normalize()
        assert not normal["errors"], normal["errors"]
        return normal["graphs"]

    native_root = normalize_provider("root_binding_providers_01", PARENT)["root"]
    assert str(private_id) not in native_root["nodes"] and "1" in native_root["nodes"]
    graph = normalize_provider("providers_01", DEPOT, archive["path"])
    gate = graph["root"]["nodes"]["50"]
    child = graph["root/50"]
    pause = child["nodes"]["65002"]
    assert gate["type"] == "questPhaseNodeDefinition" and gate["node_refs"] == ["#combat_zone_content_tr"]
    assert pause["type"] == "questPauseConditionNodeDefinition"
    gate_edges = [["65002", "Out", "65007", "In"], ["65007", "Out", "65003", "In"],
                  ["65004", "Out", "19", "In1"]]
    assert all(edge in child["edges"] for edge in gate_edges)
    assert any(c.get("operation") == "AND" or c.get("operation") == "And" for c in pause["conditions"]), pause["conditions"][0]
    for fact in ("PTFRU9_sts_ep1_03_Request", "PTFRU9_sts_ep1_03_Permit"):
        assert any(row["factName"] == fact and row["comparisonType"] == "Equal" and row["value"] == 1
                   for row in pause["reads"])

    def binding(key):
        hash32, node = key
        path, = by_hash[hash32]
        name = exact.get((path, node))
        return {"hash": f"0x{hash32:08X}", "path": path, "node": node,
                "native_jason": name is not None or path[:len(TARGET)] == TARGET, "exact_query": name}

    report_groups = []
    private = []
    for ordinal, (trigger, owner, members) in enumerate(groups):
        record = {"ordinal": ordinal, "trigger_u64": f"0x{trigger:016X}", "owner": binding(owner),
                  "members": [binding(key) | {"deferred_words": [f"0x{word:016X}" for word in words]}
                              for key, words in members]}
        report_groups.append(record)
        if any(row["path"][:2] == (1, private_id) for row in [record["owner"], *record["members"]]):
            private.append(record)
    assert all(not row["native_jason"] for group in report_groups for row in [group["owner"], *group["members"]])
    u9, = private
    assert (u9["owner"]["path"], u9["owner"]["node"]) == ((1, private_id), 50)
    assert [(row["path"], row["node"], row["deferred_words"]) for row in u9["members"]] == [
        ((1, private_id), 50, []), ((1, private_id, 50), 65002, [])]
    top_events = [(ordinal, f"0x{token:016X}") for ordinal, (token, h, node) in enumerate(events)
                  if h == phase_hash((1,)) and node == private_id]
    phase_type = "questPhaseNodeDefinition"
    assert top_events == [(8305, f"0x{cname(phase_type):016X}")], top_events
    assert not any(by_hash[h] & {(1, private_id), (1, private_id, 50)} for _, h, _ in events)

    codeware, = (row for row in read(QR15 / "baseline.json")["installed"]
                 if Path(row["path"]).name == "Codeware.dll")
    pins.append(pin(codeware["path"], codeware["sha256"]))
    assert b"ExecuteNode\0" in Path(codeware["path"]).read_bytes()
    codeware_source = WORK / "research/framework_pr63_01/codeware"
    api = codeware_source / "scripts/Quest/QuestsSystem.reds"
    impl = codeware_source / "src/App/Quest/QuestsSystemEx.hpp"
    pins.extend([pin(api), pin(impl)])
    assert "native func ExecuteNode(" in api.read_text(encoding="utf-8")
    impl_text = impl.read_text(encoding="utf-8")
    assert all(line in impl_text for line in ("CreateContext(this, &context, 1, 0, -1, -1)",
                                             "context.phaseStack.PushBack(rootPhaseInstance)", "RTTI_METHOD(ExecuteNode)"))

    result = {
        "status": STATUS, "selected_save": save, "input_pins": pins,
        "freezer": {"component_id": node_id, "bytes": len(freezer), "groups": report_groups,
                    "member_count": sum(len(group["members"]) for group in report_groups),
                    "deferred_word_count": sum(len(row["deferred_words"]) for group in report_groups for row in group["members"]),
                    "queried_native_addresses": native_targets, "native_matches": 0},
        "private_gate": {"registration_line_1_based": header + 1, "depot": DEPOT, "parent": PARENT,
                         "generated_id": private_id, "save_event_slots": top_events, "save_event_type": phase_type,
                         "freezer_group": u9,
                         "unfreeze_trigger_reference": gate["node_refs"][0], "graph_edges": gate_edges,
                         "pause_predicates": pause["reads"], "ronald_writes": child["nodes"]["65007"]["writes"]},
        "native": native_evidence(), "controls": decoder_controls(freezer, node_id),
        "codeware_boundary": "Pinned DLL contains the ExecuteNode name. Retained framework source executes in root context mode 1; this is not evidence of a saved slot rebind.",
        "limits": ["The deferred-input loop does not recreate missing native waits. Other live callbacks are outside this test.",
                   "The freezer record does not establish actual private handler liveness, native actor setup or applied vehicle commands."],
        "runtime_candidate": None, "game_calls": 0, "save_writes": 0,
    }
    for row in save["inputs"]:
        pin_save(Path(row["path"]), row["sha256"])
    out.mkdir()
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{STATUS}: {len(groups)} groups, {result['freezer']['member_count']} members, "
          f"{result['freezer']['deferred_word_count']} deferred words, 0 original Jason records")


if __name__ == "__main__":
    main()
