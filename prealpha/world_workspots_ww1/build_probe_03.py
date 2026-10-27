"""Build a standalone, additive WW1 diagnostic source tree beside JC1."""
from pathlib import Path
import hashlib
import json
import shutil

H = Path(__file__).resolve().parent
W = H.parent.parent
O = H / "probe_03"
assert not O.exists(), "Preserve prior prototype; use a successor name"
fragment = W / "diagnostics/world_npc_idle_20261026_02/ai/ww1_admission_fragment_03.reds.txt"
append = W / "diagnostics/world_npc_idle_20261026_02/ai/ww1_admission_append_03.reds.txt"
owner = H / "candidate_02/source/towercontinued/world_workspots_ww1/ce_pac_cvi_116_owner.questphase"
validation = H / "candidate_02/owner_validation_01.json"
assert json.loads(validation.read_text())["status"] == "STATIC_OWNER_PROTOTYPE_PASS_NOT_GAMEPLAY_PROOF"
source = fragment.read_text(encoding="utf-8")
assert source.count("this.Set(q,n\"PTFRWW1_CVI116_Request\",1);") == 1
source = source.replace("this.Set(q,n\"PTFRWW1_CVI116_Request\",1);",
                        "q.SetFact(n\"PTFRWW1_CVI116_Request\",1);")
script = '''module PTFR.WorldWorkspotsWW1

// Disposable exact-site Scav workspot probe. No generic NPC wrapper.
public class WorldWorkspotsWW1Driver extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private func OnAttach() -> Void {
    this.epoch += 1;
    this.running = true;
    this.WW1ResetSamples();
    this.Schedule(this.epoch);
  }
  private func OnDetach() -> Void {
    this.running = false;
    this.epoch += 1;
    ArrayClear(this.ww1Samples);
  }
  private func Schedule(expectedEpoch: Int32) -> Void {
    let delays = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delays) {
      delays.DelayCallback(WorldWorkspotsWW1Tick.Create(this, expectedEpoch), 0.5, false);
    }
  }
  public func Step(expectedEpoch: Int32) -> Void {
    if !this.running || expectedEpoch != this.epoch { return; }
    this.WW1Poll();
    this.Schedule(expectedEpoch);
  }
''' + source + '''
}

public class WorldWorkspotsWW1Tick extends DelayCallback {
  private let owner: wref<WorldWorkspotsWW1Driver>;
  private let epoch: Int32;
  public static func Create(owner: wref<WorldWorkspotsWW1Driver>, epoch: Int32) -> ref<WorldWorkspotsWW1Tick> {
    let callback = new WorldWorkspotsWW1Tick();
    callback.owner = owner;
    callback.epoch = epoch;
    return callback;
  }
  public func Call() -> Void {
    if IsDefined(this.owner) { this.owner.Step(this.epoch); }
  }
}
''' + append.read_text(encoding="utf-8").replace(
    "// Workspace-only helper types; merge into the existing RestorationBaseline file.",
    "// The sampled identity is transient and never stored in a save.")
assert "@wrapMethod" not in script and "ActivateCommunity" not in script
root = O / "source"
resource = root / "towercontinued/world_workspots_ww1/ce_pac_cvi_116_owner.questphase"
resource.parent.mkdir(parents=True)
shutil.copyfile(owner, resource)
reds = O / "package/r6/scripts/PTFR_WW1_Prototype/WW1Probe.reds"
reds.parent.mkdir(parents=True)
reds.write_text(script, encoding="utf-8", newline="\n")
assert b"\r" not in reds.read_bytes()
pins = {str(p.relative_to(W)): hashlib.sha256(p.read_bytes()).hexdigest().upper()
        for p in (fragment, append, owner, validation)}
data = {"status": "ADDITIVE_PROBE_SOURCE_NOT_PACKED_OR_INSTALLED",
        "original_owner_sha256": pins[str(owner.relative_to(W))],
        "script_sha256": hashlib.sha256(reds.read_bytes()).hexdigest().upper(),
        "resource_path": "towercontinued\\world_workspots_ww1\\ce_pac_cvi_116_owner.questphase",
        "script_path": "r6/scripts/PTFR_WW1_Prototype/WW1Probe.reds",
        "inputs": pins, "installed_writes": 0, "save_writes": 0}
(O / "source_manifest.json").write_text(json.dumps(data, indent=2)+"\n", encoding="utf-8")
print(json.dumps({k:v for k,v in data.items() if k != "inputs"},indent=2))
