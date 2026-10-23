"""Relic refund/menu extension: source, stock records, models, actual compilation.

Models do not execute REDscript. Never drives the game or writes installed files.
"""
import copy
import itertools
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import test_restrictions_r1 as r1
import test_restrictions_body_r2 as body
import test_restrictions_body_cost_r2_1 as cost

ROOT, GAME, SRC = r1.ROOT, r1.GAME, body.SRC
OUT = ROOT / 'research/restriction_profiles/relic_r2_2'
MAX = 2147483647


def protect():
    saved, installed = {}, {}
    for folder in (r1.OUT, ROOT / 'research/afterlife_world/interactions_r11', body.OUT, cost.OUT):
        path = folder / 'install_receipt.json'
        saved[str(path)] = r1.sha(path)
        for row in json.loads(r1.read(path))['files']:
            installed[str(GAME / row['relative'])] = row['sha256']
    for path, digest in installed.items():
        assert r1.sha(Path(path)) == digest, 'Installed receipt mismatch: ' + path
        saved[path] = digest
    for folder in (r1.OUT, body.OUT, cost.OUT):
        for name in ('tests.json', 'deployment_tests.json'):
            path = folder / name
            saved[str(path)] = r1.sha(path)
    for name in ('final.redscripts', 'final.redscripts.modded', 'final.redscripts.ts', 'tweakdb.bin', 'tweakdb_ep1.bin'):
        path = GAME / 'r6/cache' / name
        saved[str(path)] = r1.sha(path)
    assert saved[str(GAME / 'r6/cache/final.redscripts')] == body.BASE_SHA
    for path in (Path(__file__), ROOT / 'tools/test_restrictions_body_r2.py', ROOT / 'tools/test_restrictions_r1.py',
                 OUT / 'records.json', body.DESIGN / 'body_catalogue_records.json', body.DESIGN / 'current_base.script'):
        saved[str(path)] = r1.sha(path)
    return saved, installed


def record_checks():
    report = json.loads(r1.read(OUT / 'records.json'))
    for database in report['database_sources']:
        assert r1.sha(Path(database['path'])) == database['sha256']
    records = {r['hash']: r for r in report['reference_closure']}
    records.update({r['hash']: r for r in report['records']})
    by_name = {r['name']: r for r in report['records']}
    tree = by_name['NewPerks.EspionageAttributeData']
    assert tree['fields']['attribute']['hash'] == by_name['BaseStats.Espionage']['hash']
    roster = []
    for ref in tree['fields']['perks']:
        row = records[ref['hash']]
        f = row['fields']
        assert f['attribute']['hash'] == tree['hash'] and len(f['levels']) == 1
        assert int(records[f['tier']['hash']]['fields']['requiredAttributePoints']) == 0
        roster.append(dict(name=f['enumName'], hash=row['hash'], requires=[d['hash'] for d in f['requiresPerks']]))
    milestones = {'Espionage_Central_Milestone_1', 'Espionage_Left_Milestone_Perk', 'Espionage_Right_Milestone_1'}
    for row in roster:
        row['cost'] = 3 if row['name'] in milestones else 1
    assert len(roster) == 9 and sum(r['cost'] for r in roster) == 15
    assert sum(len(r['requires']) for r in roster) == 6
    all_audit = json.loads(r1.read(body.DESIGN / 'body_catalogue_records.json'))
    for database in all_audit['database_sources']:
        assert r1.sha(Path(database['path'])) == database['sha256']
    modern = {r['fields']['enumName']: r for r in all_audit['records'] if r['type'] == 'gamedataNewPerk_Record'}
    assert len(modern) == 189
    relic_hashes = {r['hash'] for r in roster}
    for name, row in modern.items():
        if row['hash'] not in relic_hashes:
            assert not relic_hashes & {d['hash'] for d in row['fields']['requiresPerks']}
    native = r1.read(body.DESIGN.parent / 'ban_design/decompiled_current/cyberpunk/systems/playerDevelopmentSystem.script')
    fresh = r1.read(body.DESIGN / 'current_base.script')
    checks = []
    for name, count in [('SellNewPerk', 2), ('ReturnDevelopmentPointForSoldPerk', 1), ('IsEspionageMilestonePerk', 1),
                        ('HandleRemovingPerkLevel', 1), ('DeactivateNewPerk', 1), ('AddDevelopmentPoints', 1),
                        ('BuyNewPerk', 2), ('CanNewPerkBeBought', 1), ('CheckIfAllNewPerkParentSold', 1)]:
        for n in range(count):
            fragment = r1.function(native, name, n)
            assert fragment in fresh, name
            checks.append(name + ':' + str(n))
    refund = r1.function(native, 'ReturnDevelopmentPointForSoldPerk')
    assert 'devPoints = isEspionageMilestonePerk ? 3 : 1' in refund
    assert 'this.AddDevelopmentPoints(devPoints, gamedataDevelopmentPointType.Espionage)' in refund
    assert 'spent -=' not in r1.function(native, 'AddDevelopmentPoints')
    assert set(re.findall(r'gamedataNewPerkType\.(Espionage_\w+)', r1.function(native, 'IsEspionageMilestonePerk'))) == milestones
    assert 'GLPS.RemovePackage(this.m_owner, packageID)' in r1.function(native, 'DeactivateNewPerk')
    removing = r1.function(native, 'HandleRemovingPerkLevel')
    assert 'ItemID.IsValid(itemID)' in removing and 'AttachmentSlots.NanoWiresQuickhackSlot' in removing
    ui = r1.read(body.DESIGN.parent / 'ban_design/decompiled_current/cyberpunk/UI/fullscreen/perks/newPerks/NewPerksCategoriesGameController.script')
    for name in ('UpdateJohnnyEspionageAttribute', 'OpenPerksScreen', 'InitializePerkScreen', 'OnTabMenuArrowClicked', 'PlayRelicIntroAnim'):
        assert r1.function(ui, name) in fresh, name
        checks.append(name)
    return roster, checks


def methods(source):
    return {name: r1.function(source, name) for name in re.findall(r'\bfunc (\w+)\(', source)}


def verify(sources, roster):
    assert set(sources) == {'BodyPolicy.reds', 'DevelopmentHooks.reds', 'BodyCatalogue.reds', 'RelicCatalogue.reds', 'RelicMenu.reds'}
    for source in sources.values():
        for denied in ('@replaceMethod', 'SetFact(', 'SetFactValue(', '.GiveItem(', '.RemoveItem(', '.ForceSellNewPerk(',
                       '.RemoveAllStatusEffects(', '.SetAttribute(', '.AddDevelopmentPoints(', '.AddModifier(', '.RemoveModifier(',
                       '.RequestSettingStatPoolValue(', '.RequestSettingStatPoolMaxValue(', '.RequestChangingStatPoolValue('):
            assert denied not in source, denied
    unchanged = []
    allowed_changes = {'BodyPolicy.reds': {'OwnPerk', 'OnBodyStep', 'FullNerfWithoutVitals', 'Measure', 'GetStatus', 'Same'},
                       'DevelopmentHooks.reds': {'CanNewPerkBeBought', 'BuyNewPerk', 'IsPerkUpgradeable'}}
    allowed_new = {'BodyPolicy.reds': {'BlockRelic', 'OwnRelicPerk', 'RefundRelicOne', 'IncludeRelic'},
                   'DevelopmentHooks.reds': {'IsRelicPerk', 'PTFRR2SellRelicPerk'}}
    for name in ('BodyPolicy.reds', 'DevelopmentHooks.reds'):
        old = methods(r1.read(GAME / 'r6/scripts/PTFR_Restrictions_R2' / name))
        new = methods(sources[name])
        assert set(new) - set(old) == allowed_new[name]
        assert set(old) <= set(new)
        assert {n for n in old if new[n] != old[n]} == allowed_changes[name]
        unchanged += [name + ':' + n for n in old if n not in allowed_changes[name]]
    assert sources['BodyCatalogue.reds'] == r1.read(GAME / 'r6/scripts/PTFR_Restrictions_R2/BodyCatalogue.reds')
    cost.verify_cost_method(sources['DevelopmentHooks.reds'])
    core, hooks, catalog, menu = (sources[n] for n in ('BodyPolicy.reds', 'DevelopmentHooks.reds', 'RelicCatalogue.reds', 'RelicMenu.reds'))
    def contains(source, name, *tokens):
        code = r1.function(source, name)
        for token in tokens:
            assert token in code, (name, token)
        return code
    contains(core, 'BlockRelic', 'BodyPolicy.BlockBody(owner)', '.relicEnabled')
    contains(core, 'OwnRelicPerk', 'BodyPolicy.OwnPerk(owner, perk)', 'BodyPolicy.BlockRelic(owner)', '.mutation == 3')
    contains(core, 'OwnPerk', 'policy.mutation == 1', 'policy.mutation == 3 && policy.relicEnabled', 'Equals(policy.selected, perk)')
    extend = contains(core, 'IncludeRelic', 'if this.relicEnabled', 'this.schema != 1', 'this.stage > 4 || this.inflight',
                      'CyberwarePolicy.Completed(game)', 'BodyPolicy.BlockBody(player)', 'BodyPolicy.Safe(player)',
                      '!current.valid', '!RelicCatalogue.Valid()', '!RelicCatalogue.Headroom(current)',
                      'if this.stage == 4', 'current.body != 3 || BodyPolicy.Total(current) != 0',
                      'this.expected = current; this.stage = 3', 'this.stage != 1 && !BodyPolicy.Same(this.expected, current, -1, false)',
                      'this.epoch += 1; this.queued = false', 'this.warmup = 4', 'if this.running { this.Schedule(); }')
    assert extend.index('if this.relicEnabled') < extend.index('this.expected = current')
    for denied in ('this.ResetBody(', 'this.RefundOne(', 'this.stage = 1', 'this.stage = 2', 'this.refundedRanks =', 'this.refundedAttributes ='):
        assert denied not in extend
    activate = contains(core, 'FullNerfWithoutVitals', 'if this.stage != 0', 'if !this.relicEnabled { return this.IncludeRelic(); }',
                        '!RelicCatalogue.Valid() || !RelicCatalogue.Headroom(snapshot)', 'this.relicEnabled = true')
    assert activate.index('RelicCatalogue.Valid()') < activate.index('chrome.Enable()')
    step = contains(core, 'OnBodyStep', 'this.relicEnabled && !RelicCatalogue.Valid()', 'this.relicEnabled && RelicCatalogue.Total(current) > 0',
                    'this.RefundRelicOne(player, data)', '(this.relicEnabled && RelicCatalogue.Total(current) != 0)')
    assert step.index('if this.stage == 4') < step.index('this.RefundRelicOne(')
    assert step.index('!BodyPolicy.Same(this.expected, current, -1, false)') < step.index('this.RefundRelicOne(')
    refund = contains(core, 'RefundRelicOne', 'this.inflight || !this.relicEnabled || this.stage != 3', '!RelicCatalogue.Headroom(this.expected)',
                      'data.CheckIfAllnewPerkParentSold(perk)', 'PlayerDevelopmentSystem.CanSellNewPerk(player, perk)',
                      'let cost = RelicCatalogue.Cost(perk)', 'this.inflight = true; this.mutation = 3',
                      '.PTFRR2SellRelicPerk(player, perk)', 'BodyPolicy.Same(this.expected, after, index, false, cost)',
                      'this.refundedRelicRanks += 1; this.refundedRelicPoints += cost; this.inflight = false', 'this.settleTicks = 0')
    assert refund.index('this.inflight = true') < refund.index('.PTFRR2SellRelicPerk(') < refund.index('BodyPolicy.Same(') < refund.index('this.refundedRelicPoints += cost') < refund.index('UIInventoryScriptableSystem')
    same = contains(core, 'Same', 'relicCost != 0 && (reset || soldIndex < 0', 'RelicCatalogue.Cost(IntEnum<gamedataNewPerkType>(soldIndex)) != relicCost',
                    'let primaryDelta = relicCost == 0 ? rankDelta : 0', 'a.primaryUnspent + primaryDelta',
                    'a.relicUnspent + relicCost', 'b.relicSpent != a.relicSpent', 'unspent += primaryDelta',
                    'gamedataDevelopmentPointType.Espionage) { unspent += relicCost; }')
    # Prove that all other ledger/attribute/rank/XP comparisons are still exactly
    # the installed comparator, rather than just checking a few representative fields.
    same = same.replace('    if relicCost != 0 && (reset || soldIndex < 0 || soldIndex >= EnumInt(gamedataNewPerkType.Count) ||\n      RelicCatalogue.Cost(IntEnum<gamedataNewPerkType>(soldIndex)) != relicCost) { return false; }\n', '')
    same = same.replace('    let primaryDelta = relicCost == 0 ? rankDelta : 0;\n', '').replace('primaryDelta', 'rankDelta')
    same = same.replace('a.relicUnspent + relicCost', 'a.relicUnspent')
    same = same.replace('      if Equals(a.devPoints[i].type, gamedataDevelopmentPointType.Espionage) { unspent += relicCost; }\n', '')
    assert same == r1.function(r1.read(GAME / 'r6/scripts/PTFR_Restrictions_R2/BodyPolicy.reds'), 'Same')
    helper = contains(hooks, 'PTFRR2SellRelicPerk', '!BodyPolicy.OwnRelicPerk(owner, perk)', '!BodyPolicy.Safe(owner as PlayerPuppet)',
                      '!BodyHookScope.IsRelicPerk(perk)', 'RelicCatalogue.Cost(perk) == 0', '!chrome.PTFRR2Ready',
                      'ItemID.IsValid(equipment.GetItemInEquipSlot(gamedataEquipmentArea.ArmsCW, 0))',
                      'data.IsNewPerkBought(perk) != 1', '!data.CheckIfAllnewPerkParentSold(perk)', 'return this.SellNewPerk(owner, perk)')
    assert helper.index('gamedataEquipmentArea.ArmsCW') < helper.index('this.SellNewPerk(')
    for name in ('CanNewPerkBeBought', 'BuyNewPerk', 'IsPerkUpgradeable'):
        contains(hooks, name, 'BodyPolicy.BlockRelic(', 'BodyHookScope.IsRelicPerk(')
    names = re.findall(r'ArrayPush\(result, gamedataNewPerkType\.(\w+)\)', r1.function(catalog, 'Types'))
    assert names == [row['name'] for row in roster]
    by_hash = {row['hash']: row['name'] for row in roster}
    dependency = r1.function(catalog, 'Dependencies')
    for cases, parent in re.findall(r'((?:\s*case gamedataNewPerkType\.\w+:)+)\s*ArrayPush\(result, gamedataNewPerkType\.(\w+)\)', dependency):
        for child in re.findall(r'case gamedataNewPerkType\.(\w+):', cases):
            row = next(r for r in roster if r['name'] == child)
            assert [by_hash[d] for d in row['requires']] == [parent]
    assert len(re.findall(r'case gamedataNewPerkType\.', dependency)) == 6
    costs = contains(catalog, 'Cost', 'if !ArrayContains(types, perk) { return 0; }', '? 3 : 1')
    assert set(re.findall(r'gamedataNewPerkType\.(\w+)', costs)) == {r['name'] for r in roster if r['cost'] == 3}
    contains(catalog, 'Headroom', 'rank < 0 || rank > 1', 'rank * RelicCatalogue.Cost(types[i])', '2147483647 - points')
    contains(catalog, 'Valid', '!= 189', '!= 9', 'actual.GetLevelsCount() != 1', 'actual.Tier().RequiredAttributePoints() != 0',
             'requires[j].GetID() != dependency.GetID()', '!ArrayContains(types, type) && ArrayContains(types, requires[j].Type())')
    for name in ('UpdateJohnnyEspionageAttribute', 'OpenPerksScreen', 'InitializePerkScreen', 'OnTabMenuArrowClicked', 'PlayRelicIntroAnim'):
        contains(menu, name, 'this.PTFRR2RelicClosed()', 'wrappedMethod(')
    contains(menu, 'UpdateJohnnyEspionageAttribute', 'this.m_isEspionageUnlocked = false', 'PerkMenuAttribute.Johnny', 'PerkMenuAttribute.Espionage', '.SetVisible(false)')
    contains(menu, 'InitializePerkScreen', 'gamedataStatType.Espionage', 'this.CloseActiveScreen(); return;')
    contains(menu, 'OnTabMenuArrowClicked', 'this.m_isEspionageUnlocked = false')
    contains(menu, 'OpenPerksScreen', 'gamedataStatType.Espionage) { return; }')
    contains(menu, 'PlayRelicIntroAnim', 'if this.PTFRR2RelicClosed() { return; }')
    return dict(unchanged_methods=unchanged, other_snapshot_comparisons_exact=True, native_sale_only=True,
                cost_precision_fix_preserved=True, relic_menu_and_navigation_closed=True, story_fact_writes=False)


def model_checks(roster):
    """Independent transaction/extension model; not execution of candidate code."""
    by_hash = {r['hash']: r for r in roster}
    class Model:
        def __init__(self, ranks, stage):
            self.stage, self.enabled, self.inflight = stage, False, False
            self.state = dict(body=20 if stage < 3 else 3, body_ranks=14 if stage == 0 else (7 if stage < 3 else 0),
                              attr=0 if stage < 3 else 17, primary=1 if stage == 0 else (8 if stage < 3 else 15),
                              relic=2, relic_spent=13, relic_ranks=dict(ranks), unrelated=(48, 8, 20, 11, 10, 999))
            self.expected = copy.deepcopy(self.state)
            self.body_refunds = 0 if stage == 0 else (7 if stage < 3 else 14)
            self.attr_refunds = 0 if stage < 3 else 17
            self.relic_refunds = 0
        def activate(self, safe=True):
            if self.stage == 0 and safe:
                self.stage = 1; self.enabled = True; return
            if self.enabled or not safe or self.inflight or not 1 <= self.stage <= 4:
                return
            if self.stage == 4:
                if self.state['body'] != 3 or self.state['body_ranks'] != 0:
                    return
                self.expected = copy.deepcopy(self.state)
                self.stage = 3
            elif self.stage != 1 and self.state != self.expected:
                return
            self.enabled = True
        def tick(self, safe=True, drift=None, interrupt=False):
            if not self.enabled or self.stage in (4, 5) or not safe:
                return
            if self.inflight or (self.stage != 1 and self.state != self.expected):
                self.stage = 5; return
            if self.stage == 1:
                self.expected = copy.deepcopy(self.state); self.stage = 2; return
            after = copy.deepcopy(self.expected)
            kind, amount = '', 0
            if self.stage == 2:
                if after['body_ranks']:
                    after['body_ranks'] -= 1; after['primary'] += 1; kind, amount = 'body', 1
                else:
                    amount = after['body'] - 3; after['body'] = 3; after['attr'] += amount; kind = 'attribute'
            elif any(after['relic_ranks'].values()):
                eligible = [h for h, rank in after['relic_ranks'].items() if rank and
                            not any(after['relic_ranks'][child] and h in row['requires'] for child, row in by_hash.items())]
                assert eligible
                chosen = eligible[0]; kind, amount = 'relic', by_hash[chosen]['cost']
                remaining = sum(by_hash[h]['cost'] * rank for h, rank in after['relic_ranks'].items())
                if after['relic'] > MAX - remaining:
                    self.stage = 5; return
                after['relic_ranks'][chosen] -= 1; after['relic'] += amount
            else:
                self.stage = 4; return
            self.inflight = True
            self.state = copy.deepcopy(after)
            if drift: drift(self.state)
            if interrupt: return
            if self.state != after:
                self.stage = 5; return
            self.expected = after; self.inflight = False
            if kind == 'body': self.body_refunds += amount
            if kind == 'attribute': self.attr_refunds += amount; self.stage = 3
            if kind == 'relic': self.relic_refunds += amount
    allocations = repeats = 0
    for bits in itertools.product((0, 1), repeat=9):
        ranks = dict(zip(by_hash, bits))
        refund = sum(by_hash[h]['cost'] * rank for h, rank in ranks.items())
        for stage in (0, 1, 2, 3, 4):
            model = Model(ranks, stage)
            before = copy.deepcopy(model.state)
            model.activate()
            for _ in range(40): model.tick()
            assert model.stage == 4 and not model.inflight
            assert model.state['body'] == 3 and model.state['body_ranks'] == 0
            assert model.state['attr'] == 17 and model.state['primary'] == 15
            assert model.state['relic'] == 2 + refund and not any(model.state['relic_ranks'].values())
            assert model.state['relic_spent'] == before['relic_spent'] and model.state['unrelated'] == before['unrelated']
            assert model.attr_refunds == 17 and model.body_refunds == 14 and model.relic_refunds == refund
            final = copy.deepcopy(model.__dict__)
            for _ in range(3):
                model.activate(); model.tick(); assert model.__dict__ == final; repeats += 1
            allocations += 1
    full = {h: 1 for h in by_hash}
    interrupted = drifted = 0
    for step in range(9):
        model = Model(full, 4); model.activate()
        for _ in range(step): model.tick()
        model.tick(interrupt=True)
        state = copy.deepcopy(model.state)
        model.tick(); assert model.stage == 5 and model.state == state
        model.activate(); model.tick(); assert model.stage == 5 and model.state == state
        interrupted += 1
    for key in ('attr', 'primary', 'relic', 'relic_spent', 'body', 'body_ranks'):
        model = Model(full, 4); model.activate()
        model.tick(drift=lambda state: state.__setitem__(key, state[key] + 1))
        assert model.stage == 5
        state = copy.deepcopy(model.state); model.activate(); model.tick(); assert model.state == state
        drifted += 1
    for spent in (0, 5, MAX - 15, MAX - 14):
        model = Model(full, 4); model.state['relic'] = spent; model.activate()
        for _ in range(20): model.tick()
        assert model.stage == (5 if spent > MAX - 15 else 4)
        if model.stage == 4: assert model.state['relic'] == spent + 15
    for stage in (1, 2, 3, 4):
        model = Model(full, stage); before = copy.deepcopy(model.__dict__)
        model.activate(safe=False); model.tick(); assert model.__dict__ == before
    for stage in (2, 3):
        model = Model(full, stage); model.state['primary'] += 1; model.activate(); assert not model.enabled
    for kind in ('body', 'body_ranks'):
        model = Model(full, 4); model.state[kind] += 1; model.activate(); assert not model.enabled
    policy_cases = 0
    def menu_model(body_active, relic_enabled, index, direction, direct_relic=False):
        closed = body_active and relic_enabled
        if direct_relic:
            return (not closed, None)
        count = 5 if closed else 6
        return (True, (index + direction + count) % count)
    for body_active, relic_enabled in itertools.product((False, True), repeat=2):
        expected_roster = [0, 1, 2, 3, 4] if body_active and relic_enabled else [0, 1, 2, 3, 4, 5]
        assert menu_model(body_active, relic_enabled, 0, 0, True)[0] == (5 in expected_roster)
        for index in expected_roster:
            for direction in (-1, 1):
                admitted, next_index = menu_model(body_active, relic_enabled, index, direction)
                expected_index = expected_roster[(expected_roster.index(index) + direction) % len(expected_roster)]
                assert admitted and next_index == expected_index
                policy_cases += 1
    # A second save without the opt-in keeps its own progression and Relic tree.
    first, second = Model(full, 4), Model(full, 4)
    untouched = copy.deepcopy(second.__dict__)
    first.activate()
    for _ in range(20): first.tick()
    second.tick()
    assert second.__dict__ == untouched
    return dict(allocation_and_saved_stage_cases=allocations, repeated_activation_checks=repeats,
                interrupted_native_calls=interrupted, wrong_delta_cases=drifted, overflow_boundaries=4,
                unsafe_extension_cases=4, drifted_old_journal_cases=2, changed_completed_body_cases=2,
                menu_navigation_cases=policy_cases, independent_save_model=True, game_execution=False)


def main():
    OUT.mkdir(exist_ok=True, parents=True)
    protected, installed = protect()
    roster, anchors = record_checks()
    sources = {p.name: r1.read(p) for p in SRC.glob('*.reds')}
    contracts = verify(sources, roster)
    mutants = [
        ('BodyPolicy.reds', 'this.expected = current; this.stage = 3;', 'this.expected = current; this.stage = 2;'),
        ('BodyPolicy.reds', 'this.refundedRelicPoints += cost', 'this.refundedRelicPoints += 1'),
        ('BodyPolicy.reds', 'a.relicUnspent + relicCost', 'a.relicUnspent + 1'),
        ('BodyPolicy.reds', 'b.relicSpent != a.relicSpent', 'b.relicSpent != a.relicSpent - relicCost'),
        ('BodyPolicy.reds', 'this.epoch += 1; this.queued = false;\n    this.actor = player;', 'this.queued = false;\n    this.actor = player;'),
        ('DevelopmentHooks.reds', 'data.IsNewPerkBought(perk) != 1', 'data.IsNewPerkBought(perk) < 0'),
        ('DevelopmentHooks.reds', 'ItemID.IsValid(equipment.GetItemInEquipSlot(gamedataEquipmentArea.ArmsCW, 0))', 'false'),
        ('DevelopmentHooks.reds', 'if BodyPolicy.BlockRelic(this.m_owner) && BodyHookScope.IsRelicPerk(perkType)', 'if false'),
        ('RelicCatalogue.reds', '? 3 : 1', '? 1 : 1'),
        ('RelicCatalogue.reds', '2147483647 - points', '2147483647'),
        ('RelicCatalogue.reds', 'actual.GetLevelsCount() != 1', 'false'),
        ('RelicMenu.reds', 'this.PTFRR2RelicClosed() && Equals(statType, gamedataStatType.Espionage)', 'false'),
        ('RelicMenu.reds', 'if this.PTFRR2RelicClosed() { return; }', 'if false { return; }'),
    ]
    for name, old, new in mutants:
        assert old in sources[name], old
        mutated = dict(sources); mutated[name] = mutated[name].replace(old, new, 1)
        try: verify(mutated, roster)
        except AssertionError: pass
        else: raise AssertionError('Accepted source mutant: ' + old)
    models = model_checks(roster)
    original_models = body.model_checks(body.stock_roster())
    for path in r1.SRC.glob('*.reds'):
        assert r1.sha(path) == r1.sha(GAME / 'r6/scripts/PTFR_Restrictions_R1' / path.name)
    checked = {str(p.relative_to(ROOT)).replace('\\', '/'): r1.sha(p) for p in list(SRC.glob('*.reds')) + list(r1.SRC.glob('*.reds'))}
    body.OUT = OUT
    approved = re.findall(r't"(Items\.[^"]+)"', r1.function(r1.read(r1.SRC / 'CyberwarePolicy.reds'), 'Approved'))
    compiled = body.run_compile(approved, protected)
    flat = r1.read(OUT / 'compiled_flat.script')
    for name, token in [('PTFRR2SellRelicPerk', 'this.SellNewPerk(owner, perk)'), ('IncludeRelic', 'this.stage = 3'),
                        ('RefundRelicOne', 'this.refundedRelicPoints += cost'), ('PTFRR2RelicClosed', 'BodyPolicy.BlockRelic')]:
        code = re.sub(r'\$local\$\d+', '', r1.function(flat, name))
        assert token in code, name
    assert 'wrappedMethod' not in r1.function(flat, 'PTFRR2SellRelicPerk')
    for name in ('RelicCatalogue', 'RelicMenu.reds', 'EquipmentEx.reds'):
        assert name in flat or name in r1.read(OUT / 'compile.log')
    for path, digest in protected.items(): assert r1.sha(Path(path)) == digest, path
    for path, digest in checked.items(): assert r1.sha(ROOT / path) == digest, path
    files = []
    for name in ('BodyPolicy.reds', 'DevelopmentHooks.reds', 'RelicCatalogue.reds', 'RelicMenu.reds'):
        relative = 'r6/scripts/PTFR_Restrictions_R2/' + name
        files.append(dict(relative=relative, source='redscript/PTFR_Restrictions_R2/' + name,
                          sha256=r1.sha(SRC / name), before_sha256=installed.get(str(GAME / relative))))
    result = dict(status='PASS_RELIC_R2_2_OFFLINE_LIVE_PENDING', utc=datetime.now(timezone.utc).isoformat(),
                  source_contracts=contracts, source_mutants_rejected=len(mutants), models=models,
                  original_body_models=original_models, native_source_anchors=anchors, relic_roster=roster,
                  exact_relic_full_tree_refund=15, checked_sources=checked, files=files,
                  equipmentex_full_compile=True, compile=compiled, dependency_hashes=compiled['dependency_hashes'],
                  dependency_roots=compiled['dependency_roots'], base_sha256=body.BASE_SHA,
                  protected_inputs=protected, installed=False, live_tested=False, game_writes=0, save_writes=0)
    (OUT / 'tests.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('compile','protected_inputs','dependency_hashes','checked_sources','source_contracts','relic_roster')}, indent=2))


if __name__ == '__main__':
    main()
