"""Independently verify the serialized phone tail, native ABI and source inputs."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
import struct
import sys

HERE = Path(__file__).resolve().parent
PRE = HERE.parent
REGISTRY = PRE / "quest_resume_registry_20261112_01"
RD10 = PRE / "resume_dispatcher_rd10_kirk_20261113_01"
sys.path.insert(0, str(PRE / "universal_resume_20261114_01"))
sys.path.insert(0, str(PRE / "quest_restoration_qr15/saved_graph_state_01"))
from read_handlers import phase_hash, saved_components, token
from model import normalize, load_export, reachable, resource_refs
from inspect_native import Image

ENTRY = r"towercontinued\sidejobs_s29\entries\mq058_semimaru_crystalcoat.questphase"
REPLY = r"towercontinued\sidejobs_s29\continuation\mq058_claire_reply.questphase"
DONOR = r"towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq058\phases\mq058_quest_resolution.questphase"
TAIL = {1,80,84,88,89,90,91,92,93,94,95,96,97,98,99,104,106,108,109,110,111,114,115,116,117,118,119,
        190,191,198,201,203,205,206,208,209,210}


def digest(path):
    return sha256(path.read_bytes()).hexdigest().upper()


def graph(path):
    selected = normalize(load_export(path))
    root, = selected["graphs"]
    assert root["kind"] == "quest" and not root["unresolved_connections"]
    return root, selected["support"]


def by_id(root):
    return {item["id"]: item for item in root["nodes"]}


def original_export(database, depot):
    path, expected = database.execute("SELECT export_path,export_sha256 FROM resources WHERE depot=? AND role='PTFR'",
                                      (depot,)).fetchone()
    p = Path(path)
    assert digest(p) == expected
    return graph(p)


def verify_graph(attempt, game):
    where = HERE / f"graph_{attempt:02}"
    db_path = REGISTRY / "registry_02/registry.sqlite3"
    with sqlite3.connect(db_path.resolve().as_uri()+"?mode=ro",uri=True) as db:
        before, entry_support = original_export(db,ENTRY)
        body, phone_support = original_export(db,DONOR)
    entry, entry_support_after = graph(where / "entry.questphase.json")
    phone, phone_support_after = graph(where / "reply.questphase.json")
    assert entry_support == entry_support_after and phone_support == phone_support_after
    assert not phone_support["phasePrefabs"] and not phone_support["inplacePhases"]
    assert not phone_support["embedded_resources"]
    old, new, donor, reply = map(by_id,(before,entry,body,phone))
    assert new.keys() == old.keys() | {61100,61101,61102,61103}
    assert all(new[node] == old[node] for node in old)
    assert reply.keys() == TAIL | {61110,61111}
    for node in TAIL:
        assert reply[node]["parameters"] == donor[node]["parameters"], node
        assert reply[node]["sockets"] == donor[node]["sockets"], node
    expected_phone_edges = [e for e in body["edges"] if e[0] in TAIL and e[3] in TAIL]
    assert Counter(phone["edges"]) == Counter(expected_phone_edges) + Counter([
        (61110,"Out","Output",80,"In","Input"),
        (61110,"Out","Output",61111,"In","Input"),
        (61111,"Out","Output",191,"In1","Input"),
    ])
    assert reachable({61110},[(a,b) for a,_,_,b,_,_ in phone["edges"]]) == TAIL | {61110,61111}
    assert reply[61111]["parameters"]["condition"]["type"]["factName"] == "PTFRClaire_TimerReady"
    assert all(not resource_refs(row["parameters"]) for row in reply.values())
    assert all("Reward" not in row["type"] and "Spawn" not in row["type"] and
               "Fact" not in row["type"] and "GameManager" not in row["type"] for row in reply.values())
    assert reply[1]["parameters"]["type"] == "Terminating"
    assert reply[80]["parameters"]["condition"]["type"]["days"] == 2
    assert resource_refs(new[61102]["parameters"]) == [REPLY]
    expected_entry_edges = [
        (65000,"Out","Output",61100,"In","Input"),
        (61100,"Out","Output",61101,"In","Input"),
        (61101,"Out","Output",61102,"Resume Claire Reply","Input"),
        (61102,"Output","Output",61103,"In","Input"),
    ]
    assert Counter(entry["edges"]) == Counter(before["edges"]) + Counter(expected_entry_edges)
    assert new[61101]["parameters"]["type"]["factName"] == "PTFRClaire_Issued"
    assert new[61103]["parameters"]["type"]["factName"] == "PTFRClaire_Finished"
    guard = {item["type"]["factName"]: item["type"]["value"]
             for item in new[61100]["parameters"]["condition"]["conditions"]}
    assert guard == {"PTFRClaire_Permit":1,"PTFRClaire_Issued":0,"PostTowerFreeRoamActive":1,
                     "q307_done":1,"q307_finished":1,"q307_main_game_killed":1,"q307_ep1_killed":1,
                     "mq058_done":1,"mq058_update_applied":1,"mq058_active":0,
                     "PTFRS29_mq058_semimaru_crystalcoat_Issued":0}
    from binascii import crc_hqx
    xl = game / "archive/pc/mod/zzzz_PTFR_Combined.archive.xl"
    assert digest(xl) == "2882999CABAA0777BDAC18834A99BE92148922A91519B295A5EF994672AD2590"
    assert f"path: {ENTRY}\n      parent: ep1\\quest\\ep1.quest\n      input:\n        node: [1]" in xl.read_text(encoding="utf-8-sig")
    entry_id = crc_hqx((ENTRY+":1").encode(),0xFFFF)
    assert entry_id == 141 and phase_hash((1,entry_id,61102)) == 0xC37CF97F
    assert phase_hash((0,2,82,4,9,3,98,103)) == 0xCCF9887E
    return {ENTRY: digest(where/"entry.questphase"), REPLY: digest(where/"reply.questphase")}


def verify_native(build):
    image = Image()
    source = HERE / "ReplyProbe.cpp"
    receipt = json.loads((build/"build.json").read_bytes())
    paths = {
        "source": source, "checks": HERE/"ReplyChecks.cpp", "header": HERE/"ReplyHandoff.hpp",
        "game_time": PRE/"universal_resume_eagles_20261114_01/GameTimeWait.hpp",
        "slots": PRE/"universal_resume_retirement_20261114_01/RetiredQuestSlot.hpp",
        "phase_address": PRE/"universal_resume_owner_20261114_01/OwnerTrace.hpp",
    }
    assert {key:digest(path) for key,path in paths.items()} == receipt["sources"]
    assert digest(build/"PTFR_ClaireReply.dll") == receipt["dll_sha256"]
    hooks = {}
    for address, prefix in re.findall(r'MakeHook\((0x[0-9A-F]+),"([^"]+)"',source.read_text()):
        span = bytes.fromhex(prefix.replace("\\x",""))
        offset=image.off(int(address,16))
        assert len(span)==8 and image.data[offset:offset+8]==span, address
        hooks[address]=prefix
    assert len(hooks)==12
    expected = {
        0x3040630+0x60:0x2B0800,0x30BCE78+0x200:0x88BC58,0x306FA58+0x10:0x2B2270,
        0x30BD228+0x240:0xA09BC4,0x30BD228+0x1C8:0x468358,0x30A75A8+0x120:0x193B00,
        0x31C2388+0x10:0x193C74,0x36A1D50+0x10:0x1304ED8,0x36A1D20+0x10:0x1304ED8,
    }
    for address, target in expected.items():
        assert struct.unpack_from("<Q",image.data,image.off(address))[0] == image.base + target
    return {"exe_sha256": image.sha,"hooks": hooks,"vtable_slots": len(expected),"build": receipt}


def verify_saved_owners():
    root=PRE/"handler_preservation_hp1_20261112_01/saves_01"
    original=(0,2,82,4,9,3,98,103)
    phase=phase_hash(original)
    journal=token("questJournalEntryState_ConditionType")
    expected={80:token("questGameTimeDelay_ConditionType"),88:journal,89:journal,90:journal,
              209:token("questVarComparison_ConditionType")}
    rows={}
    for slot in ("ManualSave-26","AutoSave-10","AutoSave-11","AutoSave-5"):
        digest_saved, paths, events, _ = saved_components(root/slot/"manifest.json")
        assert paths.get(phase,set()) in ({original},set())
        found = [(node,t) for t,p,node in events if t and p==phase]
        expected_rows = expected if slot in ("ManualSave-26","AutoSave-10") else {}
        assert len(found)==len(expected_rows) and dict(found)==expected_rows
        rows[slot]={"sha256":digest_saved,"registrations":found}
    journal_path=PRE/"universal_resume_eagles_20261114_01/evidence_18/journal.json"
    assert digest(journal_path)=="ED548F1F02C2765BDD62E2119A11090ED28C0AA78992116496D780DBC4A0B73A"
    after=json.loads(journal_path.read_bytes())["saves"]
    for saved in after:
        assert saved["facts"]["q307_finished"]==saved["facts"]["mq058_done"]==1
        assert saved["facts"]["mq058_update_applied"]==1
        assert saved["journal_state"]["contacts/marianne/mq058_02_resolution/01a_v"]==2
        assert saved["journal_state"]["contacts/marianne/mq058_02_resolution/01a_v/01a_ch1_1"]==2
    return {"original_registration_projections":rows,
            "post_tower_phone_state_projections":[s["slot"] for s in after]}


def main():
    p = argparse.ArgumentParser()
    for arg in ("graph","build","compile","attempt"):
        p.add_argument("--"+arg,type=int,required=True)
    args = p.parse_args()
    m = RD10 / "deployment_01/installed_manifest_01.json"
    md = json.loads(m.read_bytes())
    game = Path(md["game_root"])
    for item in md["core_files"] + md["required_files"]:
        assert digest(game/item["path"]) == item["sha256"], item["path"]
    compile_dir = HERE / f"compile_{args.compile:02}"
    compiled = json.loads((compile_dir/"receipt.json").read_bytes())
    assert compiled["source_count"] == 148 and compiled["manifest_sha256"] == digest(m)
    assert digest(compile_dir/"scripts"/compiled["changed_source"]) == compiled["source_sha256"]
    archive = verify_graph(args.graph,game)
    native = verify_native(HERE/f"build_{args.build:02}")
    owners = verify_saved_owners()
    out = HERE / f"evidence_{args.attempt:02}"
    out.mkdir(exist_ok=False)
    result = {"status":"WORKSPACE_CANDIDATE_CHECKED","graph":args.graph,"build":args.build,"compile":args.compile,
              "archive_changes":archive,"native":native,"script":compiled,"installed_files_checked":77,
              "saved_owners":owners,
              "live":False}
    (out/"assessment.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Verified phone dialogue ownership, retained native edges, hook signatures and RD10 stability.")


if __name__ == "__main__":
    main()
