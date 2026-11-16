"""Stage the retained-session hand model repair against the installed Core."""

import argparse
from difflib import unified_diff
import importlib.util
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
PRE = HERE.parent
PREVIOUS = 'QP2_TOWER_RECOVERY_PROFILE_HOLD'
EPOCH = 'QP2_TOWER_HAND_APPEARANCE'
BASELINE = PRE / 'tower_recovery_profile_hold_20261111_01/deployment_01/installed_manifest_01.json'
BASELINE_SHA = 'FE25F8986AE9B471E26ADC7C94183177FFE7672DFADBD42B83D13E51671EA499'
TEMPLATE = PRE / 'johnny_load_crash_20261111_01/deploy_core.ps1'
TEMPLATE_SHA = '8C94862FC57931194D6892B2B485C8E155F1CAC1903D1323DE6BB2E5F1E9D7C5'
TEMPLATE_MANIFEST_SHA = 'A18B646B307FE336F4D34BDFD01676322E0368C40204AA1C0CE92BF36FB79DB0'

spec = importlib.util.spec_from_file_location(
    'cyberware_build_helpers', PRE / 'cyberware_treatment_20261111_01/prepare.py'
)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
R1 = common.R1
CHANGES = {R1}
sha, read, write, one = common.digest, common.read_json, common.write_json, common.one


def edit(source):
    source = one(source, '  private let refundReadyReported: Bool;', '''  private let refundReadyReported: Bool;
  private let handRefreshAttempts: Int32;
  private let handRefreshRequested: Bool;''')
    source = one(source, '''    this.actor = null; this.fault = false; ArrayClear(this.attempts); this.Schedule();''', '''    this.actor = null; this.fault = false; ArrayClear(this.attempts);
    this.handRefreshAttempts = 0;
    this.Schedule();''')
    source = one(source, '''    this.refundReadyReported = false;
    this.Schedule();''', '''    this.refundReadyReported = false;
    this.handRefreshAttempts = 0;
    this.Schedule();''')
    source = one(source, '''    if this.actor != player { this.actor = player; this.warmup = 4; this.refundReadyReported = false; ArrayClear(this.attempts); }''', '''    if this.actor != player {
      this.actor = player;
      this.warmup = 4;
      this.refundReadyReported = false;
      this.handRefreshAttempts = 0;
      ArrayClear(this.attempts);
    }''')
    source = one(source, '''    if this.pending == 0 && this.treatmentHandoff >= 1 && data.PTFRCyberwareEffectsReady() &&''', '''    if this.pending == 0 { this.RefreshPostTowerHands(player, data); }
    if this.pending == 0 && this.treatmentHandoff >= 1 && data.PTFRCyberwareEffectsReady() &&''')
    source = one(source, '        this.treatmentHandoff = 1;', '''        this.treatmentHandoff = 1;
        this.handRefreshAttempts = 4;
        this.handRefreshRequested = false;''')
    source = one(source, '  private func ReportRefundReadiness() -> Void {', '''  private func RefreshPostTowerHands(player: ref<PlayerPuppet>, data: ref<EquipmentSystemPlayerData>) -> Void {
    if this.handRefreshAttempts == 0 { return; }
    let game = player.GetGame();
    // Let the native arrival finish before touching its live attachment. The
    // cover and refund ledger have their own readiness checks.
    if GetFact(game, n"PTFRPA2_Finished") != 1 ||
      GameInstance.GetPlayerSystem(game).GetLocalPlayerControlledGameObject() != player ||
      !CyberwarePolicy.ArmAppearanceSettled(player) || !CyberwarePolicy.Safe(player) { return; }

    this.handRefreshAttempts -= 1;
    let result = data.PTFRRefreshPostTowerHands(!this.handRefreshRequested);
    if Equals(result, PostTowerHandAttachment.Attached) {
      this.handRefreshAttempts = 0;
      ModLog(n"PTFR_Restrictions_R1", "Post-Tower stock hands attachment confirmed.");
      return;
    }
    if Equals(result, PostTowerHandAttachment.Requested) && !this.handRefreshRequested {
      this.handRefreshRequested = true;
      ModLog(n"PTFR_Restrictions_R1", "Post-Tower stock hands attachment refresh requested.");
    }
    if this.handRefreshAttempts == 0 {
      ModLog(n"PTFR_Restrictions_R1", "Post-Tower stock hands attachment could not be confirmed.");
    }
  }
  private func ReportRefundReadiness() -> Void {''')
    return one(source, '''public class ResetPostTowerArmAppearance extends ScriptableSystemRequest {''', '''public enum PostTowerHandAttachment {
  Waiting = 0,
  Requested = 1,
  Attached = 2
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRRefreshPostTowerHands(rebuild: Bool) -> PostTowerHandAttachment {
  if (this.GetEquipAreaIndex(gamedataEquipmentArea.ArmsCW) >= 0 &&
      this.GetNumberOfItemsInEquipmentArea(gamedataEquipmentArea.ArmsCW) > 0) ||
     (this.GetEquipAreaIndex(gamedataEquipmentArea.ArmsCWStyle) >= 0 &&
      this.GetNumberOfItemsInEquipmentArea(gamedataEquipmentArea.ArmsCWStyle) > 0) {
    return PostTowerHandAttachment.Waiting;
  }
  let player = this.m_owner as PlayerPuppet;
  let ts = GameInstance.GetTransactionSystem(player.GetGame());
  let slot = t"AttachmentSlots.RightArm";
  if ts.IsSlotSpawningAnyItem(player, slot) { return PostTowerHandAttachment.Waiting; }

  let fists = this.GetItemInEquipSlot(gamedataEquipmentArea.BaseFists, 0);
  if ItemID.GetTDBID(fists) != ItemID.GetTDBID(this.GetBaseFistsItemID()) || !ts.HasItem(player, fists) {
    this.HandleArmsCWUnequip(player);
    return PostTowerHandAttachment.Requested;
  }
  let record = TweakDBInterface.GetWeaponItemRecord(ItemID.GetTDBID(fists));
  if !IsDefined(record) || !IsDefined(record.HolsteredItem()) { return PostTowerHandAttachment.Waiting; }

  let stockHands = record.HolsteredItem().GetID();
  let equipped = this.GetItemInEquipSlot(gamedataEquipmentArea.RightArm, 0);
  let attachment = ts.GetItemInSlot(player, slot);
  if ItemID.GetTDBID(equipped) != stockHands || !ts.HasItem(player, equipped) ||
    (IsDefined(attachment) && !ts.HasItemInSlot(player, slot, equipped)) {
    EquipmentSystemPlayerData.UpdateArmSlot(player, fists, true);
    return PostTowerHandAttachment.Requested;
  }

  // A saved equipment slot can be correct while its live visual is stale.
  // Rebuild only the matching stock attachment and keep the owned instance.
  let attached = IsDefined(attachment);
  if attached {
    if !rebuild { return PostTowerHandAttachment.Attached; }
    if !ts.RemoveItemFromSlot(player, slot, true) { return PostTowerHandAttachment.Waiting; }
  } else if !ts.IsSlotEmpty(player, slot) {
    return PostTowerHandAttachment.Waiting;
  }
  if ts.AddItemToSlot(player, slot, equipped, true) || attached { return PostTowerHandAttachment.Requested; }
  return PostTowerHandAttachment.Waiting;
}

public class ResetPostTowerArmAppearance extends ScriptableSystemRequest {''')


def check_source(old, new):
    def block(source, start, end):
        return source.split(start, 1)[1].split(end, 1)[0]

    for start, end in (
        ('public static func CompletionBlocker(', 'public static func Area('),
        ('public static func Safe(', 'private func OnAttach('),
        ('public final func PTFRR2Ready(', 'public class CyberwareTreatmentRestore'),
        ('public final func PTFRR1Remove(', '@wrapMethod(EquipmentSystemPlayerData)'),
        ('public class ResetPostTowerArmAppearance', '@wrapMethod(CoolExitJumpEvents)'),
    ):
        assert block(old, start, end) == block(new, start, end), start
    assert [line for line in old.splitlines() if 'persistent let' in line] == [
        line for line in new.splitlines() if 'persistent let' in line
    ]
    step = block(new, 'private func OnCyberwareTreatmentStep(', 'private func RefreshPostTowerHands(')
    assert step.index('!CyberwarePolicy.Active(player)') < step.index('if this.fault') < step.index('this.RefreshPostTowerHands(')
    assert 'if this.pending == 0 { this.RefreshPostTowerHands(' in step
    assert step.index('if this.treatmentHandoff < 1') < step.index('this.handRefreshAttempts = 4;')
    refresh = block(new, 'private func RefreshPostTowerHands(', 'private func ReportRefundReadiness(')
    assert 'GetFact(game, n"PTFRPA2_Finished") != 1' in refresh
    assert '!CyberwarePolicy.ArmAppearanceSettled(player) || !CyberwarePolicy.Safe(player)' in refresh
    assert refresh.index('GetLocalPlayerControlledGameObject() != player') < refresh.index('data.PTFRRefreshPostTowerHands(')
    attachment = block(new, 'public final func PTFRRefreshPostTowerHands(', 'public class ResetPostTowerArmAppearance')
    assert attachment.index('IsSlotSpawningAnyItem') < attachment.index('HandleArmsCWUnequip')
    assert attachment.index('ts.HasItemInSlot') < attachment.index('ts.RemoveItemFromSlot') < attachment.index('ts.AddItemToSlot')
    assert 'RemoveItem(' not in attachment and 'GiveItem(' not in attachment
    return {
        'tower_and_refund_admission': 'MATCH',
        'persistent_fields_and_item_conservation': 'MATCH',
        'attachment_scope': 'FRESH_HANDOFF_AFTER_NATIVE_ARRIVAL; EXACT_STOCK_ATTACHMENT',
        'render_visibility': 'LIVE_ONLY',
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

    original = (game / R1).read_text(encoding='utf-8')
    edited = edit(original)
    checks = check_source(original, edited)
    package = candidate / 'package'
    for row in baseline['core_files']:
        relative = row['path']
        dest = package / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if relative == R1:
            dest.write_text(edited, encoding='utf-8', newline='\n')
            assert dest.read_text(encoding='utf-8') == edited
        else:
            shutil.copyfile(game / relative, dest)
            assert sha(dest) == row['sha256'], relative
    patch = unified_diff(original.splitlines(keepends=True), edited.splitlines(keepends=True), 'a/' + R1, 'b/' + R1)
    (candidate / 'source.patch').write_text(''.join(patch), encoding='utf-8', newline='\n')
    count = common.compile_overlay(game, package, compile_output)
    write(candidate / 'verification.json', {
        'baseline_sha256': BASELINE_SHA, 'script_hashes': {R1: sha(package / R1)},
        'registered_sources': count, 'checks': checks, 'compile': 'PASS', 'gameplay': 'UNVERIFIED',
    })
    print(f'Hand appearance repair compiled with all {count} registered sources.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=int)
    build(parser.parse_args().attempt)
