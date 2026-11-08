"""Bind the 6 November saved Voodoo Treasure records to the installed wrapper."""

import base64
import binascii
import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
QR15 = HERE.parent / "quest_restoration_qr15"
sys.path[:0] = [str(QR15 / sub) for sub in ("event_stage_01", "rebind_01")]
from analyze_components import decode_paths, phase_hash
from analyze_native_layout import native_records, cname
from analyze import decode_freezer


DEPOT = r"towercontinued\sidejobs_s23\ep1\voodoo_boot.questphase"
XL = Path("C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc/mod/zzzz_PTFR_Combined.archive.xl")
XL_SHA = "F22693981B0A10DB21B47AFAD7FC8BCAEF1F021D9EA99548BA4FF80F56D18245"


def main():
    capture = HERE / "nov06_graph_capture.json"
    output = HERE / "nov06_wait.json"
    assert not output.exists()
    installed = XL.read_bytes()
    assert hashlib.sha256(installed).hexdigest().upper() == XL_SHA
    lines = installed.decode("utf-8-sig").splitlines()
    index, = (i for i, line in enumerate(lines) if line.strip() == f"- path: {DEPOT}")
    assert [line.strip() for line in lines[index + 1:index + 5]] == [
        r"parent: ep1\quest\ep1.quest", "input:", "node: [1]", "socket: Out"
    ]
    node = binascii.crc_hqx((DEPOT + ":1").encode("ascii"), 0xFFFF)
    assert node == 6479
    parent, wrapper = (1,), (1, node)
    parent_key = phase_hash(parent)
    samples = []
    for sample in json.loads(capture.read_text(encoding="utf-8-sig"))["results"]:
        components = sample["graph_components"]

        def component(name):
            row = components[name]
            raw = base64.b64decode(row["base64"], validate=True)
            assert len(raw) == row["size"]
            return raw, row["id"]

        _, paths = decode_paths(*component("customArray"))
        contexts = sorted({p for p in paths if p[:2] == wrapper})
        context_keys = {phase_hash(p): p for p in contexts}
        assert len(context_keys) == len(contexts)
        for path in paths:
            if path and path[0] in (0, 1):
                key = phase_hash(path)
                if key in context_keys:
                    assert context_keys[key] == path, "Ambiguous saved phase hash"
                if key == parent_key:
                    assert path == parent, "Ambiguous parent phase hash"
        relevant = {(parent_key, node)}
        events = native_records(*component("eventManager"))
        groups = decode_freezer(*component("questPhaseFreezer"))

        def selected(key):
            return key[0] in context_keys or key in relevant

        samples.append({
            "save": sample["source"], "sha256": sample["sha256"], "paths": contexts,
            "event_slots": [{"slot": i, "phase_hash": key, "node": n, "type_token": str(token),
                             "logical_condition": token == cname("questLogicalCondition")}
                            for i, (token, key, n) in enumerate(events) if selected((key, n))],
            "freezer_groups": [{"trigger": str(trigger), "owner": owner, "members": members}
                               for trigger, owner, members in groups
                               if selected(owner) or any(selected(k) for k, _ in members)],
        })
    with output.open("x", encoding="utf-8") as stream:
        json.dump({"wrapper": DEPOT, "id": node, "installed_xl_sha256": XL_SHA, "samples": samples,
                   "scope": "Exact saved registration membership. Does not resolve which condition failed in live play."},
                  stream, indent=2)
    for sample in samples:
        print(Path(sample["save"]).parent.name, sample["paths"], sample["event_slots"], sample["freezer_groups"])


if __name__ == "__main__":
    main()
