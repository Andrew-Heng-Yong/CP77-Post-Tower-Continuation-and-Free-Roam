"""Pin the installed build and stage the Meet Kirk distance correction."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RD8 = HERE.parent / "resume_dispatcher_rd8_kirk_20261113_01"
OBSERVATION = HERE.parent / "resume_dispatcher_rd8_observe_20261113_01"
sys.path.insert(0, str(HERE.parent / "resume_dispatcher_rd6_batch50_20261113_01"))
from review_batch import plain, read, sha, write

SCRIPT = "r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds"
ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"
FACT = "PTFRS29_mq017_streetkid_ResumeOutsideBar"
DEPOT = r"towercontinued\sidejobs_s29\resume\mq017_meet_kirk\root.questphase"
PACKAGE = HERE / "candidate_01/package"


def baseline():
    path = RD8 / "deployment_01/installed_manifest_01.json"
    assert sha(path) == "8E8328DC9C2F259197446B94AC4809373EACD56BF2989D3F1343717DAB37EA13"
    manifest = read(path)
    assert manifest["core_epoch"] == "RD8_MEET_KIRK_RESUME"
    assert len(manifest["core_files"]) == 51 and len(manifest["required_files"]) == 26
    for row in manifest["core_files"] + manifest["required_files"]:
        file = Path(manifest["game_root"]) / row["path"]
        plain(file)
        assert sha(file) == row["sha256"] and file.stat().st_size == row["bytes"], file
    receipt = RD8 / "archive_02/readback.json"
    assert sha(receipt) == "F805E6500487FAC7FD28D80FE729684385D994F451F8B9640DC4BA2118436FD8"
    packed = read(receipt)
    assert packed["archive_sha256"] == manifest["archive_sha256"]
    members = {row["depot"]: row["sha256"] for row in packed["members"]}
    assert len(members) == manifest["archive_payloads"] == 1748
    return manifest, members


def replace(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new)


def main():
    installed, members = baseline()
    game = Path(installed["game_root"])
    world = read(OBSERVATION / "bar_anchor.json")
    sector, = world["sectors"]
    marker, = sector["markers"]
    assert marker["type"] == "worldEntityNode" and marker["streaming_distance"] == 10
    assert marker["node"]["debugName"]["$value"] == "mq017_distance_check"
    assert [round(value, 3) for value in marker["position"]] == [-1266.38, -990.218, 16.027]
    current = read(RD8 / "evidence_01/inputs.json")
    root = current["parts"]["root"]
    assert root["depot"] == DEPOT and root["raw_sha256"] == members[DEPOT]
    assert sha(root["raw"]) == members[DEPOT]
    observation = read(OBSERVATION / "saved_stage_and_handlers_02.json")
    sample, = [row for row in observation["saves"] if row["slot"] == "AutoSave-8"]
    assert {row["node"] for row in sample["owner"]["handlers"] if row["route"] == "1/40866/61002"} == {61013}
    source = (game / SCRIPT).read_text(encoding="utf-8-sig")
    x, y, z = (format(value, ".9g") for value in marker["position"])
    marker_position = f"new Vector4({x}, {y}, {z}, 1.0)"
    helper = f'''  private func SetKirkOutsideBar(outside: Bool) -> Void {{
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    let value = outside ? 1 : 0;
    if IsDefined(qs) && qs.GetFactStr("{FACT}") != value {{ qs.SetFactStr("{FACT}", value); }}
  }}
  private func PollKirkBarDistance() -> Void {{
    if this.Own(1, "ResumeClaimed") != 1 || this.Own(1, "Issued") != 0 || this.Own(1, "Fault") != 0 {{ return; }}
    let players = GameInstance.GetPlayerSystem(this.GetGameInstance());
    if !IsDefined(players) {{
      this.SetKirkOutsideBar(false);
      return;
    }}
    let player = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
    // Authored mq017_distance_check world position. The entity streams at 10 m.
    let anchor = {marker_position};
    let outside = IsDefined(player) && !player.IsReplacer() && !player.IsDead() &&
      Vector4.DistanceSquared(player.GetWorldPosition(), anchor) > 2500.0;
    this.SetKirkOutsideBar(outside);
  }}
'''
    source = replace(source, "  private func KirkEligible() -> Bool {", helper + "  private func KirkEligible() -> Bool {")
    source = replace(source, "    this.kirkPrevious = false;\n", "    this.kirkPrevious = false;\n    this.SetKirkOutsideBar(false);\n")
    source = replace(source, "    this.PollKirkResume(", "    this.PollKirkBarDistance();\n    this.PollKirkResume(")
    output = HERE / "evidence_01"
    output.mkdir()
    stage = PACKAGE / SCRIPT
    stage.parent.mkdir(parents=True)
    stage.write_text(source, encoding="utf-8", newline="\n")
    write(output / "inputs.json", {
        "game": str(game), "archive_sha256": installed["archive_sha256"], "archive_source": installed["archive_source"],
        "root": root, "fact": FACT, "members": members, "script_sha256": sha(stage),
        "bar_anchor_sha256": sha(OBSERVATION / "bar_anchor.json"), "save_observation_sha256": sha(OBSERVATION / "saved_stage_and_handlers_02.json"),
    })


if __name__ == "__main__":
    main()
