"""Build a narrow successor for the profile setup stall after The Tower."""

import argparse
from difflib import unified_diff
import importlib.util
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
PRE = HERE.parent
PREVIOUS = 'QP2_TOWER_RECOVERY'
EPOCH = 'QP2_TOWER_RECOVERY_PROFILE_HOLD'
BASELINE = PRE / 'tower_recovery_20261111_01/deployment_02/installed_manifest_01.json'
BASELINE_SHA = 'A1865CF8A8B9DFBFDCDAD2339BB0400931B43031EB32A086AD0C52F24DA98354'
TEMPLATE = PRE / 'johnny_load_crash_20261111_01/deploy_core.ps1'
TEMPLATE_SHA = '8C94862FC57931194D6892B2B485C8E155F1CAC1903D1323DE6BB2E5F1E9D7C5'
TEMPLATE_MANIFEST_SHA = 'A18B646B307FE336F4D34BDFD01676322E0368C40204AA1C0CE92BF36FB79DB0'

# Import only the helpers; the earlier candidate builder is behind its main guard.
spec = importlib.util.spec_from_file_location(
    'cyberware_build_helpers', PRE / 'cyberware_treatment_20261111_01/prepare.py'
)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
R1, R3 = common.R1, common.R3
CHANGES = {R1, R3}
sha, read, write = common.digest, common.read_json, common.write_json
one, section = common.one, common.replace_section


def edit_r1(source):
    source = one(source, '  private let audit: String;', '''  private let audit: String;
  private let refundReadyReported: Bool;''')
    source = one(source, '''    this.warmup = 4; this.actor = null; this.fault = false; ArrayClear(this.attempts);
    this.Schedule();''', '''    this.warmup = 4; this.actor = null; this.fault = false; ArrayClear(this.attempts);
    this.refundReadyReported = false;
    this.Schedule();''')
    source = one(source, 'if this.actor != player { this.actor = player; this.warmup = 4; ArrayClear(this.attempts); }',
                 'if this.actor != player { this.actor = player; this.warmup = 4; this.refundReadyReported = false; ArrayClear(this.attempts); }')
    source = one(source, '''      this.detail = "Cyberware treatment settled";
      return;''', '''      this.ReportRefundReadiness();
      this.detail = "Cyberware treatment settled";
      return;''')
    source = one(source, '''      this.detail = effectsReady ? "Cyberware treatment settled" : "Waiting for isolated cyberware effects";
      return;''', '''      if data.PTFRCyberwareTreatmentReady() { this.ReportRefundReadiness(); }
      this.detail = effectsReady ? "Cyberware treatment settled" : data.PTFRCyberwareTreatmentStatus();
      return;''')
    source = one(source, '  public func Enable() -> String {', '''  private func ReportRefundReadiness() -> Void {
    if this.refundReadyReported { return; }
    this.refundReadyReported = true;
    ModLog(n"PTFR_Restrictions_R1", "Arms and Hands settled; per-item treatments processed; equipment ready for profile refunds.");
  }
  public func Enable() -> String {''')
    source = section(source, '  public func GetStatus() -> String {', '  public func GetAudit()', '''  public func GetStatus() -> String {
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) { return "Waiting for V"; }
    let data = EquipmentSystem.GetData(player);
    let pending = 0;
    if IsDefined(data) && CyberwarePolicy.Active(player) { pending = ArraySize(data.PTFRPendingCyberwareRemoval()); }
    return "Cyberware mode=" + ToString(this.mode) + " pending removal=" + ToString(pending) +
      " ready for refunds=" + ToString(IsDefined(data) && this.PTFRR2Ready(player)) + " | " + this.detail;
  }
''')
    source = one(source, '''      this.treatmentHandoff >= 1 && ArraySize(ids) == 0 && data.PTFRCyberwareEffectsReady() &&
      CyberwarePolicy.ArmAppearanceSettled(player) && !data.IsEquipPending();''', '''      this.treatmentHandoff >= 1 && ArraySize(ids) == 0 && data.PTFRCyberwareTreatmentReady() &&
      CyberwarePolicy.ArmAppearanceSettled(player) && !data.IsEquipPending();''')
    source = one(source, 'private let ptfrEffectsVerified: Bool;', '''private let ptfrEffectsVerified: Bool;

@addField(EquipmentSystemPlayerData)
private let ptfrTreatmentStatus: String;''')
    source = one(source, '''  ArrayClear(this.ptfrSkippedPackages);
  this.ptfrEffectsVerified = false;''', '''  ArrayClear(this.ptfrSkippedPackages);
  this.ptfrEffectsVerified = false;
  this.ptfrTreatmentStatus = "";''')
    source = one(source, '''  if !IsDefined(item) { return false; }
  let livePackages = this.PTFRLiveEquipPackages(item);''', '''  if !IsDefined(item) {
    this.PTFRNoteTreatmentStatus("Waiting for exact installed item " + CyberwareDiagnosticsCD1.Item(id));
    return false;
  }
  let livePackages = this.PTFRLiveEquipPackages(item);''')
    source = one(source, '''    ModLog(n"PTFR_Restrictions_R1", "Cannot isolate shared equip package for " + CyberwareDiagnosticsCD1.Item(id));''',
                 '''    this.PTFRNoteTreatmentStatus("Cannot isolate shared equip package for " + CyberwareDiagnosticsCD1.Item(id));''')
    source = one(source, '''      !GameInstance.GetStatsSystem(game).AddModifier(Cast<StatsObjectID>(this.m_owner.GetEntityID()), treatment.retained) {
      return false;
    }
  }
  if ArraySize(livePackages) > 0 {
    ArrayRemove(this.ptfrSkippedPackages, id);
    this.RemoveEquipGLPs(id);
  }''', '''      !GameInstance.GetStatsSystem(game).AddModifier(Cast<StatsObjectID>(this.m_owner.GetEntityID()), treatment.retained) {
      this.PTFRNoteTreatmentStatus("Retained modifier admission pending for " + CyberwareDiagnosticsCD1.Item(id));
      return false;
    }
  }
  // Vanilla equipment applies each record and part GLP with V as both
  // target and instigator. Retire those references through the matching
  // instigator overload, leaving other instigators alone.
  let glps = GameInstance.GetGameplayLogicPackageSystem(game);
  let i = 0;
  while i < ArraySize(livePackages) {
    glps.RemovePackageOfInstigator(this.m_owner, this.m_owner, livePackages[i]);
    i += 1;
  }''')
    source = one(source, '''public final func PTFRCyberwareEffectsReady() -> Bool {
  if !this.ptfrEffectsVerified { return false; }
  let ids = this.PTFRInstalledCyberware();''', '''public final func PTFRCyberwareEffectsReady() -> Bool {
  return this.ptfrEffectsVerified && this.PTFRCyberwareTreatmentReady();
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRCyberwareTreatmentReady() -> Bool {
  // The refund ledger depends on completed per-instance treatment and
  // stable slots. A package ID cannot identify a residual contribution.
  let ids = this.PTFRInstalledCyberware();''')
    source = one(source, '''  this.ptfrEffectsVerified = ok && this.PTFRCyberwarePackagesCleared(ids);
  return this.ptfrEffectsVerified;''', '''  if !ok { this.ptfrEffectsVerified = false; return false; }
  let residual = this.PTFRResidualCyberwarePackage(ids);
  this.ptfrEffectsVerified = StrLen(residual) == 0;
  this.PTFRNoteTreatmentStatus(this.ptfrEffectsVerified ? "Cyberware treatment settled" : residual);
  return this.ptfrEffectsVerified;''')
    source = one(source, '''private final func PTFRCyberwarePackagesCleared(ids: array<ItemID>) -> Bool {
  let ts = GameInstance.GetTransactionSystem(this.m_owner.GetGame());
  let i = 0;
  while i < ArraySize(ids) {
    if CyberwarePolicy.Suppresses(this.m_owner, ids[i]) {
      let item = ts.GetItemData(this.m_owner, ids[i]);
      if !IsDefined(item) || ArraySize(this.PTFRLiveEquipPackages(item)) > 0 { return false; }
    }
    i += 1;
  }
  return true;
}''', '''private final func PTFRResidualCyberwarePackage(ids: array<ItemID>) -> String {
  let ts = GameInstance.GetTransactionSystem(this.m_owner.GetGame());
  let i = 0;
  while i < ArraySize(ids) {
    if CyberwarePolicy.Suppresses(this.m_owner, ids[i]) {
      let item = ts.GetItemData(this.m_owner, ids[i]);
      if !IsDefined(item) { return "Waiting for exact installed item " + CyberwareDiagnosticsCD1.Item(ids[i]); }
      let packages = this.PTFRLiveEquipPackages(item);
      if ArraySize(packages) > 0 {
        return "Native package still listed for " + TDBID.ToStringDEBUG(ItemID.GetTDBID(ids[i])) +
          ": " + TDBID.ToStringDEBUG(packages[0]);
      }
    }
    i += 1;
  }
  return "";
}

@addMethod(EquipmentSystemPlayerData)
private final func PTFRNoteTreatmentStatus(status: String) -> Void {
  if Equals(this.ptfrTreatmentStatus, status) { return; }
  this.ptfrTreatmentStatus = status;
  ModLog(n"PTFR_Restrictions_R1", status);
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRCyberwareTreatmentStatus() -> String {
  return this.ptfrTreatmentStatus;
}''')
    return source


def edit_r3(source):
    return one(source, '''  public func LC1Progress() -> String {
    let progress = "Other ranks: " + ToString(this.refunded) + " / " + ToString(this.starting);
    return StrBeginsWith(this.detail, "Refund waiting") ? progress + "\\n" + this.detail : progress;
  }''', '''  public func LC1Progress() -> String {
    let progress = "Other ranks: " + ToString(this.refunded) + " / " + ToString(this.starting);
    let game = this.GetGameInstance();
    let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let chrome = CyberwarePolicy.Get(game);
    if IsDefined(player) && IsDefined(chrome) && !chrome.PTFRR2Ready(player) {
      return progress + "\\n" + chrome.GetStatus();
    }
    if StrBeginsWith(this.detail, "Refund waiting") || StrBeginsWith(this.detail, "Waiting for vitals") ||
      StrBeginsWith(this.detail, "Waiting:") {
      return progress + "\\n" + this.detail;
    }
    return progress;
  }''')


def check_source(old_r1, r1, old_r3, r3):
    def extract(text, start, end):
        return text.split(start, 1)[1].split(end, 1)[0]

    for start, end in (
        ('public static func CompletionBlocker(', 'public static func Area('),
        ('public static func InMenu(', 'private func OnAttach('),
        ('public final func PTFRR1Remove(', '@wrapMethod(EquipmentSystemPlayerData)'),
    ):
        assert extract(old_r1, start, end) == extract(r1, start, end), start
    assert old_r1.count('this.treatmentHandoff = 1;') == r1.count('this.treatmentHandoff = 1;') == 1
    ready = extract(r1, 'public final func PTFRR2Ready(', '\n}\npublic class CyberwareTreatmentRestore')
    for check in ('!this.fault', 'this.warmup == 0', 'this.actor == player', 'CyberwarePolicy.Active(player)',
                  'this.treatmentHandoff >= 1', 'ArraySize(ids) == 0', 'data.PTFRCyberwareTreatmentReady()',
                  'CyberwarePolicy.ArmAppearanceSettled(player)', '!data.IsEquipPending()'):
        assert check in ready, check
    assert 'PTFRCyberwareEffectsReady()' not in ready
    treat = extract(r1, 'private final func PTFRApplyTreatment(', 'public final func PTFRCyberwareEffectsReady(')
    assert treat.index('PTFRFindTreatment(id) >= 0') < treat.index('RemovePackageOfInstigator(') < treat.index('ArrayPush(this.ptfrTreated')
    assert treat.index('PTFRPackageOwnershipSafe') < treat.index('RemovePackageOfInstigator(')
    start = '  public func LC1Progress() -> String {'
    end = '  public func PTFRPAConfigured() -> Bool {'
    assert old_r3.split(start, 1)[0] == r3.split(start, 1)[0]
    assert old_r3.split(end, 1)[1] == r3.split(end, 1)[1]
    return {
        'tower_and_native_safety_gates': 'MATCH',
        'per_instance_conservation_and_tattoo_receipt': 'MATCH',
        'profile_mutation_ledger_and_recovery': 'MATCH',
        'refund_admission': 'OWNED_TREATMENT_REQUIRED; RESIDUAL_ID_READBACK_REPORTED',
        'live': 'UNVERIFIED',
    }


def build(attempt):
    candidate = HERE / f'candidate_{attempt:02}'
    compile_output = HERE / f'compile_{attempt:02}'
    assert not candidate.exists() and not compile_output.exists()
    assert sha(BASELINE) == BASELINE_SHA
    baseline = read(BASELINE)
    assert baseline['core_epoch'] == PREVIOUS
    game = Path(baseline['game_root'])
    assert len(baseline['core_files']) == 51 and len(baseline['required_files']) == 26
    for row in baseline['core_files'] + baseline['required_files']:
        path = game / row['path']
        common.plain(path, game)
        assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], path
    originals = {p: (game / p).read_text(encoding='utf-8') for p in CHANGES}
    edited = {R1: edit_r1(originals[R1]), R3: edit_r3(originals[R3])}
    checks = check_source(originals[R1], edited[R1], originals[R3], edited[R3])
    package = candidate / 'package'
    patches = []
    hashes = {}
    for row in baseline['core_files']:
        relative = row['path']
        dest = package / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if relative in CHANGES:
            dest.write_text(edited[relative], encoding='utf-8', newline='\n')
            assert dest.read_text(encoding='utf-8') == edited[relative]
            patches.extend(unified_diff(originals[relative].splitlines(keepends=True),
                                        edited[relative].splitlines(keepends=True),
                                        'a/' + relative, 'b/' + relative))
            hashes[relative] = sha(dest)
        else:
            shutil.copyfile(game / relative, dest)
            assert sha(dest) == row['sha256'], relative
    (candidate / 'source.patch').write_text(''.join(patches), encoding='utf-8', newline='\n')
    count = common.compile_overlay(game, package, compile_output)
    write(candidate / 'verification.json', {
        'baseline_sha256': BASELINE_SHA, 'script_hashes': hashes, 'registered_sources': count,
        'checks': checks, 'compile': 'PASS', 'gameplay': 'UNVERIFIED',
    })
    print(f'Profile setup repair compiled with all {count} registered sources.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=int)
    build(parser.parse_args().attempt)
