"""Stage one save-compatible world cleanup admission change; never write the game."""

from pathlib import Path
import hashlib
import json
import shutil
import stat

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
BASE = ROOT / "prealpha/body_view_revert_bv1_20261116_01/candidate_01/core_manifest_01.json"
BASE_SHA = "8A6182A3B104AC3DE6D835EF2351D04EF019EA0544A652F8ED546F06FB11003C"
SCRIPT = "r6/scripts/PTFR_Consolidated/PTFR_MistyViktorAuto.reds"
SCRIPT_SHA = "F4D5050730FF3255F3B963B4499D0D33080CFE428F0B4E4A888C1F317A6BDFBA"
OUT = HERE / "candidate_01"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def plain(path: Path) -> None:
    for part in (path, *path.parents):
        if part.exists() and part.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise RuntimeError(f"Reparse path refused: {part}")


def check_rows(rows: list[dict]) -> None:
    for row in rows:
        path = GAME / row["path"]
        plain(path)
        if not path.is_file() or path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            raise RuntimeError(f"Installed baseline drift: {row['path']}")


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError(f"Source anchor count {source.count(old)}: {old[:60]}")
    return source.replace(old, new, 1)


def stage_script(raw: bytes) -> bytes:
    bom = raw.startswith(b"\xef\xbb\xbf")
    crlf = b"\r\n" in raw
    source = raw.decode("utf-8-sig").replace("\r\n", "\n")
    source = replace_once(
        source,
        '''    let q = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if IsDefined(q) && q.GetFact(n"PTFRWO1_CleanupPermit") != 0 {
      q.SetFact(n"PTFRWO1_CleanupPermit", 0);
    }
    this.Schedule(this.epoch, 1.0);''',
        '''    let q = GameInstance.GetQuestsSystem(this.GetGameInstance());
    let players = GameInstance.GetPlayerSystem(this.GetGameInstance());
    if IsDefined(q) && q.GetFact(n"PTFRWO1_CleanupPermit") != 0 {
      q.SetFact(n"PTFRWO1_CleanupPermit", 0);
    }
    // A qualified saved free-roam load may already be beside the street.
    if IsDefined(q) && IsDefined(players) {
      this.RefreshStreetCleanupPermit(q, players.GetLocalPlayerMainGameObject() as PlayerPuppet);
    }
    this.Schedule(this.epoch, 1.0);''',
    )
    source = replace_once(
        source,
        '''  // The native ending set is displaced from the ordinary streets. Its authored
  // cleanup runs only after genuine completion and while the player is away.
  private func RefreshStreetCleanupPermit(q: ref<QuestsSystem>, p: ref<PlayerPuppet>) -> Void {
    let permit = 0;
    if this.Completed(q) && this.Safe(p) &&
      q.GetFact(n"PTFRMV_Applied") == 1 &&
      q.GetFact(n"PTFRWO1_CleanupRegistered") == 1 &&
      q.GetFact(n"PTFRWO1_CleanupDone") == 0 {
      let pos = p.GetWorldPosition();
      let dx = pos.X + 1475.0;
      let dy = pos.Y - 1080.0;
      if dx * dx + dy * dy > 250000.0 { permit = 1; }
    }
    if q.GetFact(n"PTFRWO1_CleanupPermit") != permit {
      q.SetFact(n"PTFRWO1_CleanupPermit", permit);
    }
  }''',
        '''  // Keep the street owner separate from the clinic's 80-metre admission.
  // The native final state also restores the ordinary solid street variant.
  private func SafeStreet(p: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(p) || !p.IsAttached() || p.IsInCombat() { return false; }
    let game = this.GetGameInstance();
    let scenesSystem = GameInstance.GetSceneSystem(game);
    let workspots = GameInstance.GetWorkspotSystem(game);
    let mountingFacility = GameInstance.GetMountingFacility(game);
    let content = GameInstance.GetQuestsContentSystem(game);
    if !IsDefined(scenesSystem) || !IsDefined(workspots) ||
      !IsDefined(mountingFacility) || !IsDefined(content) { return false; }
    let scenes = scenesSystem.GetScriptInterface();
    if !IsDefined(scenes) { return false; }
    if scenes.IsEntityInScene(p.GetEntityID()) || workspots.IsActorInWorkspot(p) { return false; }
    let mounting = mountingFacility.GetMountingInfoSingleWithObjects(p);
    if EntityID.IsDefined(mounting.parentId) || content.IsTokensActivationBlocked() { return false; }
    let locks: array<gameSaveLock>;
    return !GameInstance.IsSavingLocked(game, locks);
  }
  // A fresh post-Tower load must release the final-scene street even nearby.
  private func RefreshStreetCleanupPermit(q: ref<QuestsSystem>, p: ref<PlayerPuppet>) -> Void {
    let permit = 0;
    if this.Completed(q) && this.SafeStreet(p) &&
      q.GetFact(n"PTFRMV_Applied") == 1 &&
      q.GetFact(n"PTFRWO1_CleanupRegistered") == 1 &&
      q.GetFact(n"PTFRWO1_CleanupDone") == 0 {
      permit = 1;
    }
    if q.GetFact(n"PTFRWO1_CleanupPermit") != permit {
      q.SetFact(n"PTFRWO1_CleanupPermit", permit);
    }
  }''',
    )
    result = source.replace("\n", "\r\n") if crlf else source
    return (b"\xef\xbb\xbf" if bom else b"") + result.encode("utf-8")


def main() -> None:
    plain(BASE)
    if sha(BASE) != BASE_SHA:
        raise RuntimeError("Predecessor manifest drift")
    base = json.loads(BASE.read_text(encoding="utf-8-sig"))
    assert base["status"] == "STAGED_OFFLINE" and len(base["core_files"]) == 51
    check_rows(base["core_files"] + base["required_files"])
    source = GAME / SCRIPT
    assert sha(source) == SCRIPT_SHA
    plain(OUT)
    OUT.mkdir(exist_ok=False)
    changed = stage_script(source.read_bytes())
    candidate = OUT / "package" / SCRIPT
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(changed)
    assert sha(candidate) != SCRIPT_SHA
    rows = []
    for row in base["core_files"]:
        path = OUT / "package" / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if row["path"] != SCRIPT:
            shutil.copyfile(GAME / row["path"], path)
        rows.append({"path": row["path"], "bytes": path.stat().st_size, "sha256": sha(path)})
    check_rows(base["core_files"] + base["required_files"])
    assert [a["path"] for a, b in zip(base["core_files"], rows) if a != b] == [SCRIPT]
    proof = {"status": "STAGED_OFFLINE", "baseline_manifest_sha256": BASE_SHA,
             "changed_paths": [SCRIPT], "core_files": rows, "required_files": base["required_files"],
             "script_before": SCRIPT_SHA, "script_after": sha(candidate), "game_writes": 0, "save_writes": 0}
    with (OUT / "core_manifest_01.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(proof, stream, indent=2)
        stream.write("\n")
    print(f"STAGED: 51 exact Core paths, one changed script {sha(candidate)}")


if __name__ == "__main__":
    main()
