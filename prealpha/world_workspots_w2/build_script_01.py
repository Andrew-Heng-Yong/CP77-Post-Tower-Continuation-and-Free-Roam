"""Generate one existing-module REDscript successor for ambient prefab admission."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
MANIFEST = HERE / "manifest_02.json"
ORIGINAL = GAME / "r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds"
OUT = HERE / "candidate_01/script_source/PTFR_RestorationBaseline.reds"
PROOF = HERE / "candidate_01/script_source/build_01.json"
assert not OUT.exists() and not PROOF.exists(), "Preserve prior script build"
m = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
assert m["status"] == "EXACT_NATIVE_IDENTITY_CANDIDATES_NOT_DEPLOYABLE"
assert m["owner_count"] == 206 and m["spawner_count"] == 212
old = ORIGINAL.read_text(encoding="utf-8-sig")
assert old.startswith("module PTFR.RestorationBaseline\n")
needle = "    this.Schedule(this.epoch, 1.0);\n"
assert old.count(needle) == 1
old = old.replace(needle, needle +
    '    let ambientW2 = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.RestorationBaseline.AmbientWorkspotsW2Driver") as AmbientWorkspotsW2Driver;\n')
groups = []
for group in m["groups"]:
    ident = group["id"]
    prefix = group["prefix"]
    groups.extend([f"    g = new AmbientWorkspotGroupW2(); g.id = {ident}; g.prefix = \"{prefix}\";"])
    assert len(group["spawner_hashes"]) == len(group["community_refs"])
    for value, ref in zip(group["spawner_hashes"], group["community_refs"]):
        assert value.isdecimal() and '"' not in ref and "\\" not in ref
        groups.append(f'    ArrayPush(g.spawners, EntityID.FromHash({value}ul)); ArrayPush(g.communities, ToNodeRef("{ref}"));')
    groups.append("    ArrayPush(this.groups, g);")
rows = "\n".join(groups)
extension = r'''

// W2: restore only exact native prefab support while its original community
// has a living streamed NPC. All fields below are transient; quest facts and
// the private phase record the one-time owner claim.
public class AmbientWorkspotGroupW2 extends IScriptable {
  public let id: Int32;
  public let prefix: String;
  public let spawners: array<EntityID>;
  public let communities: array<NodeRef>;
}

public class AmbientWorkspotSampleW2 extends IScriptable {
  public let actor: wref<NPCPuppet>;
  public let groupIndex: Int32;
  public let refIndex: Int32;
  public let entry: CName;
  public let settled: Int32;
}

public class AmbientWorkspotsW2Driver extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let scanTicks: Int32;
  private let stage: String;
  private let groups: array<ref<AmbientWorkspotGroupW2>>;
  private let samples: array<ref<AmbientWorkspotSampleW2>>;

  private func OnAttach() -> Void {
    this.epoch += 1; this.running = true;
    this.scanTicks = 0; ArrayClear(this.samples);
    this.LoadGroups();
    this.Report("attached groups=" + ToString(ArraySize(this.groups)));
    this.Schedule(this.epoch);
  }
  private func OnDetach() -> Void {
    this.running = false; this.epoch += 1;
    ArrayClear(this.samples); ArrayClear(this.groups);
  }
  private func Report(s: String) -> Void {
    if NotEquals(this.stage,s) { this.stage = s; ModLog(n"PTFR_W2",s); }
  }
  private func Schedule(expected: Int32) -> Void {
    let delays = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delays) { delays.DelayCallback(AmbientWorkspotsW2Tick.Create(this,expected),0.5,false); }
  }
  public func Step(expected: Int32) -> Void {
    if !this.running || expected != this.epoch { return; }
    this.Poll(); this.Schedule(expected);
  }
  private func LoadGroups() -> Void {
    ArrayClear(this.groups);
    let g: ref<AmbientWorkspotGroupW2>;
__GROUPS__
  }
  private func Safe(game: GameInstance, q: ref<QuestsSystem>, player: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(q) || !IsDefined(player) || !player.IsAttached() { return false; }
    if q.GetFact(n"PostTowerFreeRoamActive") != 1 || q.GetFact(n"PTFRP0_DR13") != 1 ||
       q.GetFact(n"q307_active") != 0 || q.GetFact(n"q307_done") != 1 ||
       q.GetFact(n"q307_finished") != 1 || q.GetFact(n"q307_2079") != 1 ||
       q.GetFact(n"q307_main_game_killed") != 1 || q.GetFact(n"q307_ep1_killed") != 1 ||
       q.GetFact(n"q305_johnny_scene_active") != 0 || q.GetFact(n"q115_point_of_no_return") != 0 ||
       q.GetFact(n"q000_done") != 1 || q.GetFact(n"PTFRBASE_Suspended") != 0 { return false; }
    let world = GameInstance.GetWorldStateSystem();
    let scenes = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let spots = GameInstance.GetWorkspotSystem(game);
    let time = GameInstance.GetTimeSystem(game);
    if !IsDefined(world) || !world.IsReady() || !IsDefined(scenes) || !IsDefined(spots) || !IsDefined(time) { return false; }
    if time.IsPausedState() || player.IsInCombat() || scenes.IsEntityInDialogue(player.GetEntityID()) || spots.IsActorInWorkspot(player) { return false; }
    let mounted = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(player);
    if EntityID.IsDefined(mounted.parentId) { return false; }
    let board = player.GetPlayerStateMachineBlackboard();
    if !IsDefined(board) || board.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel) != 1 ||
       board.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier) != 1 { return false; }
    if GameInstance.GetQuestsContentSystem(game).IsTokensActivationBlocked() { return false; }
    let locks: array<gameSaveLock>;
    return !GameInstance.IsSavingLocked(game,locks);
  }
  private func Open(q: ref<QuestsSystem>, index: Int32) -> Bool {
    let p = this.groups[index].prefix;
    return q.GetFact(StringToName(p+"Ready")) == 1 &&
      q.GetFact(StringToName(p+"Request")) == 0 &&
      q.GetFact(StringToName(p+"Claimed")) == 0 &&
      q.GetFact(StringToName(p+"Entered")) == 0 &&
      q.GetFact(StringToName(p+"Hold")) == 0;
  }
  private func Observe(q: ref<QuestsSystem>, actor: wref<NPCPuppet>) -> Void {
    if !IsDefined(actor) || !actor.IsAttached() { return; }
    let game = this.GetGameInstance();
    let ps = GameInstance.GetPersistencySystem(game);
    if !IsDefined(ps) { return; }
    let pid = CreatePersistentID(actor.GetEntityID(),gameEntityStubComponentPS.GetPSComponentName());
    let stub = ps.GetConstAccessToPSObject(pid,n"gameEntityStubComponentPS") as gameEntityStubComponentPS;
    if !IsDefined(stub) { return; }
    let i = 0;
    while i < ArraySize(this.groups) {
      if this.Open(q,i) {
        let j = 0;
        while j < ArraySize(this.groups[i].spawners) {
          if stub.GetSpawnerID() == this.groups[i].spawners[j] {
            let k = 0;
            while k < ArraySize(this.samples) {
              if this.samples[k].actor == actor { return; }
              k += 1;
            }
            let sample = new AmbientWorkspotSampleW2();
            sample.actor = actor; sample.groupIndex = i; sample.refIndex = j;
            sample.entry = stub.GetOwnerCommunityEntryName(); sample.settled = 0;
            ArrayPush(this.samples,sample); return;
          }
          j += 1;
        }
      }
      i += 1;
    }
  }
  private func Proven(game: GameInstance, q: ref<QuestsSystem>, s: ref<AmbientWorkspotSampleW2>) -> Bool {
    if !this.Open(q,s.groupIndex) { return false; }
    let actor = s.actor;
    if !IsDefined(actor) || !actor.IsAttached() || actor.IsDead() || actor.IsIncapacitated() ||
       ScriptedPuppet.IsDefeated(actor) || !actor.IsOnAutonomousAI() || NPCPuppet.IsInCombat(actor) { return false; }
    if GameInstance.FindEntityByID(game,actor.GetEntityID()) != actor { return false; }
    let scenes = GameInstance.GetSceneSystem(game).GetScriptInterface();
    if !IsDefined(scenes) || scenes.IsEntityInScene(actor.GetEntityID()) { return false; }
    let ps = GameInstance.GetPersistencySystem(game);
    if !IsDefined(ps) { return false; }
    let pid = CreatePersistentID(actor.GetEntityID(),gameEntityStubComponentPS.GetPSComponentName());
    let stub = ps.GetConstAccessToPSObject(pid,n"gameEntityStubComponentPS") as gameEntityStubComponentPS;
    let group = this.groups[s.groupIndex];
    if !IsDefined(stub) || stub.GetSpawnerID() != group.spawners[s.refIndex] ||
       NotEquals(stub.GetOwnerCommunityEntryName(),s.entry) { return false; }
    let community = GameInstance.GetWorldStateSystem().GetCommunity(group.communities[s.refIndex]);
    if !IsDefined(community) { return false; }
    let entries = community.GetEntries();
    let i = 0;
    while i < ArraySize(entries) {
      if IsDefined(entries[i]) && Equals(entries[i].GetName(),s.entry) { return entries[i].IsActive(); }
      i += 1;
    }
    return false;
  }
  private func Poll() -> Void {
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    let players = GameInstance.GetPlayerSystem(game);
    if !IsDefined(q) || !IsDefined(players) { ArrayClear(this.samples); return; }
    let player = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !this.Safe(game,q,player) { this.scanTicks = 0; ArrayClear(this.samples); return; }
    if this.scanTicks <= 0 {
      let nearby = player.GetNPCsAroundObject(80.0);
      let k = 0;
      while k < ArraySize(nearby) { this.Observe(q,nearby[k]); k += 1; }
      this.scanTicks = 10;
    } else { this.scanTicks -= 1; }
    let i = ArraySize(this.samples)-1;
    while i >= 0 {
      let sample = this.samples[i];
      if !IsDefined(sample.actor) || !sample.actor.IsAttached() || sample.actor.IsDead() || sample.actor.IsIncapacitated() {
        ArrayErase(this.samples,i);
      } else {
        if this.Proven(game,q,sample) { sample.settled += 1; } else { sample.settled = 0; }
        if sample.settled >= 2 {
          let group = this.groups[sample.groupIndex];
          q.SetFact(StringToName(group.prefix+"Request"),1);
          this.Report("requested exact prefab id="+ToString(group.id));
          ArrayClear(this.samples); return;
        }
      }
      i -= 1;
    }
  }
}

public class AmbientWorkspotsW2Tick extends DelayCallback {
  private let owner: wref<AmbientWorkspotsW2Driver>;
  private let epoch: Int32;
  public static func Create(owner: wref<AmbientWorkspotsW2Driver>, epoch: Int32) -> ref<AmbientWorkspotsW2Tick> {
    let c = new AmbientWorkspotsW2Tick(); c.owner = owner; c.epoch = epoch; return c;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Step(this.epoch); } }
}
'''.replace("__GROUPS__", rows)
assert extension.count("ArrayPush(this.groups, g);") == 206
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(old.rstrip() + extension, encoding="utf-8", newline="\n")
record = {"status":"EXISTING_MODULE_SCRIPT_CANDIDATE_NOT_COMPILED_OR_INSTALLED",
          "manifest_sha256":sha256(MANIFEST.read_bytes()).hexdigest().upper(),
          "original_sha256":sha256(ORIGINAL.read_bytes()).hexdigest().upper(),
          "candidate_sha256":sha256(OUT.read_bytes()).hexdigest().upper(),
          "groups":206,"spawners":212,"game_writes":0,"save_writes":0}
PROOF.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
print(json.dumps(record,indent=2))
