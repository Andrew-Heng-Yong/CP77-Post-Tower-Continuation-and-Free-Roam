"""Offline Body R2 contracts, accounting models and real staged compilation.

This deliberately does not drive the game, touch saves or deploy compiler output.
The model is an independent oracle, not execution of the REDscript implementation.
"""
import argparse
import copy
import itertools
import json
import random
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import test_restrictions_r1 as r1
import test_restrictions_casius as casius

ROOT = r1.ROOT
GAME = r1.GAME
SRC = ROOT / 'redscript/PTFR_Restrictions_R2'
OUT = ROOT / 'research/restriction_profiles/body_r2'
DESIGN = ROOT / 'research/restriction_profiles/body_stats_design'
BASE_SHA = '2119046F3F3466206D8A16A4803B0EF0F3C90926AB689F9ABBD5B8E42E28EE86'
R1_BRIDGE = '''  // Read-only admission for the opt-in Body migration; never clears a fault.
  public final func PTFRR2Healthy() -> Bool { return !this.fault; }
  public final func PTFRR2Ready(player: ref<PlayerPuppet>) -> Bool {
    let data = EquipmentSystem.GetData(player);
    if !IsDefined(data) { return false; }
    let ids = data.PTFRR1RestrictedEquipped();
    return !this.fault && this.warmup == 0 && this.actor == player && CyberwarePolicy.Active(player) &&
      ArraySize(ids) == 0 && !data.IsEquipPending();
  }
'''


def verify_r1_candidate(installed):
    sources = {p.name: r1.read(p) for p in r1.SRC.glob('*.reds')}
    assert sources['CyberwarePolicy.reds'].count(R1_BRIDGE) == 1
    sources['CyberwarePolicy.reds'] = sources['CyberwarePolicy.reds'].replace(R1_BRIDGE, '')
    # The prior Casius audit independently proves that the remainder is exactly
    # its one approved line against installed R1, including original invariants.
    return casius.verify(sources, installed)


def stock_roster():
    checks = json.loads(r1.read(DESIGN / 'source_checks.json'))
    assert r1.sha(DESIGN / 'records.json') == checks['records_sha256']
    for relative, expected in checks['sources'].items():
        assert r1.sha(DESIGN.parent / 'ban_design/decompiled_current' / relative) == expected
    records = json.loads(r1.read(DESIGN / 'records.json'))
    for database in records['database_sources']:
        assert r1.sha(Path(database['path'])) == database['sha256']
    perks = checks['body_perks']
    assert len(perks) == 33 and sum(p['ranks'] for p in perks) == 41
    assert len({p['name'] for p in perks}) == len({p['hash'] for p in perks}) == 33
    assert sum(len(p['requires']) for p in perks) == 31
    assert {p['required_body'] for p in perks} == {4, 9, 15, 20}
    assert all(set(p['requires']) <= {x['hash'] for x in perks} for p in perks)
    return perks


class RefundModel:
    """Persistent, acknowledgement-oriented independent transaction oracle."""

    def __init__(self, roster, body, ranks):
        self.roster = {p['hash']: p for p in roster}
        self.state = dict(body=body, ranks=dict(ranks), attribute_unspent=7,
                          attribute_spent=body + 39, primary_unspent=11,
                          primary_spent=93, relic_unspent=2, relic_spent=13,
                          attributes_other=(20, 15, 12, 9), other_perks=(3, 2, 1),
                          character_level=60, street_cred=50, solo=55,
                          skill_xp=(123, 456, 789, 135, 246),
                          inventory=('weapon', 'part', 'basic_kiroshi', 'tattoo'))
        self.initial = copy.deepcopy(self.state)
        self.expected = copy.deepcopy(self.state)
        self.inflight = False
        self.fault = False
        self.done = False
        self.enabled = False
        self.operations = []
        self.vital_writes = []

    def activate(self):
        if not self.enabled:
            self.enabled = True
        return not self.fault

    def restored(self):
        # An interrupted native call is ambiguous; do not invent a refund retry.
        if self.inflight:
            self.fault = True

    def eligible(self):
        return [key for key, rank in self.state['ranks'].items() if rank > 0 and
                not any(self.state['ranks'][child] > 0 and key in row['requires']
                        for child, row in self.roster.items())]

    def next_operation(self):
        eligible = self.eligible()
        if eligible:
            return ('perk', sorted(eligible)[0])
        if any(self.state['ranks'].values()):
            return ('invalid_dependency', '')
        if self.state['body'] != 3:
            return ('body', '')
        return ('done', '')

    def tick(self, safe=True, mutate=None, interrupt=False):
        if not self.enabled or self.done or self.fault or not safe:
            return
        if self.inflight or self.state != self.expected:
            self.fault = True
            return
        kind, key = self.next_operation()
        if kind == 'done':
            self.done = True
            return
        if kind == 'invalid_dependency':
            self.fault = True
            return
        after = copy.deepcopy(self.expected)
        if kind == 'perk':
            after['ranks'][key] -= 1
            after['primary_unspent'] += 1
        else:
            amount = after['body'] - 3
            after['body'] = 3
            after['attribute_unspent'] += amount
            after['attribute_spent'] -= amount
        self.inflight = True
        self.state = copy.deepcopy(after)
        if mutate:
            mutate(self.state)
        self.operations.append((kind, key))
        if interrupt:
            return
        if self.state != after:
            self.fault = True
            return
        self.expected = after
        self.inflight = False

    def finish(self):
        for _ in range(50):
            self.tick()
        assert self.done and not self.fault
        assert self.state['body'] == 3 and not any(self.state['ranks'].values())
        count = sum(self.initial['ranks'].values())
        amount = self.initial['body'] - 3
        assert self.state['primary_unspent'] == self.initial['primary_unspent'] + count
        assert self.state['primary_spent'] == self.initial['primary_spent']
        assert self.state['attribute_unspent'] == self.initial['attribute_unspent'] + amount
        assert self.state['attribute_spent'] == self.initial['attribute_spent'] - amount
        for key in self.state.keys() - {'body', 'ranks', 'attribute_unspent', 'attribute_spent', 'primary_unspent'}:
            assert self.state[key] == self.initial[key], key
        assert not self.vital_writes
        return count, amount


def model_checks(roster):
    rng = random.Random(20261007)
    allocations = [dict.fromkeys((p['hash'] for p in roster), 0),
                   {p['hash']: p['ranks'] for p in roster}]
    allocations += [{p['hash']: rng.randrange(p['ranks'] + 1) for p in roster} for _ in range(64)]
    cases = refunds = repeat_checks = restore_checks = 0
    for body, ranks in itertools.product(range(3, 21), allocations):
        transaction = RefundModel(roster, body, ranks)
        assert transaction.activate()
        original = copy.deepcopy(transaction.state)
        transaction.tick(safe=False)
        assert transaction.state == original and not transaction.operations
        count, _ = transaction.finish()
        refunds += count
        completed = copy.deepcopy(transaction.state)
        for _ in range(3):
            transaction.activate()
            transaction.restored()
            transaction.tick()
            assert transaction.state == completed
            repeat_checks += 1
        cases += 1
    # Interrupt both before and after each possible native mutation. The journal
    # refuses ambiguous replay even if the mutation happened exactly once.
    full = RefundModel(roster, 20, allocations[1])
    full.activate()
    while not full.done:
        if full.next_operation()[0] == 'done':
            full.tick()
            break
        for happened in (False, True):
            copy_tx = copy.deepcopy(full)
            if happened:
                copy_tx.tick(interrupt=True)
            else:
                copy_tx.inflight = True
            state = copy.deepcopy(copy_tx.state)
            copy_tx.restored()
            assert copy_tx.fault
            copy_tx.tick()
            copy_tx.activate()
            copy_tx.tick()
            assert copy_tx.state == state
            restore_checks += 1
        full.tick()
    # Any unexpected progression/accounting drift must stop, not compensate.
    drift_checks = 0
    for field in ('body', 'attribute_unspent', 'attribute_spent', 'primary_unspent',
                  'primary_spent', 'relic_unspent', 'relic_spent', 'character_level',
                  'street_cred', 'solo'):
        for when in ('before', 'after'):
            transaction = RefundModel(roster, 20, allocations[1])
            transaction.activate()
            if when == 'before':
                transaction.state[field] += 1
                state = copy.deepcopy(transaction.state)
                transaction.tick()
                assert transaction.state == state
            else:
                transaction.tick(mutate=lambda state, key=field: state.__setitem__(key, state[key] + 1))
            assert transaction.fault
            state = copy.deepcopy(transaction.state)
            transaction.tick()
            assert transaction.state == state
            drift_checks += 1
    # Policy is a persistent opt-in, not auto-enabled by entering a pre-Tower save.
    # Exact implementation gate is checked against source separately.
    policy_cases = 0
    for opt_in, tower, normal, cyberware_on, busy, is_body in itertools.product((False, True), repeat=6):
        active = opt_in and tower and normal and cyberware_on
        denied = active and (busy or is_body)
        if not active or (not busy and not is_body):
            assert not denied
        if active and is_body:
            assert denied
        policy_cases += 1
    return dict(allocation_cases=cases, modeled_rank_refunds=refunds,
                repeat_or_completed_reload_checks=repeat_checks,
                ambiguous_interruption_checks=restore_checks,
                accounting_drift_checks=drift_checks, policy_cases=policy_cases,
                game_execution=False)


def verify_hooks(hooks):
    snapshot = r1.function(hooks, 'PTFRR2Snapshot')
    for field in ('attributes', 'devPoints', 'perkRanks', 'profTypes', 'profLevels',
                  'profXP', 'profSpent', 'legacyPerkTypes', 'legacyPerkRanks'):
        assert 'public persistent let ' + field + ':' in hooks
        assert 'result.' + field in snapshot
    assert 'ArrayResize(result.perkRanks, EnumInt(gamedataNewPerkType.Count))' in snapshot
    for seen in ('seenAttributes', 'seenPoints', 'seenBuckets', 'seenPerks', 'seenProfs'):
        assert 'ArrayContains(' + seen in snapshot
    assert 'result.liveBody != Cast<Float>(result.body)' in snapshot
    assert 'result.attributeSpent < result.body - 3' in snapshot
    assert snapshot.rstrip().endswith('result.valid = true;\n  return result;')
    reset = r1.function(hooks, 'PTFRR2ResetBody')
    for guard in ('OwnBodyReset', 'BodyPolicy.Safe', '!before.valid',
                  'before.perkRanks[i] > 0', 'PTFRR2CompatibleBodyCosts'):
        assert reset.index(guard) < reset.index('this.ResetAttribute(gamedataStatType.Strength)')
    costs = r1.function(hooks, 'PTFRR2CompatibleBodyCosts')
    assert 'player_attributeLevelToCostIncrease' in costs and '!= 1.00' in costs
    assert 'let i = 4' in costs and 'while i <= body' in costs
    assert 'snapshot.valid && this.PTFRR2CompatibleBodyCosts(snapshot.body)' in r1.function(hooks, 'PTFRR2CanResetBody')
    assert 'after.body == 3 && after.liveBody == 3.00' in reset
    assert 'after.attributeUnspent == before.attributeUnspent + before.body - 3' in reset
    assert 'after.attributeSpent == before.attributeSpent - before.body + 3' in reset
    sell = r1.function(hooks, 'PTFRR2SellBodyPerk')
    for guard in ('OwnPerk', 'BodyPolicy.Safe', 'BodyHookScope.IsBodyPerk',
                  'CheckIfAllnewPerkParentSold', 'CanSellNewPerk', '!allowed.success'):
        assert sell.index(guard) < sell.index('this.SellNewPerk(owner, perk)')
    assert sell.count('this.SellNewPerk(owner, perk)') == 1
    assert '.ForceSellNewPerk(' not in sell
    relock = r1.function(hooks, 'PTFRR2RelockBody')
    assert relock.index('this.IsNewPerkBought(records[i].Type()) != 0') < relock.index('this.LockNewPerk')
    assert 'RequiredAttributePoints() > this.GetAttributePoints' in relock
    assert 'new NewPerkLockedEvent()' in relock and '.QueueEvent(evt)' in relock
    assert 'this.UpdateUIBB()' in r1.function(hooks, 'PTFRR2PublishUI')
    restore = r1.function(hooks, 'OnRestored')
    assert 'wrappedMethod(gameInstance)' in restore and 'policy.Restored()' in restore
    for name in ('OnAttributeBuy', 'CanAttributeBeBought', 'BuyAttribute',
                 'CanNewPerkBeBought', 'BuyNewPerk', 'IsPerkUpgradeable'):
        body = r1.function(hooks, name)
        assert body.index('BodyPolicy.Busy') < body.index('wrappedMethod')
        assert body.index('BodyPolicy.BlockBody') < body.index('wrappedMethod')
    for name in ('SellNewPerk', 'ForceSellNewPerk', 'ResetAttribute', 'SellAttribute',
                 'ResetAttributes', 'SellAllAttributes', 'ResetNewPerks',
                 'ResetAllDevPoints', 'ClearAllDevPoints', 'SetDevelopmentsPoint', 'IsNewPerkRefundable'):
        body = r1.function(hooks, name)
        assert body.index('BodyPolicy.Busy') < body.index('wrappedMethod')
    assert '!BodyPolicy.OwnPerk(this.m_owner, perkType)' in r1.function(hooks, 'SellNewPerk')
    assert 'BodyPolicy.OwnBodyReset(this.m_owner)' in r1.function(hooks, 'ResetAttribute')
    return dict(all_attribute_and_development_ledgers=True, all_189_perk_ranks=True,
                independent_skills_and_legacy_ranks=True, normal_native_owner_ui_events=True,
                exact_body_reset_native_accounting=True, zero_rank_relock=True,
                force_buy_and_pregrant_guards=True)


def verify_sources(sources, roster):
    assert set(sources) == {'BodyPolicy.reds', 'DevelopmentHooks.reds', 'BodyCatalogue.reds'}
    for name, source in sources.items():
        for forbidden in ('@replaceMethod', '.SetFact(', '.SetFactValue(', '.GiveItem(', '.RemoveItem(',
                          '.SetAttribute(', '.AddDevelopmentPoints(', '.ForceModifier(', '.AddModifier(',
                          '.RemoveModifier(', '.RemoveSavedModifiers(', '.RemoveAllModifiers(',
                          '.RequestSettingStatPoolValue(', '.RequestSettingStatPoolMaxValue(',
                          '.RequestChangingStatPoolValue(', '.FlushDevelopment(', '.SetProgressionBuild('):
            assert forbidden not in source, (name, forbidden)
    hooks = verify_hooks(sources['DevelopmentHooks.reds'])
    catalogue = sources['BodyCatalogue.reds']
    names = re.findall(r'ArrayPush\(result, gamedataNewPerkType\.(\w+)\)', r1.function(catalogue, 'Types'))
    assert names == [p['name'] for p in roster]
    by_hash = {p['hash']: p for p in roster}
    for function, key in (('ExpectedRanks', 'ranks'), ('ExpectedThreshold', 'required_body')):
        mapping = dict((name, int(value)) for name, value in re.findall(
            r'case gamedataNewPerkType\.(\w+):\s+return (\d+);', r1.function(catalogue, function)))
        assert mapping == {p['name']: p[key] for p in roster}
    dependency_body = r1.function(catalogue, 'ExpectedDependencies')
    actual_dependencies = {}
    for name, body in re.findall(r'case gamedataNewPerkType\.(\w+):(.*?)(?=case gamedataNewPerkType\.|default:)', dependency_body, re.S):
        actual_dependencies[name] = re.findall(r'ArrayPush\(result, gamedataNewPerkType\.(\w+)\)', body)
    assert actual_dependencies == {p['name']: [by_hash[h]['name'] for h in p['requires']]
                                   for p in roster if p['requires']}
    valid = r1.function(catalogue, 'Valid')
    for guard in ('EnumInt(gamedataNewPerkType.Count) != 189', 'body.GetPerksCount() != 33',
                  'bodyStat.GetID() != t"BaseStats.Strength"', 'actual.GetID() != expected.GetID()',
                  'actual.GetLevelsCount() != BodyCatalogue.ExpectedRanks(type)',
                  'tier.RequiredAttributePoints() != BodyCatalogue.ExpectedThreshold(type)',
                  'ArraySize(requires) != ArraySize(expectedRequires)',
                  'requires[j].GetID() != dependency.GetID()',
                  '!ArrayContains(roster, type) && ArrayContains(roster, requires[j].Type())'):
        assert guard in valid
    core = sources['BodyPolicy.reds']
    for name, type_name in (('enabled', 'Bool'), ('schema', 'Int32'), ('stage', 'Int32'),
                            ('inflight', 'Bool'), ('expected', 'BodySnapshot'),
                            ('refundedRanks', 'Int32'), ('refundedAttributes', 'Int32')):
        assert f'private persistent let {name}: {type_name};' in core
    assert 'CyberwarePolicy.Active(owner)' in r1.function(core, 'BlockBody')
    assert 'policy.enabled' in r1.function(core, 'BlockBody')
    assert 'policy.stage >= 1 && policy.stage <= 3' in r1.function(core, 'Busy')
    assert 'policy.inflight && policy.actor == owner && policy.mutation > 0' in r1.function(core, 'OwnMutation')
    assert 'policy.mutation == 1 && Equals(policy.selected, perk)' in r1.function(core, 'OwnPerk')
    assert 'mutation == 2' in r1.function(core, 'OwnBodyReset')
    safe = r1.function(core, 'Safe')
    assert 'CyberwarePolicy.Safe(player)' in safe and 'gamedataStatPoolType.Overshield, false) <= 0.00' in safe
    restore = r1.function(core, 'Restored')
    assert 'this.stage != 0 && this.schema != 1' in restore
    assert 'if this.inflight { this.Fail(' in restore
    assert 'this.actor = null; this.mutation = 0' in restore
    poll = r1.function(core, 'Poll')
    assert 'this.epoch != epoch' in poll
    assert 'this.warmup > 0' in poll and 'this.stage == 5' in poll
    step = r1.function(core, 'OnBodyStep')
    for guard in ('request.epoch != this.epoch', 'this.actor != request.player',
                  '!BodyPolicy.BlockBody(player)', '!BodyPolicy.Safe(player)',
                  '!chrome.PTFRR2Healthy()', '!chrome.PTFRR2Ready(player)',
                  '!current.valid', '!BodyCatalogue.Valid()', '!BodyPolicy.Headroom(current)'):
        assert guard in step
    assert step.index('if this.stage == 4') < step.index('this.RefundOne')
    assert step.index('if !BodyPolicy.Same(this.expected, current, -1, false)') < step.index('this.RefundOne')
    assert 'current.body != 3 || BodyPolicy.Total(current) != 0' in step
    assert 'this.readyTicks < 3' in step
    refund = r1.function(core, 'RefundOne')
    ordered = ['this.expected.perkRanks[index] > 0', 'data.CheckIfAllnewPerkParentSold(perk)',
               'PlayerDevelopmentSystem.CanSellNewPerk', 'this.inflight = true; this.mutation = 1',
               '.PTFRR2SellBodyPerk(player, perk)', 'data.PTFRR2Snapshot()',
               '!BodyPolicy.Same(this.expected, after, index, false)',
               'this.expected = after; this.refundedRanks += 1; this.inflight = false',
               'UIInventoryScriptableSystem.GetInstance(player.GetGame()).QueueRequest(notification)']
    positions = [refund.index(fragment) for fragment in ordered]
    assert positions == sorted(positions)
    assert refund.count('.PTFRR2SellBodyPerk(player, perk)') == 1
    assert 'return;' in refund[refund.index('this.Note('):]
    reset = r1.function(core, 'ResetBody')
    ordered = ['data.PTFRR2CanResetBody()', 'let refund = this.expected.body - 3',
               'this.inflight = true; this.mutation = 2', 'data.PTFRR2ResetBody()',
               'data.PTFRR2RelockBody()', 'data.PTFRR2Snapshot()',
               '!BodyPolicy.Same(this.expected, after, -1, true)',
               'this.expected = after; this.refundedAttributes += refund; this.inflight = false',
               'this.stage = 3']
    positions = [reset.index(fragment) for fragment in ordered]
    assert positions == sorted(positions)
    same = r1.function(core, 'Same')
    for guard in ('!a.valid || !b.valid', 'b.attributeUnspent != a.attributeUnspent + attributeDelta',
                  'b.attributeSpent != a.attributeSpent - attributeDelta',
                  'b.primaryUnspent != a.primaryUnspent + rankDelta', 'b.primarySpent != a.primarySpent ||',
                  'b.relicUnspent != a.relicUnspent', 'b.relicSpent != a.relicSpent',
                  'b.perkRanks[i] != a.perkRanks[i] - (i == soldIndex ? 1 : 0)',
                  'a.profLevels[i] != b.profLevels[i]', 'a.profXP[i] != b.profXP[i]',
                  'a.profSpent[i] != b.profSpent[i]', 'a.legacyPerkRanks[i] != b.legacyPerkRanks[i]'):
        assert guard in same
    for array in ('attributes', 'devPoints', 'perkRanks', 'profTypes', 'legacyPerkTypes'):
        assert f'ArraySize(a.{array}) != ArraySize(b.{array})' in same
    for prefix, arrays in (('profTypes', ('profLevels', 'profXP', 'profSpent')),
                           ('legacyPerkTypes', ('legacyPerkRanks',))):
        for side, array in itertools.product(('a', 'b'), arrays):
            assert f'ArraySize({side}.{prefix}) != ArraySize({side}.{array})' in same
    command = r1.function(core, 'FullNerfWithoutVitals')
    assert command.index('if this.stage != 0') < command.index('chrome.Enable()')
    assert command.index('CyberwarePolicy.Completed(game)') < command.index('chrome.Enable()')
    assert command.index('BodyPolicy.Safe(player)') < command.index('chrome.Enable()')
    assert command.index('BodyPolicy.Headroom') < command.index('chrome.Enable()')
    assert 'this.enabled = true' in command and 'this.stage = 1' in command and 'this.schema = 1' in command
    settle = r1.function(core, 'Settle')
    assert 'this.settleTicks < 4' in settle and 'this.stage = 4' in settle
    for read in ('GetStatPoolValue', 'GetStatPoolMaxPointValue', 'GetStatValue'):
        assert '.' + read + '(' in r1.function(core, 'Measure')
    headroom = r1.function(core, 'Headroom')
    assert '2147483606' in headroom and '2147483630' in headroom
    assert 'this.mutation = 0; this.stage = 5' in r1.function(core, 'Fail')
    return dict(hooks=hooks, stock_body_roster_count=33, stock_body_possible_ranks=41,
                stock_dependencies=31, persistent_schema_journal=True, exact_ack_before_advance=True,
                no_replay_or_compensation=True, complete_progression_comparison=True,
                no_direct_hp_stamina_writes=True, four_equal_native_maxima_samples=True)


def source_mutants(sources, roster):
    mutations = [
        ('BodyPolicy.reds', 'if this.inflight { this.Fail(', 'if false { this.Fail('),
        ('BodyPolicy.reds', 'this.epoch != epoch', 'false'),
        ('BodyPolicy.reds', 'if this.stage != 0 { return "Not replayed.', 'if false { return "Not replayed.'),
        ('BodyPolicy.reds', 'b.primarySpent != a.primarySpent ||', 'b.primarySpent != a.primarySpent - rankDelta ||'),
        ('BodyPolicy.reds', 'b.attributeSpent != a.attributeSpent - attributeDelta', 'b.attributeSpent != a.attributeSpent'),
        ('BodyPolicy.reds', 'if !BodyPolicy.Same(this.expected, current, -1, false)', 'if false'),
        ('BodyPolicy.reds', 'this.inflight = true; this.mutation = 1', 'this.inflight = false; this.mutation = 1'),
        ('BodyPolicy.reds', 'this.refundedRanks += 1', 'this.refundedRanks += 2'),
        ('BodyPolicy.reds', 'this.settleTicks < 4', 'this.settleTicks < 0'),
        ('DevelopmentHooks.reds', 'this.ResetAttribute(gamedataStatType.Strength)', 'this.ResetAttribute(gamedataStatType.Intelligence)'),
        ('DevelopmentHooks.reds', 'this.IsNewPerkBought(records[i].Type()) != 0', 'false'),
        ('DevelopmentHooks.reds', 'return this.SellNewPerk(owner, perk);', 'return data.SellNewPerk(perk, soldRank);'),
        ('DevelopmentHooks.reds', 'after.attributeSpent == before.attributeSpent - before.body + 3', 'after.attributeSpent == before.attributeSpent'),
        ('BodyCatalogue.reds', 'body.GetPerksCount() != 33', 'body.GetPerksCount() != 32'),
        ('BodyCatalogue.reds', 'case gamedataNewPerkType.Body_Central_Milestone_3:\n        return 3;', 'case gamedataNewPerkType.Body_Central_Milestone_3:\n        return 2;'),
    ]
    rejected = []
    for name, before, after in mutations:
        assert before in sources[name], (name, before)
        mutant = dict(sources)
        mutant[name] = mutant[name].replace(before, after, 1)
        try:
            verify_sources(mutant, roster)
        except (AssertionError, ValueError):
            rejected.append(dict(source=name, removed=before, inserted=after))
        else:
            raise AssertionError('Source validator accepted mutant: ' + before)
    mutant = dict(sources)
    mutant['BodyPolicy.reds'] += '\n// forbidden actual call example\npublic func Bad() { pools.RequestSettingStatPoolMaxValue(id, gamedataStatPoolType.Health); }\n'
    try:
        verify_sources(mutant, roster)
    except AssertionError:
        rejected.append(dict(source='BodyPolicy.reds', inserted='Direct HP pool refill call'))
    else:
        raise AssertionError('Source validator accepted direct HP pool write')
    return rejected


def protected_inputs():
    result = {}
    installed_r1 = {}
    receipts = [r1.OUT / 'install_receipt.json',
                ROOT / 'research/afterlife_world/interactions_r11/install_receipt.json']
    for receipt_path in receipts:
        result[str(receipt_path)] = r1.sha(receipt_path)
        receipt = json.loads(r1.read(receipt_path))
        for entry in receipt['files']:
            path = GAME / entry['relative']
            assert r1.sha(path) == entry['sha256'], 'Installed receipt drift: ' + str(path)
            result[str(path)] = r1.sha(path)
            if receipt_path == receipts[0]:
                installed_r1[path.name] = r1.read(path)
    for name in ('final.redscripts', 'final.redscripts.modded', 'final.redscripts.ts',
                 'tweakdb.bin', 'tweakdb_ep1.bin'):
        path = GAME / 'r6/cache' / name
        result[str(path)] = r1.sha(path)
    assert result[str(GAME / 'r6/cache/final.redscripts')] == BASE_SHA
    for path in (DESIGN / 'records.json', DESIGN / 'source_checks.json',
                 r1.OUT / 'tests.json', casius.OUT / 'tests.json'):
        result[str(path)] = r1.sha(path)
    return result, installed_r1


def run_compile(approved, protected):
    # First use the headless compiler: scc may show a modal error for bad sources.
    # Inputs to both compilers are workspace copies, including the timestamp file.
    stage = Path(tempfile.mkdtemp(prefix='compile_', dir=OUT))
    cache = stage / 'cache'
    cache.mkdir()
    for name in ('final.redscripts', 'final.redscripts.ts'):
        shutil.copy2(GAME / 'r6/cache' / name, cache / name)
    dependencies = {}
    for path in (GAME / 'r6/scripts').rglob('*.reds'):
        relative = path.relative_to(GAME / 'r6/scripts')
        if relative.parts[0] in ('PTFR_Restrictions_R1', 'PTFR_Restrictions_R2'):
            if relative.parts[0] == 'PTFR_Restrictions_R1' and path.name != 'CyberwarePolicy.reds':
                dependencies[str(path)] = r1.sha(path)
            continue
        target = stage / 'scripts' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        dependencies[str(path)] = r1.sha(path)
        shutil.copy2(path, target)
        assert r1.sha(target) == dependencies[str(path)]
    plugin_paths = r1.read(r1.OUT / 'compile_paths.txt').splitlines()[2:]
    for directory in plugin_paths:
        for path in Path(directory).rglob('*.reds'):
            dependencies[str(path)] = r1.sha(path)
    cli = ROOT / 'research/finalboards_dismissal/tooling/redscript-cli.exe'
    source_paths = [r1.SRC, SRC, stage / 'scripts'] + [Path(p) for p in plugin_paths]
    quick_args = [str(cli), 'compile']
    # The older headless CLI cannot compile an existing EquipmentEx temporary-
    # expression construct. The installed SCC below checks all installed mods.
    for directory in (r1.SRC, SRC, GAME / 'red4ext/plugins/Codeware/Scripts'):
        quick_args += ['-s', str(directory)]
    quick_args += ['-b', str(cache / 'final.redscripts'), '-o', str(stage / 'headless.redscripts')]
    quick = subprocess.run(quick_args, cwd=ROOT, capture_output=True, text=True, timeout=90)
    quick_log = quick.stdout + quick.stderr
    (OUT / 'headless_compile.log').write_text(quick_log, encoding='utf-8')
    assert quick.returncode == 0 and 'Output successfully saved' in quick_log and 'ERROR' not in quick_log, quick_log[-10000:]
    paths_file = stage / 'compile_paths.txt'
    paths_file.write_text('\n'.join(str(p) for p in source_paths) + '\n', encoding='utf-8')
    scc = GAME / 'engine/tools/scc.exe'
    compiled_path = cache / 'compiled.redscripts'
    run = subprocess.run([str(scc), '-compile', str(SRC), '-compilePathsFile', str(paths_file),
                          '-customCacheDir', str(cache), '-outputCacheFile', str(compiled_path),
                          str(cache / 'final.redscripts')], cwd=ROOT, capture_output=True, text=True, timeout=90)
    log = run.stdout + run.stderr
    (OUT / 'compile.log').write_text(log, encoding='utf-8')
    assert run.returncode == 0 and 'Compilation complete' in log and 'Output successfully saved' in log and '[ERROR' not in log, log[-10000:]
    assert all(name in log for name in ('EquipmentEx.reds', 'CyberwarePolicy.reds', 'BodyPolicy.reds', 'DevelopmentHooks.reds'))
    flat = OUT / 'compiled_flat.script'
    decompile = subprocess.run([str(cli), 'decompile', '-i', str(compiled_path), '-o', str(flat)],
                               capture_output=True, text=True, timeout=45)
    assert 'Output successfully saved' in decompile.stdout + decompile.stderr
    compiled = r1.read(flat)
    assert set(re.findall(r't"(Items\.[^"]+)"', r1.function(compiled, 'Approved'))) == set(approved)
    for symbol in ('func FullNerfWithoutVitals(', 'func Measure(', 'EquipmentEx.OutfitSystem.GetInstance',
                   'func PTFRR2SellBodyPerk(', 'func PTFRR2ResetBody(', 'func PTFRR2Ready(',
                   'func PTFRR2Snapshot(', 'func PTFRR2RelockBody('):
        assert symbol in compiled, symbol
    for method, expected in (('PTFRR2SellBodyPerk', 'this.SellNewPerk(owner, perk)'),
                             ('PTFRR2ResetBody', 'this.ResetAttribute(gamedataStatType.Strength)'),
                             ('RefundOne', 'this.refundedRanks += 1'),
                             ('Restored', 'this.inflight')):
        # Restored is not globally unique in the full mod bundle.
        if method == 'Restored':
            assert 'Interrupted mutation journal.' in compiled
        else:
            assert expected in r1.function(compiled, method), method
    for path, expected in {**protected, **dependencies}.items():
        assert r1.sha(Path(path)) == expected, 'Read-only input changed: ' + path
    return dict(compiled_sha256=r1.sha(compiled_path), compiled_path=str(compiled_path),
                flat_sha256=r1.sha(flat), stage=str(stage), dependency_hashes=dependencies,
                dependency_roots=[str(GAME / 'r6/scripts')] + plugin_paths,
                headless_and_installed_compiler=True, compiled_symbols_readback=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-only', action='store_true')
    parser.add_argument('--no-compile', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    roster = stock_roster()
    models = model_checks(roster)
    if args.model_only:
        print(json.dumps(models, indent=2))
        return
    protected, installed = protected_inputs()
    approved, _ = verify_r1_candidate(installed)
    sources = {p.name: r1.read(p) for p in SRC.glob('*.reds')}
    contracts = verify_sources(sources, roster)
    mutants = source_mutants(sources, roster)
    candidate_paths = list(SRC.glob('*.reds')) + list(r1.SRC.glob('*.reds'))
    checked_sources = {str(p.relative_to(ROOT)).replace('\\', '/'): r1.sha(p) for p in candidate_paths}
    compile_result = {} if args.no_compile else run_compile(approved, protected)
    for relative, expected in checked_sources.items():
        assert r1.sha(ROOT / relative) == expected, 'Candidate changed during tests: ' + relative
    for path, expected in protected.items():
        assert r1.sha(Path(path)) == expected, 'Read-only input changed: ' + path
    old_receipt = json.loads(r1.read(r1.OUT / 'install_receipt.json'))
    replacement = next(x for x in old_receipt['files'] if Path(x['relative']).name == 'CyberwarePolicy.reds')
    files = [dict(relative=replacement['relative'], source='redscript/PTFR_Restrictions_R1/CyberwarePolicy.reds',
                  sha256=r1.sha(r1.SRC / 'CyberwarePolicy.reds'), before_sha256=replacement['sha256'])]
    for path in sorted(SRC.glob('*.reds')):
        files.append(dict(relative='r6/scripts/PTFR_Restrictions_R2/' + path.name,
                          source=str(path.relative_to(ROOT)).replace('\\', '/'),
                          sha256=r1.sha(path), before_sha256=None))
    assert len(files) == 4
    result = dict(status='PASS_RESTRICTIONS_BODY_R2_OFFLINE_LIVE_PENDING' if not args.no_compile else 'PASS_BODY_R2_SOURCE_MODEL_ONLY',
                  utc=datetime.now(timezone.utc).isoformat(), models=models,
                  source_contracts=contracts, source_mutants_rejected=mutants,
                  source_audit=True, equipmentex_full_compile=not args.no_compile,
                  checked_sources=checked_sources, base_sha256=BASE_SHA, files=files,
                  dependency_hashes=compile_result.get('dependency_hashes', {}),
                  dependency_roots=compile_result.get('dependency_roots', []),
                  preserved_inputs=protected, compile=compile_result,
                  installed=False, live_tested=False, game_writes=0, save_writes=0)
    output = OUT / ('source_model_tests.json' if args.no_compile else 'tests.json')
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('preserved_inputs', 'compile', 'dependency_hashes', 'source_mutants_rejected')}, indent=2))


if __name__ == '__main__':
    main()
