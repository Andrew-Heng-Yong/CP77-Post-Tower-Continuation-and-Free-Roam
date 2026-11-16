"""Bind the installed root and native content-lock condition to the playtest."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RD9 = HERE.parent / "resume_dispatcher_rd9_kirk_20261113_01"
OBSERVATION = HERE.parent / "resume_dispatcher_rd9_observe_20261113_01"
sys.path.insert(0, str(HERE.parent / "resume_dispatcher_rd6_batch50_20261113_01"))
from review_batch import pinned, read, readonly, sha, write

ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"
DEPOT = r"towercontinued\sidejobs_s29\resume\mq017_meet_kirk\root.questphase"
PACKAGE = HERE / "candidate_01/package"
BASELINE = RD9 / "deployment_01/installed_manifest_01.json"
STAGE = OBSERVATION / "saved_stage.json"


def baseline():
    installed = read(pinned(BASELINE.parent, (BASELINE.name, "B83EB24FD33BFB3F962FB25ADCE65A90969FA72D351D7C1539738676178B97B6")))
    assert installed["core_epoch"] == "RD9_MEET_KIRK_DISTANCE"
    assert len(installed["core_files"]) == 51 and len(installed["required_files"]) == 26
    game = Path(installed["game_root"])
    for row in installed["core_files"] + installed["required_files"]:
        assert pinned(game, (row["path"], row["sha256"])).stat().st_size == row["bytes"]
    packed = read(pinned(RD9 / "archive_01", ("readback.json", "CF979EAC2431DDDF71AD2F3976BED8FC374802368DEBCD52D3C4A72AC6E06672")))
    assert packed["archive_sha256"] == installed["archive_sha256"]
    members = {r["depot"]: r["sha256"] for r in packed["members"]}
    assert len(members) == installed["archive_payloads"] == 1748
    return installed, members


def main():
    installed, members = baseline()
    saved, = read(pinned(OBSERVATION, (STAGE.name, "9BAACD437D44F4687C8C755D6060AA6F492B6679ABC09FDDF7447804DC0EDB05")))["saves"]
    facts = saved["facts"]
    tag = "PTFRS29_mq017_streetkid_"
    assert saved["sha256"] == "2943EA7D98C0F657A5B4D526683A90D14C0BE5223C6CE52AD4874CD9C475D7B5"
    assert all(facts[tag + field] == 1 for field in ("ResumeClaimed", "ResumePhoneReleased", "ResumeOutsideBar"))
    assert facts[tag + "Issued"] is None and facts["holo_kirk_calls_v_end_count"] == 2
    assert {r["node"] for r in saved["owner"]["handlers"] if r["route"] == "1/40866/61002"} == {61013}
    assert {r["state_u32"] for r in saved["journals"] if not r["path"].endswith("/description")} == {4}
    root = read(RD9 / "graph_01/readback.json")
    assert root["sha256"] == members[DEPOT] and sha(root["path"]) == members[DEPOT]
    assert sha(root["path"] + ".json") == root["export_sha256"]
    with readonly("registry") as db:
        donor = dict(db.execute("select depot,sha256,export_path,export_sha256 from resources where rid=14498").fetchone())
    assert members[donor["depot"]] == donor["sha256"]
    assert sha(donor["export_path"]) == donor["export_sha256"]
    out = HERE / "evidence_01"
    out.mkdir()
    write(out / "inputs.json", {"game": installed["game_root"], "archive_sha256": installed["archive_sha256"],
        "archive_source": installed["archive_source"], "root": root | {"depot": DEPOT}, "donor": donor, "members": members,
        "playtest_sha256": sha(STAGE), "baseline_manifest_sha256": sha(BASELINE)})


if __name__ == "__main__":
    main()
