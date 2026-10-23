"""One-method Body R2 cost conversion regression; workspace-only compilation.

The accounting tests are independent models, not live game execution. Historical
R2 evidence is preserved. Its source validator is run on the unchanged remainder
with this one method normalized to the installed predecessor; the new method has
separate contracts, negative mutants and compiled-output checks below.
"""
import argparse
import json
import math
import re
import struct
from datetime import datetime, timezone
from pathlib import Path

import test_restrictions_r1 as r1
import test_restrictions_body_r2 as body

ROOT, GAME = r1.ROOT, r1.GAME
OUT = ROOT / 'research/restriction_profiles/body_cost_r2_1'
R2_OUT = body.OUT
RELATIVE = 'r6/scripts/PTFR_Restrictions_R2/DevelopmentHooks.reds'
SOURCE = 'redscript/PTFR_Restrictions_R2/DevelopmentHooks.reds'
BEFORE_SHA = '49D3BB837704DA60F2A2B300D991025B7A01EC0E9ABA2FB59621A41760317DAB'
METHOD = 'PTFRR2CompatibleBodyCosts'
LIVE_LINE = '4:1 5:1.00038397 6:1 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1'


def protected_inputs():
    protected = {}
    # Later R2 entries supersede the original R1 policy receipt, not its two
    # untouched hook files. No historical result or receipt is rewritten.
    expected = {}
    for folder in (r1.OUT, ROOT / 'research/afterlife_world/interactions_r11', R2_OUT):
        receipt_path = folder / 'install_receipt.json'
        protected[str(receipt_path)] = r1.sha(receipt_path)
        for entry in json.loads(r1.read(receipt_path))['files']:
            expected[str(GAME / entry['relative'])] = entry['sha256']
    for path, digest in expected.items():
        assert r1.sha(Path(path)) == digest, 'Installed receipt drift: ' + path
        protected[path] = digest
    for name in ('final.redscripts', 'final.redscripts.modded', 'final.redscripts.ts',
                 'tweakdb.bin', 'tweakdb_ep1.bin'):
        path = GAME / 'r6/cache' / name
        protected[str(path)] = r1.sha(path)
    assert protected[str(GAME / 'r6/cache/final.redscripts')] == body.BASE_SHA
    for path in (Path(__file__), ROOT / 'tools/test_restrictions_body_r2.py',
                 ROOT / 'tools/test_restrictions_r1.py', R2_OUT / 'tests.json',
                 R2_OUT / 'deployment_tests.json', R2_OUT / 'ValidateRollback.json',
                 body.DESIGN / 'source_checks.json', body.DESIGN / 'records.json'):
        protected[str(path)] = r1.sha(path)
    return protected


def verify_cost_method(source):
    method = r1.function(source, METHOD)
    statements = re.sub(r'//[^\n]*', '', method)
    statements = re.sub(r'\s+', ' ', statements).strip()
    expected = '''if !IsDefined(this.m_owner) || body < 3 || body > 20 { return false; }
      let curve = GameInstance.GetStatsDataSystem(this.m_owner.GetGame());
      let statName = EnumValueToName(n"gamedataStatType", Cast<Int64>(EnumInt(gamedataStatType.Strength)));
      let i = 4;
      while i <= body {
        let rawCost = curve.GetValueFromCurve(n"player_attributeLevelToCostIncrease", Cast<Float>(i), statName);
        if !(rawCost > 0.00 && rawCost < 2.00) { return false; }
        if Cast<Int32>(rawCost) != 1 { return false; }
        i += 1;
      }
      return true;'''
    assert statements == re.sub(r'\s+', ' ', expected).strip(), 'Cost conversion contract changed'
    return method


def verify_candidate(sources):
    receipt = json.loads(r1.read(R2_OUT / 'install_receipt.json'))
    old_hooks = r1.read(GAME / RELATIVE)
    assert r1.sha(GAME / RELATIVE) == BEFORE_SHA
    old_method = r1.function(old_hooks, METHOD)
    new_method = verify_cost_method(sources['DevelopmentHooks.reds'])
    normalized = dict(sources)
    assert normalized['DevelopmentHooks.reds'].count(new_method) == 1
    normalized['DevelopmentHooks.reds'] = normalized['DevelopmentHooks.reds'].replace(new_method, old_method)
    assert normalized['DevelopmentHooks.reds'] == old_hooks, 'Change outside the one cost method'
    for entry in receipt['files']:
        if entry['relative'] != RELATIVE:
            assert r1.sha(ROOT / entry['source']) == entry['sha256'], 'Unrelated R2/R1 source change'
    for name in ('EquipmentHooks.reds', 'RipperdocHooks.reds'):
        assert r1.sha(r1.SRC / name) == r1.sha(GAME / 'r6/scripts/PTFR_Restrictions_R1' / name)
    return normalized


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def cost_models():
    # Model REDscript Float precision and native positive Float-to-Int32 cost.
    # Actual compiled Cast<Int32> is also checked, not replaced with an epsilon.
    def unit_cost(value):
        return value > 0.0 and value < 2.0 and math.trunc(value) == 1

    def compatible(level, values, owner=True):
        return owner and 3 <= level <= 20 and all(unit_cost(values[i]) for i in range(4, level + 1))

    values = {int(part.split(':')[0]): f32(float(part.split(':')[1])) for part in LIVE_LINE.split()}
    assert values[5] != 1.0 and math.trunc(values[5]) == 1
    assert not all(value == 1.0 for value in values.values())
    assert compatible(20, values)
    assert sum(math.trunc(value) for value in values.values()) == 17
    cases = [('exact one', 1.0, True), ('observed level five', values[5], True),
             ('next float above one', f32(1.0000001192092896), True),
             ('largest float below two', f32(1.9999998807907104), True),
             ('below one', f32(0.9999999403953552), False),
             ('zero', 0.0, False), ('negative', -1.0, False), ('two points', 2.0, False),
             ('three points', 3.0, False), ('huge', f32(3.4e38), False),
             ('NaN', float('nan'), False), ('positive infinity', float('inf'), False),
             ('negative infinity', float('-inf'), False)]
    for label, raw, expected in cases:
        assert unit_cost(raw) == expected, label
    per_level = 0
    for level in range(3, 21):
        assert compatible(level, values)
        assert not compatible(level, values, owner=False)
        for bad_level in range(4, level + 1):
            for label, raw, expected in cases:
                if expected:
                    continue
                invalid = dict(values)
                invalid[bad_level] = raw
                assert not compatible(level, invalid), (level, bad_level, label)
                per_level += 1
    for invalid_level in (-1, 0, 2, 21, 2147483647):
        assert not compatible(invalid_level, values)
    return dict(observed_curve=LIVE_LINE, observed_level5_float32=values[5],
                observed_old_rejection=True, observed_new_acceptance=True,
                expected_attribute_refund=17, scalar_boundary_cases=len(cases),
                per_level_invalid_cost_cases=per_level, body_range_cases=23,
                owner_guard_cases=18, model_only_not_runtime=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-compile', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    protected = protected_inputs()
    native = r1.read(ROOT / 'research/restriction_profiles/ban_design/decompiled_current/cyberpunk/systems/playerDevelopmentSystem.script')
    assert 'Cast<Int32>(statDataSystem.GetValueFromCurve(' in r1.function(native, 'GetAttributeNextLevelCost')
    assert 'cost = this.GetAttributeNextLevelCost(type)' in r1.function(native, 'BuyAttribute')
    sources = {path.name: r1.read(path) for path in body.SRC.glob('*.reds')}
    normalized = verify_candidate(sources)
    roster = body.stock_roster()
    contracts = body.verify_sources(normalized, roster)
    original_mutants = body.source_mutants(normalized, roster)
    mutants = [
        ('if Cast<Int32>(rawCost) != 1', 'if rawCost != 1.00'),
        ('if Cast<Int32>(rawCost) != 1', 'if false'),
        ('if Cast<Int32>(rawCost) != 1', 'if Cast<Int32>(rawCost) > 1'),
        ('if !(rawCost > 0.00 && rawCost < 2.00) { return false; }', ''),
        ('while i <= body', 'while i < body'),
        ('let i = 4;', 'let i = 5;'),
        ('gamedataStatType.Strength', 'gamedataStatType.Intelligence'),
        ('body < 3 || body > 20', 'false'),
    ]
    original_method = r1.function(sources['DevelopmentHooks.reds'], METHOD)
    for before, after in mutants:
        assert before in original_method
        mutant_source = sources['DevelopmentHooks.reds'].replace(original_method, original_method.replace(before, after, 1))
        try:
            verify_cost_method(mutant_source)
        except AssertionError:
            pass
        else:
            raise AssertionError('Accepted cost mutant: ' + after)
    costs = cost_models()
    models = body.model_checks(roster)
    checked_sources = {str(path.relative_to(ROOT)).replace('\\', '/'): r1.sha(path)
                       for path in list(body.SRC.glob('*.reds')) + list(r1.SRC.glob('*.reds'))}
    approved = re.findall(r't"(Items\.[^"]+)"', r1.function(r1.read(r1.SRC / 'CyberwarePolicy.reds'), 'Approved'))
    body.OUT = OUT  # Reuse compilation mechanics; never overwrite R2 evidence.
    compiled = {} if args.no_compile else body.run_compile(approved, protected)
    if not args.no_compile:
        method = r1.function(r1.read(OUT / 'compiled_flat.script'), METHOD)
        method = re.sub(r'\$local\$\d+', '', method)
        assert 'Cast<Int32>(rawCost) != 1' in method
        assert 'rawCost > 0.00 && rawCost < 2.00' in method
        assert method.index('rawCost > 0.00') < method.index('Cast<Int32>(rawCost)')
        assert 'while i <= body' in method and 'rawCost != 1.00' not in method
    for path, digest in protected.items():
        assert r1.sha(Path(path)) == digest, 'Protected input changed: ' + path
    for path, digest in checked_sources.items():
        assert r1.sha(ROOT / path) == digest, 'Candidate changed during validation: ' + path
    result = dict(status='PASS_BODY_COST_R2_1_SOURCE_MODEL_ONLY' if args.no_compile else 'PASS_BODY_COST_R2_1_OFFLINE_LIVE_PENDING',
                  utc=datetime.now(timezone.utc).isoformat(), checked_sources=checked_sources,
                  files=[dict(relative=RELATIVE, source=SOURCE, before_sha256=BEFORE_SHA, sha256=r1.sha(ROOT / SOURCE))],
                  exact_one_method_delta=True, source_contracts=contracts,
                  cost_source_mutants_rejected=len(mutants), original_source_mutants_rejected=len(original_mutants),
                  original_contract_cost_method_normalized=True, cost_regressions=costs, original_accounting_models=models,
                  equipmentex_full_compile=not args.no_compile, compile=compiled,
                  protected_inputs=protected, dependency_hashes=compiled.get('dependency_hashes', {}),
                  dependency_roots=compiled.get('dependency_roots', []),
                  base_sha256=body.BASE_SHA, installed=False, live_tested=False, game_writes=0, save_writes=0)
    output = OUT / ('source_model_tests.json' if args.no_compile else 'tests.json')
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('compile', 'protected_inputs', 'dependency_hashes', 'checked_sources', 'source_contracts')}, indent=2))


if __name__ == '__main__':
    main()
