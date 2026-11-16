"""Stage and compile the post-Tower cyberware successor against installed inputs."""

from difflib import unified_diff
from hashlib import sha256
from pathlib import Path
import argparse
import json
import shutil
import stat
import subprocess


HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / 'johnny_load_crash_20261111_01/deployment_01/installed_manifest_01.json'
BASELINE_HASH = 'EE5CEF96EE36BB8C876A46BA9FFE179B235592138059C75FC45BB7636B880878'
R1 = 'r6/scripts/PTFR_Consolidated/PTFR_RestrictionsR1.reds'
R3 = 'r6/scripts/PTFR_Consolidated/PTFR_RestrictionsR3.reds'


def digest(path):
    with path.open('rb') as stream:
        return sha256_stream(stream)


def sha256_stream(stream):
    result = sha256()
    while block := stream.read(1024 * 1024):
        result.update(block)
    return result.hexdigest().upper()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def one(source, before, after):
    assert source.count(before) == 1, before
    return source.replace(before, after, 1)


def replace_section(source, start, end, body):
    first = source.index(start)
    last = source.index(end, first)
    return source[:first] + body + source[last:]


def edit_r1(source, model_records):
    source = one(source, 'import PTFR.RestrictionsR3.ProfileDefinition\n', '')
    source = one(source, 'Equals(area, gamedataEquipmentArea.ArmsCW) || Equals(area, gamedataEquipmentArea.EyesCW)',
                 'Equals(area, gamedataEquipmentArea.ArmsCW) || Equals(area, gamedataEquipmentArea.ArmsCWStyle) || Equals(area, gamedataEquipmentArea.EyesCW)')
    source = one(source, '  private let running: Bool;', '''  // Save-local receipt for the first Arms and Hands removal pass.
  private persistent let treatmentHandoff: Int32;
  private let running: Bool;''')
    source = replace_section(source, '  public static func Approved(', '  public static func DeniedAction(', '''  public static func Suppresses(owner: ref<GameObject>, id: ItemID) -> Bool {
    if !CyberwarePolicy.Active(owner) { return false; }
    let level = CyberwareTreatmentSettings.Level(id);
    return Equals(level, CyberwareTreatment.Disabled) || Equals(level, CyberwareTreatment.Limited);
  }
  public static func MustUnequip(owner: ref<GameObject>, id: ItemID) -> Bool {
    let level = CyberwareTreatmentSettings.Level(id);
    return Equals(level, CyberwareTreatment.Remove) ||
      (Equals(level, CyberwareTreatment.Limited) && CyberwareTreatmentSettings.Tattoo(ItemID.GetTDBID(id)) &&
        CyberwarePolicy.Get(owner.GetGame()).treatmentHandoff < 1);
  }
  public static func Denied(owner: ref<GameObject>, id: ItemID) -> Bool {
    return CyberwarePolicy.Active(owner) &&
      (Equals(CyberwareTreatmentSettings.Level(id), CyberwareTreatment.Disabled) || CyberwarePolicy.MustUnequip(owner, id));
  }
  public static func ModificationDenied(owner: ref<GameObject>, id: ItemID) -> Bool {
    return CyberwarePolicy.Denied(owner, id) || CyberwarePolicy.Suppresses(owner, id);
  }
  public static func OperatingSystemDisabled(owner: ref<GameObject>) -> Bool {
    if !CyberwarePolicy.Active(owner) { return false; }
    let equipment = EquipmentSystem.GetData(owner);
    return IsDefined(equipment) &&
      CyberwarePolicy.Suppresses(owner, equipment.GetActiveItem(gamedataEquipmentArea.SystemReplacementCW));
  }
  private static func ArmAppearance(owner: ref<GameObject>) -> ref<CyberwareCustomizationSystem> {
    return GameInstance.GetScriptableSystemsContainer(owner.GetGame()).Get(n"CyberwareCustomizationSystem") as CyberwareCustomizationSystem;
  }
  private static func ArmAppearanceSettled(owner: ref<GameObject>) -> Bool {
    let system = CyberwarePolicy.ArmAppearance(owner);
    if !IsDefined(system) { return false; }
    let data = system.GetSavedData();
    return !data.enabled && data.switcherIndex == 0u && !data.hasMaxTacApperanceEquipped;
  }
''')
    source = one(source, '''    if !IsDefined(item) || !CyberwarePolicy.Denied(owner, item.GetID()) { return false; }
    let action = TweakDBInterface.GetObjectActionRecord(actionID);
    if !IsDefined(action) { return false; }
    return Equals(action.ActionName(), n"Use") || Equals(action.ActionName(), n"UseHealCharge") || Equals(action.ActionName(), n"Equip");''', '''    if !IsDefined(item) { return false; }
    let action = TweakDBInterface.GetObjectActionRecord(actionID);
    if !IsDefined(action) { return false; }
    if Equals(action.ActionName(), n"Equip") { return CyberwarePolicy.Denied(owner, item.GetID()); }
    return (Equals(action.ActionName(), n"Use") || Equals(action.ActionName(), n"UseHealCharge")) &&
      CyberwarePolicy.ModificationDenied(owner, item.GetID());''')
    source = one(source, '''    this.warmup = 4; this.actor = null; this.fault = false; ArrayClear(this.attempts);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || this.epoch != epoch { return; }''', '''    this.QueueRequest(new CyberwareTreatmentRestore());
  }
  private func OnCyberwareTreatmentRestore(request: ref<CyberwareTreatmentRestore>) -> Void {
    if !this.running { return; }
    this.epoch += 1;
    this.warmup = 4; this.actor = null; this.fault = false; ArrayClear(this.attempts);
    this.Schedule();
  }
  public func Poll(epoch: Int32) -> Void {
    let request = new CyberwareTreatmentStep();
    request.epoch = epoch;
    this.QueueRequest(request);
  }
  private func OnCyberwareTreatmentStep(request: ref<CyberwareTreatmentStep>) -> Void {
    if !this.running || this.epoch != request.epoch { return; }''')
    source = one(source, '''    if !CyberwarePolicy.Active(player) { this.pending = 0; this.detail = "Inactive / No Nerf / outside completed Tower"; return; }
    let data = EquipmentSystem.GetData(player);''', '''    let data = EquipmentSystem.GetData(player);
    if !IsDefined(data) { this.detail = "Waiting for equipment"; return; }
    if !CyberwarePolicy.Active(player) {
      this.pending = 0;
      if this.mode == 2 && data.PTFRHasTreatedCyberware() {
        if !CyberwarePolicy.Safe(player) { this.detail = "No Nerf waiting for safe gameplay"; return; }
        data.PTFRRestoreCyberwareEffects();
      }
      this.detail = "Inactive / No Nerf / outside completed Tower";
      return;
    }''')
    source = one(source, '    if this.pending == 0 { this.detail = "No restricted installed items"; return; }', '''    if this.pending == 0 && this.treatmentHandoff >= 1 && data.PTFRCyberwareEffectsReady() &&
      CyberwarePolicy.ArmAppearanceSettled(player) {
      this.detail = "Cyberware treatment settled";
      return;
    }''')
    source = one(source, '    let i = 0;\n    while i < ArraySize(ids) {\n      if !ArrayContains(this.attempts, ids[i]) {', '''    let effectsReady = data.PTFRCyberwareEffectsReady() || data.PTFRReconcileCyberwareEffects();
    if this.pending == 0 {
      if !CyberwarePolicy.ArmAppearanceSettled(player) {
        let appearance = CyberwarePolicy.ArmAppearance(player);
        if IsDefined(appearance) {
          let reset = new ResetPostTowerArmAppearance();
          reset.owner = player;
          appearance.QueueRequest(reset);
        }
        this.detail = "Waiting for native arm appearance reset";
        return;
      }
      if this.treatmentHandoff < 1 {
        this.treatmentHandoff = 1;
        ModLog(n"PTFR_Restrictions_R1", "Arms and Hands handoff complete; cosmetic tattoo refits enabled.");
      }
      this.detail = effectsReady ? "Cyberware treatment settled" : "Waiting for isolated cyberware effects";
      return;
    }
    let i = 0;
    while i < ArraySize(ids) {
      if !ArrayContains(this.attempts, ids[i]) {''')
    source = one(source, '    this.mode = 2; return "No Nerf selected for this save. Owned items remain; re-equip manually. No old loadout restored.";', '''    this.mode = 2;
    return "No Nerf selected. Retained effects restore when V is safe. Removed items can be equipped manually.";''')
    source = one(source, '      ArraySize(ids) == 0 && !data.IsEquipPending();', '''      this.treatmentHandoff >= 1 && ArraySize(ids) == 0 && data.PTFRCyberwareEffectsReady() &&
      CyberwarePolicy.ArmAppearanceSettled(player) && !data.IsEquipPending();''')
    source = one(source, 'public class PolicyTick extends DelayCallback {', '''public class CyberwareTreatmentRestore extends ScriptableSystemRequest {}
public class CyberwareTreatmentStep extends ScriptableSystemRequest { public let epoch: Int32; }

public class PolicyTick extends DelayCallback {''')
    source = one(source, '    id == this.ptfrr1PreserveParts && CyberwarePolicy.Denied(this.m_owner, id);', '''    id == this.ptfrr1PreserveParts && CyberwarePolicy.ModificationDenied(this.m_owner, id);''')
    source = one(source, '    if this.m_playerData.PTFRCF1PreservesExactItem(id) {', '''    if this.m_playerData.PTFRCF1PreservesExactItem(id) || CyberwarePolicy.Suppresses(this.m_owner, id) {''')
    source = one(source, '''  wrappedMethod(); // Keep EquipmentEx and vanilla restoration chains intact.
  let policy = CyberwarePolicy.Get(this.m_owner.GetGame());
  if IsDefined(policy) { policy.Restored(); }''', '''  if IsDefined(this.m_owner) && this.PTFRHasTreatedCyberware() { this.PTFRCyberwareRestoreStarted(); }
  wrappedMethod(); // Keep EquipmentEx and vanilla restoration chains intact.
  if IsDefined(this.m_owner) && this.m_owner == GameInstance.GetPlayerSystem(this.m_owner.GetGame()).GetLocalPlayerMainGameObject() {
    let policy = CyberwarePolicy.Get(this.m_owner.GetGame());
    if IsDefined(policy) { policy.Restored(); }
  }''')
    source = source.replace('PTFRR1RestrictedEquipped', 'PTFRPendingCyberwareRemoval')
    source = one(source, '''public final func PTFRPendingCyberwareRemoval() -> array<ItemID> {
  let ids: array<ItemID>;''', '''public final func PTFRPendingCyberwareRemoval() -> array<ItemID> {
  let ids = this.PTFRInstalledCyberware();
  let pending: array<ItemID>;
  let i = 0;
  while i < ArraySize(ids) {
    if CyberwarePolicy.MustUnequip(this.m_owner, ids[i]) { ArrayPush(pending, ids[i]); }
    i += 1;
  }
  return pending;
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRInstalledCyberware() -> array<ItemID> {
  let ids: array<ItemID>;''')
    source = one(source, '        if CyberwarePolicy.Restricted(id) && !ArrayContains(ids, id)', '        if ItemID.IsValid(id) && !ArrayContains(ids, id)')
    source = one(source, '  if !CyberwarePolicy.Denied(this.m_owner, id) || !CyberwarePolicy.Safe(this.m_owner as PlayerPuppet) { return 0; }',
                 '  if !CyberwarePolicy.Active(this.m_owner) || !CyberwarePolicy.MustUnequip(this.m_owner, id) || !CyberwarePolicy.Safe(this.m_owner as PlayerPuppet) { return 0; }')
    source = one(source, '  if CyberwarePolicy.Denied(this.m_owner, newID) { return; }',
                 '  if CyberwarePolicy.ModificationDenied(this.m_owner, newID) { return; }')
    source = one(source, '  if CyberwarePolicy.Denied(executor, itemID) { return false; }',
                 '  if CyberwarePolicy.ModificationDenied(executor, itemID) { return false; }')
    source = one(source, '  if IsDefined(request) && CyberwarePolicy.Denied(this.m_owner, request.itemID) { return; }', '''  if IsDefined(request) && CyberwarePolicy.Active(this.m_owner) {
    if CyberwarePolicy.ModificationDenied(this.m_owner, request.itemID) { return; }
    let area = EquipmentSystem.GetEquipAreaType(request.itemID);
    if CyberwarePolicy.Area(area) && (request.transferInstalledParts || request.removeOldItem) &&
      request.slotIndex >= 0 && request.slotIndex < this.GetNumberOfSlots(area, true) &&
      CyberwarePolicy.ModificationDenied(this.m_owner, this.GetItemInEquipSlot(area, request.slotIndex)) { return; }
  }''')
    # Keep upgrades and part rolls stable while the limited bonus is fixed.
    begin = source.index('@wrapMethod(RPGManager)\npublic final static func CanUpgradeCyberware')
    end = source.index('@wrapMethod(ItemActionsHelper)', begin)
    source = source[:begin] + source[begin:end].replace('CyberwarePolicy.Denied(', 'CyberwarePolicy.ModificationDenied(') + source[end:]
    source = one(source, '''  let mixed = Equals(this.ptfrr1SlotArea, gamedataEquipmentArea.EyesCW) || Equals(this.ptfrr1SlotArea, gamedataEquipmentArea.HandsCW);
  let item = this.GetUIInventoryItem();
  if mixed && (!IsDefined(item) || !CyberwarePolicy.Restricted(item.GetID())) { return; }''', '''  let item = this.GetUIInventoryItem();
  if !IsDefined(item) || !CyberwarePolicy.Denied(this.ptfrr1SlotPlayer, item.GetID()) { return; }''')
    source = one(source, '''  if IsDefined(item) && CyberwarePolicy.Denied(this.m_player, item.GetID()) {
    this.m_buttonHintsController.RemoveButtonHint(n"select");
    this.m_buttonHintsController.RemoveButtonHint(n"upgrade_perk");
    this.m_buttonHintsController.RemoveButtonHint(this.m_upgradeCWInputName);
    this.m_buttonHintsController.AddButtonHint(n"select", isVendorItem ? "Buy to inventory (installation blocked)" : "Installation blocked: post-Tower");
  }''', '''  if IsDefined(item) && CyberwarePolicy.ModificationDenied(this.m_player, item.GetID()) {
    this.m_buttonHintsController.RemoveButtonHint(n"upgrade_perk");
    this.m_buttonHintsController.RemoveButtonHint(this.m_upgradeCWInputName);
    if CyberwarePolicy.Denied(this.m_player, item.GetID()) && (isVendorItem || !item.IsEquipped()) {
      this.m_buttonHintsController.RemoveButtonHint(n"select");
      this.m_buttonHintsController.AddButtonHint(n"select", isVendorItem ? "Buy to inventory (installation blocked)" : "Installation blocked: post-Tower");
    }
  }''')
    source = one(source, '''    let note = "Installation blocked by post-Tower restrictions. Browse and buy to inventory.";
    if Equals(data.category, gamedataEquipmentArea.EyesCW) { note = "Only stock Basic Kiroshi Optics may be installed. Other models: inventory purchases only."; }
    if Equals(data.category, gamedataEquipmentArea.HandsCW) { note = "Only Tattoo: Johnny's Special may be installed. Other models: inventory purchases only."; }''', '''    let note = "Installed implants are disabled. You can remove them or buy items to inventory.";
    if Equals(data.category, gamedataEquipmentArea.ArmsCW) { note = "Combat arms cannot be refitted after the Tower."; }
    if Equals(data.category, gamedataEquipmentArea.EyesCW) { note = "Basic Kiroshi Optics remain functional. Other optics are disabled."; }
    if Equals(data.category, gamedataEquipmentArea.HandsCW) { note = "Stock tattoos can be refitted as cosmetic ink after the handoff."; }
    if Equals(data.category, gamedataEquipmentArea.MusculoskeletalSystemCW) { note = "Titanium Bones provide limited carry capacity. Other implants are disabled."; }
    if Equals(data.category, gamedataEquipmentArea.IntegumentarySystemCW) { note = "Chitin, Subdermal Armor and Carapace provide reduced armor. Other implants are disabled."; }''')

    predicates = []
    for model, rows in model_records.items():
        ids = [f'record == t"{row["id"]}"' for row in rows]
        aliases = sorted({row['sideUpgrade'] for row in rows if row['sideUpgrade']})
        ids.extend(f'TDBID.ToNumber(record) == {alias}ul' for alias in aliases)
        terms = ' ||\n      '.join(ids)
        predicates.append(f'  public static func {model}(record: TweakDBID) -> Bool {{\n    return {terms};\n  }}')
    treatment = (HERE / 'CyberwareTreatment.reds').read_text(encoding='utf-8')
    return source.rstrip() + '\n\n' + one(treatment, '  // STOCK_RECORD_PREDICATES', '\n\n'.join(predicates))


def edit_r3(source):
    source = one(source, 'ProfilePolicy.EmptyNativeSideEffectSlots(owner as PlayerPuppet)', 'ProfilePolicy.NativeSalePreservesCyberware(owner as PlayerPuppet, perk)')
    source = one(source, '''    let record = ItemID.GetTDBID(id);
    return (record == t"Items.CasiusTattoo" || record == t"Items.AdvancedCasiusTattoo") && CyberwarePolicy.Approved(record);''',
                 '''    return CyberwareTreatmentSettings.Tattoo(ItemID.GetTDBID(id));''')
    source = one(source, '''  private func RefundOne(player: ref<PlayerPuppet>, data: ref<PlayerDevelopmentData>) -> Void {
    let i = 0;''', '''  private func RefundOne(player: ref<PlayerPuppet>, data: ref<PlayerDevelopmentData>) -> Void {
    let held = "";
    let i = 0;''')
    source = one(source, '''        if !admission.success { this.Fail("Native slot/capacity admission refused for " + EnumValueToString("gamedataNewPerkType", Cast<Int64>(index))); return; }
        if !ProfilePolicy.EmptyNativeSideEffectSlots(player) { this.Fail("Native side-effect slot guard failed; no forced sale."); return; }''', '''        if !admission.success || !ProfilePolicy.NativeSalePreservesCyberware(player, perk) {
          if StrLen(held) == 0 { held = EnumValueToString("gamedataNewPerkType", Cast<Int64>(index)); }
        } else {''')
    begin = source.index('        this.selected = perk; this.inflight = true; this.mutation = true;',
                         source.index('  private func RefundOne('))
    end = source.index('\n      }\n      i += 1;', begin)
    indent = '\n'.join('  ' + line for line in source[begin:end].splitlines())
    source = source[:begin] + indent + '\n        }' + source[end:]
    source = one(source, '    this.Fail("No dependency-safe leaf. Force-selling refused.");', '''    if StrLen(held) > 0 {
      this.detail = "Refund waiting for native slot/capacity clearance: " + held;
      return;
    }
    this.Fail("No dependency-safe leaf. Force-selling refused.");''')
    source = replace_section(source, '  public static func EmptyNativeSideEffectSlots(', '  private func Total(', '''  public static func NativeSalePreservesCyberware(player: ref<PlayerPuppet>, perk: gamedataNewPerkType) -> Bool {
    let e = EquipmentSystem.GetData(player);
    if !IsDefined(e) || e.IsEquipPending() { return false; }
    if Equals(perk, gamedataNewPerkType.Tech_Central_Perk_3_2) {
      return e.GetNumberOfSlots(gamedataEquipmentArea.HandsCW, true) <= 1 ||
        !ItemID.IsValid(e.GetItemInEquipSlot(gamedataEquipmentArea.HandsCW, 1));
    }
    if Equals(perk, gamedataNewPerkType.Tech_Central_Milestone_3) {
      // The perk owns the third slot. The first two can retain inert items
      // because the exact R3 sale skips the native variant replacement below.
      let i = 0;
      while i < e.GetNumberOfSlots(gamedataEquipmentArea.MusculoskeletalSystemCW, true) {
        let id = e.GetItemInEquipSlot(gamedataEquipmentArea.MusculoskeletalSystemCW, i);
        if ItemID.IsValid(id) && (i >= 2 || !CyberwarePolicy.Suppresses(player, id)) { return false; }
        i += 1;
      }
    }
    if Equals(perk, gamedataNewPerkType.Tech_Central_Perk_3_3) {
      let i = 0;
      while i < e.GetNumberOfSlots(gamedataEquipmentArea.IntegumentarySystemCW, true) {
        let id = e.GetItemInEquipSlot(gamedataEquipmentArea.IntegumentarySystemCW, i);
        if ItemID.IsValid(id) && RPGManager.IsItemAdaptiveStemCells(ItemID.GetTDBID(id)) { return false; }
        i += 1;
      }
    }
    return true;
  }
''')
    source = one(source, '@wrapMethod(PlayerDevelopmentData)\nprivate final const func GetNewPerkGLPackageTDBID', '''@wrapMethod(PlayerDevelopmentData)
private final func HandleRemovingTech_Central_Milestone_3(playerData: ref<EquipmentSystemPlayerData>) -> Void {
  let perk = gamedataNewPerkType.Tech_Central_Milestone_3;
  if ProfilePolicy.OwnPerk(this.m_owner, perk) && playerData == EquipmentSystem.GetData(this.m_owner) &&
    ProfilePolicy.NativeSalePreservesCyberware(this.m_owner as PlayerPuppet, perk) {
    // Keep the inert instances in the two permanent slots. The native sale
    // still removes the perk package and credits the development point.
    return;
  }
  wrappedMethod(playerData);
}

@wrapMethod(PlayerDevelopmentData)
private final const func GetNewPerkGLPackageTDBID''')
    source = one(source, '  public func LC1Progress() -> String { return "Other ranks: "+ToString(this.refunded)+" / "+ToString(this.starting); }',
                 '''  public func LC1Progress() -> String {
    let progress = "Other ranks: " + ToString(this.refunded) + " / " + ToString(this.starting);
    return StrBeginsWith(this.detail, "Refund waiting") ? progress + "\\n" + this.detail : progress;
  }''')
    return source


def plain(path, root):
    assert path.is_file() and path.resolve().is_relative_to(root), path
    for entry in [path, *path.parents]:
        assert not entry.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, entry
        if entry == root:
            break


def compile_overlay(game, package, output):
    registry = game / 'r6/logs/redscript_rCURRENT.log'
    plain(registry, game)
    registry_hash = digest(registry)
    lines = registry.read_text(encoding='utf-8-sig').splitlines()
    registered = {(game / 'r6/scripts' / line.strip()).resolve()
                  for line in lines if line.strip().lower().endswith('.reds')}
    discovered = {p.resolve() for directory in ('r6/scripts', 'red4ext/plugins')
                  for p in (game / directory).rglob('*.reds')}
    assert registered == discovered and {game / R1, game / R3} <= registered
    compiler = game / 'engine/tools/scc.exe'
    caches = [game / 'r6/cache' / name for name in ('final.redscripts', 'final.redscripts.ts')]
    pins = {}
    for path in sorted(registered | {compiler, *caches}):
        plain(path, game)
        pins[path.relative_to(game).as_posix()] = digest(path)
    cache = output / 'cache'
    cache.mkdir(parents=True)
    for path in caches:
        staged_cache = cache / path.name
        shutil.copyfile(path, staged_cache)
        assert digest(staged_cache) == pins[path.relative_to(game).as_posix()]
    scripts = output / 'scripts'
    staged = {}
    for path in sorted(registered):
        relative = path.relative_to(game).as_posix()
        source = package / relative if relative in (R1, R3) else path
        destination = scripts / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        staged[relative] = digest(destination)
        assert staged[relative] == (digest(source) if relative in (R1, R3) else pins[relative])
    paths = output / 'compile_paths.txt'
    paths.write_bytes(b'')
    compiled = cache / 'compiled.redscripts'
    command = [compiler, '-compile', scripts, '-compilePathsFile', paths, '-customCacheDir',
               cache, '-outputCacheFile', compiled, cache / 'final.redscripts']
    result = subprocess.run(list(map(str, command)), capture_output=True, encoding='utf-8',
                            errors='replace', timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    log = result.stdout + result.stderr
    (output / 'scc.log').write_text(log, encoding='utf-8')
    assert digest(registry) == registry_hash
    assert all(digest(game / relative) == pin for relative, pin in pins.items())
    passed = result.returncode == 0 and 'Compilation complete' in log and compiled.is_file()
    write_json(output / 'result.json', {
        'status': 'PASS' if passed else 'FAIL', 'source_count': len(staged),
        'registry_sha256': registry_hash, 'input_pins': pins, 'staged_hashes': staged,
        'compiled_sha256': digest(compiled) if passed else None
    })
    if not passed:
        raise RuntimeError(log[-8500:])
    return len(staged)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=int)
    attempt = parser.parse_args().attempt
    assert attempt > 0
    candidate = HERE / f'candidate_{attempt:02}'
    package = candidate / 'overlay'
    output = HERE / f'compile_{attempt:02}'
    assert not candidate.exists() and not output.exists()
    assert digest(BASELINE) == BASELINE_HASH
    baseline = read_json(BASELINE)
    assert baseline['core_epoch'] == 'QP2_JOHNNY_LOAD_REPAIR'
    game = Path(baseline['game_root']).resolve()
    assert len(baseline['core_files']) == 51
    for row in baseline['core_files'] + baseline['required_files']:
        path = game / row['path']
        plain(path, game)
        assert path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], path
    records = read_json(HERE / 'scope_records_02.json')
    for row in records['inputs']:
        path = Path(row['Path'])
        plain(path, game)
        assert digest(path) == row['Sha256'], path

    patches = []
    hashes = {}
    for relative, edit in ((R1, lambda source: edit_r1(source, records['models'])), (R3, edit_r3)):
        source = game / relative
        before = source.read_text(encoding='utf-8')
        after = edit(before)
        destination = package / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(after, encoding='utf-8', newline='\n')
        assert destination.read_text(encoding='utf-8') == after
        patches.extend(unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                    'a/' + relative, 'b/' + relative))
        hashes[relative] = {'before': digest(source), 'after': digest(destination)}
    (candidate / 'source.patch').write_text(''.join(patches), encoding='utf-8', newline='\n')
    count = compile_overlay(game, package, output)
    write_json(candidate / 'verification.json', {
        'baseline_sha256': BASELINE_HASH, 'changed_sources': hashes,
        'exact_registered_source_count': count, 'compile': 'PASS', 'gameplay': 'UNVERIFIED',
        'installed': False,
    })
    print(f'Compiled two overlay files with all {count} registered scripts: {candidate}')


if __name__ == '__main__':
    main()
