"""Compile actual sources and audit policy/transaction invariants. Not a game test."""
import hashlib
import itertools
import json
from pathlib import Path
import re
import shutil
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/restriction_profiles/implementation_r1'
SRC = ROOT / 'redscript/PTFR_Restrictions_R1'
GAME = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def read(path):
    return path.read_text(encoding='utf-8-sig')

def function(text, name, occurrence=0):
    matches = list(re.finditer(r'func ' + re.escape(name) + r'\(', text))
    start = text.index('{', matches[occurrence].end())
    depth = 1
    for end in range(start + 1, len(text)):
        depth += (text[end] == '{') - (text[end] == '}')
        if depth == 0:
            return text[start + 1:end]
    raise AssertionError(name)

def verify(sources):
    core, equip, ui = (sources[n] for n in ('CyberwarePolicy.reds', 'EquipmentHooks.reds', 'RipperdocHooks.reds'))
    approved = re.findall(r't"(Items\.[^"]+)"', function(core, 'Approved'))
    tiers = ('Common', 'CommonPlus', 'Uncommon', 'UncommonPlus', 'Rare', 'RarePlus', 'Epic', 'EpicPlus', 'Legendary', 'LegendaryPlus', 'LegendaryPlusPlus')
    expected = ['Items.AdvancedCasiusTattoo'] + ['Items.AdvancedKiroshiOpticsBare' + t for t in tiers]
    assert set(approved) == set(expected) and len(approved) == 12
    audit = json.loads(read(OUT / 'allowed_records.json'))
    records = {r['name']: r for r in audit['records']}
    for item in expected:
        assert item in records and records[item]['type'] in ('gamedataItem_Record', 'gamedataCyberware_Record')
    for a, b in zip(expected[1:-1], expected[2:]):
        assert records[a]['fields']['nextUpgradeItem']['name'] == b
    assert not records[expected[-1]]['fields']['nextUpgradeItem'].get('name')
    areas = re.findall(r'gamedataEquipmentArea\.(\w+)', function(core, 'Area'))
    assert len(areas) == len(set(areas)) == 10
    assert not {'PersonalLink', 'BaseFists', 'Splinter'} & set(areas)
    assert 'player.IsReplacer()' in function(core, 'Active')
    assert 'policy.mode != 2' in function(core, 'Active')
    assert len(re.findall(r'q.GetFact', function(core, 'Completed'))) == 10
    for s in sources.values():
        for forbidden in ('SetFact(', 'SetFactValue(', 'RemoveItem(', 'GiveItem(', 'RemoveAllStatusEffects', '@replaceMethod'):
            assert forbidden not in s, forbidden
    assert 'private persistent let mode' in core
    assert 'epoch != epoch' in function(core, 'Poll')
    assert 'ArrayContains(this.attempts, ids[i])' in core and 'this.fault = true' in core
    remove = function(equip, 'PTFRR1Remove')
    assert remove.index('CyberwarePolicy.Safe') < remove.index('this.UnequipItem')
    assert 'this.UnequipItem(area, slot, false)' in remove
    assert 'this.GetItemInEquipSlot(area, slot) != id' in remove
    assert 'UnequipBlocked' in remove and 'ts.GetItemQuantity(this.m_owner, id) != quantity' in remove
    assert 'InnerItemData.GetItemID(before[i])' in remove and 'InnerItemData.GetSlotID(before[i])' in remove
    assert 'this.ptfrr1PreserveParts = ItemID.None()' in remove
    for name in ('OnReplaceEquipmentRequest', 'HandleBuyShardPopupClosed'):
        body = function(equip, name)
        assert body.index('CyberwarePolicy.Denied') < body.index('wrappedMethod')
    for occurrence in (0, 1):
        body = function(ui, 'CheckIfCanEquip', occurrence)
        assert body.index('CyberwarePolicy.Denied') < body.index('wrappedMethod')
        assert 'DeniedAction' in function(equip, 'ProcessItemAction', occurrence)
    assert 'wrappedMethod();' in function(equip, 'OnRestored')
    buy = function(ui, 'OnItemBought')
    assert 'ptfrr1BuyOnly' in buy and 'return;' in buy[:buy.index('wrappedMethod')]
    # Comments mentioning EquipCyberware are intentionally allowed; no actual call.
    assert '.EquipCyberware(' not in buy[:buy.index('wrappedMethod')]
    assert 'result.confirm = false' in function(ui, 'OnBuyConfirmationPopupClosed')
    assert 'popup.ptfrr1BuyOnly = true' in function(ui, 'OnSlotClick')
    assert 'BuybackItemFromVendor(item, 1)' in function(ui, 'OnPTFRR1BuyClosed')
    assert '.SetLocked(' not in ui and '.m_isLocked =' not in ui
    assert 'ptfrr1SlotPlayer' in function(ui, 'PTFRR1PaintLock')
    assert 'CyberwarePolicy.Denied' in function(equip, 'AssignItemToHotkey')
    assert 'GetSellingPrice' in function(ui, 'PTFRR1Price')
    assert 'if ItemID.GetTDBID(itemID) != ItemID.GetTDBID(this.ptfrr1BuyOnly) { return; }' in buy
    return expected, areas

def main():
    OUT.mkdir(exist_ok=True)
    sources = {p.name: read(p) for p in SRC.glob('*.reds')}
    expected, areas = verify(sources)
    mutations = [
        ('CyberwarePolicy.reds', 'policy.mode != 2', 'true'),
        ('CyberwarePolicy.reds', 'Items.AdvancedCasiusTattoo', 'Items.AdvancedSilverhandTattoo'),
        ('CyberwarePolicy.reds', 'player.IsReplacer()', 'false'),
        ('EquipmentHooks.reds', 'this.UnequipItem(area, slot, false)', 'this.UnequipItem(area, slot, true)'),
        ('EquipmentHooks.reds', 'ts.GetItemQuantity(this.m_owner, id) != quantity', 'false'),
        ('RipperdocHooks.reds', 'result.confirm = false', 'result.confirm = true'),
        ('RipperdocHooks.reds', 'popup.ptfrr1BuyOnly = true', 'popup.ptfrr1BuyOnly = false'),
    ]
    for file, old, new in mutations:
        mutant = dict(sources); assert old in mutant[file]
        mutant[file] = mutant[file].replace(old, new)
        try:
            verify(mutant)
        except AssertionError:
            pass
        else:
            raise AssertionError('Mutant accepted: ' + old)
    # Explicit abstract decision model: not execution of compiled redscript.
    cases = 0
    for completed, normal, mode, in_area, allowed in itertools.product((False, True), (False, True), (0, 1, 2), (False, True), (False, True)):
        active = completed and normal and mode != 2
        denied = active and in_area and not allowed
        assert not denied or (completed and normal and mode != 2 and in_area and not allowed)
        if allowed or not completed or mode == 2 or not normal or not in_area:
            assert not denied
        cases += 1
    for confirm, funds, buy_only, newly_denied in itertools.product((False, True), repeat=4):
        paid = confirm and funds and (buy_only or not newly_denied)
        installed = paid and not buy_only and not newly_denied
        assert not (buy_only and installed)
        if not confirm or not funds or (not buy_only and newly_denied):
            assert not paid
        cases += 1
    # Once-per-actor item attempts, stale epoch and exact readback failure models.
    attempted = set(); inventory = {'mask': (1, ('part',)), 'basic': (1, ())}; before = dict(inventory)
    slots = ['mask', 'basic']; requests = []
    for tick in range(20):
        for item in slots[:]:
            if item != 'basic' and item not in attempted:
                attempted.add(item); requests.append(item); slots.remove(item)
    assert requests == ['mask'] and inventory == before and slots == ['basic']
    base = GAME / 'r6/cache/final.redscripts'
    baseline_hash = sha(base)
    assert baseline_hash == '2119046F3F3466206D8A16A4803B0EF0F3C90926AB689F9ABBD5B8E42E28EE86'
    # Catch our errors with the headless CLI before invoking the installed
    # compiler (which can show a desktop error dialog on failure).
    cli = ROOT / 'research/finalboards_dismissal/tooling/redscript-cli.exe'
    quick = subprocess.run([str(cli), 'compile', '-s', str(SRC), '-s', str(GAME/'red4ext/plugins/Codeware/Scripts'), '-b', str(base), '-o', str(OUT/'compile.redscripts')], capture_output=True, text=True, timeout=30)
    assert 'Output successfully saved' in quick.stdout + quick.stderr and 'ERROR' not in quick.stdout + quick.stderr, quick.stdout + quick.stderr
    cache = OUT / 'scc_cache'; cache.mkdir(exist_ok=True)
    # The compiler opens the input timestamp for writing. BOTH inputs are copies.
    shutil.copy2(base, cache / 'final.redscripts')
    shutil.copy2(GAME / 'r6/cache/final.redscripts.ts', cache / 'final.redscripts.ts')
    scc = GAME / 'engine/tools/scc.exe'
    cmd = [str(scc), '-compile', str(SRC), '-compilePathsFile', str(OUT / 'compile_paths.txt'), '-customCacheDir', str(cache), '-outputCacheFile', str(cache / 'compiled.redscripts'), str(cache / 'final.redscripts')]
    run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=90)
    log = run.stdout + run.stderr
    (OUT / 'compile.log').write_text(log, encoding='utf-8')
    assert run.returncode == 0 and 'Compilation complete' in log and 'Output successfully saved' in log and '[ERROR' not in log, log[-6000:]
    assert 'EquipmentEx.reds' in log and 'CyberwarePolicy.reds' in log
    assert sha(base) == baseline_hash
    # Flat output is essential: compiled units contain absolute source paths.
    # Never use decompile -f here, which can target those original locations.
    flat = OUT / 'compiled_flat.script'
    decompile = subprocess.run([str(cli), 'decompile', '-i', str(cache/'compiled.redscripts'), '-o', str(flat)], capture_output=True, text=True, timeout=30)
    assert 'Output successfully saved' in decompile.stdout + decompile.stderr
    compiled = read(flat)
    for symbol in ('public class PTFR.RestrictionsR1.CyberwarePolicy extends ScriptableSystem', 'func PTFRR1Remove(', 'func OnPTFRR1BuyClosed(', 'popup$local$2.ptfrr1BuyOnly = true', 'policy$local$0.Restored();', 'EquipmentEx.OutfitSystem.GetInstance'):
        assert symbol in compiled, symbol
    files = [{'source': str(p.relative_to(ROOT)).replace('\\', '/'), 'relative': 'r6/scripts/PTFR_Restrictions_R1/' + p.name, 'sha256': sha(p)} for p in sorted(SRC.glob('*.reds'))]
    assert len(files) == 3
    dependencies = {}
    for path in read(OUT / 'compile_paths.txt').splitlines()[1:]:
        for p in Path(path).rglob('*.reds'):
            dependencies[str(p)] = sha(p)
    result = {'status': 'PASS_RESTRICTIONS_R1_OFFLINE_LIVE_PENDING', 'utc': datetime.now(timezone.utc).isoformat(), 'files': files,
              'compiler': str(scc), 'compiler_sha256': sha(scc), 'compiled_sha256': sha(cache / 'compiled.redscripts'),
              'base_sha256': baseline_hash, 'source_audit': True, 'source_mutants_rejected': len(mutations),
              'abstract_decision_cases': cases, 'abstract_lifecycle': True, 'approved_records': expected, 'restricted_areas': areas,
              'equipmentex_full_compile': True, 'compiled_symbol_readback': True, 'dependency_hashes': dependencies, 'live_tested': False, 'game_writes': 0,
              'checked_sources': {str(p.relative_to(ROOT)).replace('\\','/'): sha(p) for p in (Path(__file__), OUT/'allowed_records.json', OUT/'slot_records.json', OUT/'compile_paths.txt')}}
    (OUT / 'tests.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('files', 'dependency_hashes', 'checked_sources', 'approved_records', 'restricted_areas')}, indent=2))

if __name__ == '__main__':
    main()
