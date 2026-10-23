"""PA1 source contracts and state-machine models, not an engine playtest."""
import hashlib
import itertools
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research/pre_alpha_clean/arrival"
SOURCE = ROOT / "prealpha/arrival/scripts/PreAlphaArrivalPA1.reds"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class Arrival:
    """Executable model of the source's persisted stage and volatile observation state."""
    def __init__(self, stage=0):
        self.stage = stage
        self.epoch = 1
        self.running = True
        self.safe_ticks = self.landing = self.observed = self.calls = 0

    def restore(self):
        self.epoch += 1
        self.safe_ticks = self.landing = self.observed = 0

    def begin(self, authorized):
        if self.stage == 0 and authorized:
            self.stage = 1

    def tick(self, epoch=None, authorized=True, player=True, safe=True, facility=True, ui=True, menu=False, near=False):
        if not self.running or (epoch is not None and epoch != self.epoch):
            return
        if self.stage in (0, 3, 4):
            return
        if not authorized or not player:
            self.safe_ticks = self.landing = 0
            return
        if self.stage == 1:
            if not safe:
                self.safe_ticks = 0
                return
            self.safe_ticks += 1
            if self.safe_ticks < 3 or not facility:
                return
            self.stage = 2
            self.observed = self.landing = 0
            self.calls += 1
            return
        if not ui or menu:
            return
        self.observed += 1
        if near:
            self.landing = 1
        if self.landing == 1:
            self.stage = 3
            return
        if self.observed >= 60:
            self.stage = 4


def main():
    source = SOURCE.read_text(encoding="utf-8")
    target_path = OUT / "target.json"
    target = json.loads(target_path.read_text(encoding="utf-8"))
    for path, digest in target["source_pins"].items():
        assert sha(ROOT / path) == digest
    marker = target["marker"]
    assert marker["node_data"] == 12756
    assert marker["definition"]["$type"] == "worldStaticMarkerNode"
    assert marker["ref"] in source
    assert 'let path = "' + marker["ref"] + '";' in source
    assert "return CreateNodeRef(path);" in source
    codeware_path = Path("C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/red4ext/plugins/Codeware/Scripts/Codeware.Global.reds")
    codeware = codeware_path.read_text(encoding="utf-8")
    assert "public native func CreateNodeRef(value: script_ref<String>) -> NodeRef" in codeware
    assert marker["position"] == [-1432.13672, 1261.04565, 23.0654984]
    assert marker["orientation"] == {"$type": "Quaternion", "i": 0, "j": 0, "k": 0, "r": 1}
    assert source.count(".TeleportToNode(") == 1
    assert ".Teleport(" not in source
    assert source.index("this.stage = 2;") < source.index("facility.TeleportToNode(")
    for banned in ("SetFact(", "RequestAutoSave", "PerformFastTravel", "RemoveAllGameplayRestrictions", "AddItem(", "money", "apartment_owned"):
        assert banned not in source
    assert "entry.PostEndingAuthorized() && CyberwarePolicy.Completed" in source
    assert "!CyberwarePolicy.Safe(player) || GameInstance.GetPhoneManager(game).IsPhoneCallActive()" in source
    assert "if !IsDefined(ui) || ui.GetBool" in source
    assert "dx * dx + dy * dy <= 100.0 && AbsF(point.Z - target.Z) <= 2.0" in source
    assert "if this.landedTicks == 1" in source
    assert "this.observedTicks >= 60" in source
    assert "epoch != this.epoch" in source
    assert "private persistent let stage: Int32" in source
    assert "persistent let detail" not in source
    for stage in range(1, 5):
        assert "if this.stage == " + str(stage) + " { this.detail =" in source
    assert source.count("this.stage = 1;") == 1
    assert "this.stage = 0" not in source
    for api in ("Begin() -> String", "Completed() -> Bool", "Status() -> String"):
        assert api in source
    stock_path = ROOT / "research/finalboards_dismissal/decompiled/core/systems/fastTravelSystem.script"
    stock = stock_path.read_text(encoding="utf-8")
    assert "GetTeleportationFacility(this.GetGameInstance()).TeleportToNode(player, nodeData.GetMarkerRef());" in stock
    api_path = ROOT / "research/finalboards_dismissal/decompiled/orphans.script"
    assert "public final native func TeleportToNode(objectToTeleport: ref<GameObject>, nodeRef: NodeRef) -> Void;" in api_path.read_text(encoding="utf-8")
    entry_path = ROOT / "prealpha/entry/scripts/PreAlphaEntry.reds"
    entry = entry_path.read_text(encoding="utf-8")
    assert entry.index("if !arrival.Completed()") < entry.index("profile.FullNerf()")
    count = 0
    # Every Boolean admission condition, including a missing facility, is essential.
    for authorized, player, safe, facility in itertools.product((False, True), repeat=4):
        model = Arrival()
        model.begin(authorized)
        for _ in range(5):
            model.tick(authorized=authorized, player=player, safe=safe, facility=facility)
        assert model.calls == int(authorized and player and safe and facility)
        count += 1
    # Every saved phase restores exactly; completed/faulted/dispatched never issue again.
    for initial in range(5):
        for near, menu, ui in itertools.product((False, True), repeat=3):
            model = Arrival(initial)
            model.restore()
            for _ in range(100):
                model.begin(True)
                model.tick(near=near, menu=menu, ui=ui)
            assert model.calls <= int(initial <= 1)
            if initial == 3:
                assert model.stage == 3
            if initial == 4:
                assert model.stage == 4
            if initial == 2 and near and ui and not menu:
                assert model.stage == 3
            count += 1
    # Interrupted safety must restart the consecutive three-tick dispatch delay.
    model = Arrival(1)
    model.tick(); model.tick(); model.tick(safe=False); model.tick(); model.tick()
    assert model.calls == 0
    model.tick(); assert model.calls == 1 and model.stage == 2
    # Loading/missing UI and menus do not burn verification samples.
    for _ in range(100):
        model.tick(ui=False); model.tick(menu=True); model.tick(player=False)
    assert model.observed == 0 and model.stage == 2
    model.tick(near=True)
    assert model.stage == 3 and model.calls == 1
    count += 1
    # Stale callback invalidation and in-flight load cannot duplicate dispatch.
    for saved_stage in range(5):
        model = Arrival(saved_stage)
        epoch = model.epoch
        model.restore()
        for _ in range(100):
            model.tick(epoch=epoch, near=True)
        assert model.stage == saved_stage and model.calls == 0
        count += 1
    model = Arrival(1)
    for _ in range(3): model.tick()
    assert model.stage == 2 and model.calls == 1
    model.restore()
    for _ in range(60): model.tick()
    assert model.stage == 4 and model.calls == 1
    model.begin(True)
    for _ in range(100): model.tick(near=True)
    assert model.stage == 4 and model.calls == 1
    count += 1
    # Exhaustively varied safety histories, with a reload and repeated Begin calls.
    for history in itertools.product((False, True), repeat=10):
        model = Arrival()
        for step, safe in enumerate(history):
            model.begin(True)
            if step == 5: model.restore()
            model.tick(safe=safe, near=step >= 6)
            assert model.calls <= 1
        count += 1
    report = {
        "status": "PASS_SOURCE_AND_STATE_MODELS_LIVE_PENDING", "model_cases": count,
        "source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha(SOURCE),
        "target": str(target_path.relative_to(ROOT)), "target_sha256": sha(target_path),
        "api_sources": {str(p.relative_to(ROOT)): sha(p) for p in (stock_path, api_path, entry_path)},
        "installed_codeware_api": {"path": str(codeware_path), "sha256": sha(codeware_path), "declaration": "public native func CreateNodeRef(value: script_ref<String>) -> NodeRef"},
        "checks": ["exact authored H10 exterior marker and orientation", "single native node teleport callsite", "persistent dispatch-before-call; no implicit retry", "postcredits authorization and safe-source transition", "no global restriction/fact/entitlement/autosave mutations", "entry blocks profile/gigs until observed arrival", "bounded missing-arrival diagnostic; natural movement acknowledgment", "epoch/load/death/menu models"],
        "limits": ["Models validate intended state behavior, not engine serialization or native streaming.", "Parent must compile exact full package and read compiled bodies.", "Live physical street location, footing, transition, reload/death, phone and profile regression remain pending.", "Loading an earlier save predating arrival legitimately runs arrival for that earlier timeline; no cross-save global ledger.", "Dispatched but unconfirmed reload intentionally never teleports again; stage4 requires inspection, not automatic retry."],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tests.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["status"], count)


if __name__ == "__main__":
    main()
