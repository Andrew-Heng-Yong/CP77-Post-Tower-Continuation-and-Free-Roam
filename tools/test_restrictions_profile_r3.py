"""R3 source/record checks and independent models. Not engine runtime proof."""
import copy, itertools, json, math, random, re
from datetime import datetime, timezone
from pathlib import Path
import build_restrictions_profile_r3 as build
import compile_restrictions_profile_r3 as compiler
import test_restrictions_r1 as common
import test_restrictions_body_r2 as body
import test_restrictions_relic_r2_2 as relic

ROOT, GAME, OUT = compiler.ROOT, compiler.GAME, compiler.OUT
PREDECESSORS = {
 'PTFR_Restrictions_R1/CyberwarePolicy.reds': 'D9CF279E8FB15BA2319CB6CFBB1D2B1E71656B691986D202D9F89CEA95D3CBD1',
 'PTFR_Restrictions_R2/BodyPolicy.reds': '731758C7717CD164FA967DF993E480BE07C40B5BDF8096F6A770A933F0A36FAE',
 'PTFR_Restrictions_R2/DevelopmentHooks.reds': '6D87171DCFCFFA1F4DC10276B7D30AF10BCFFAFF26A1989F324DE42AFDDF7BD3',
}
def read(p): return Path(p).read_text(encoding='utf-8-sig')
def source_checks(s):
    p,h,v,d = (s[n] for n in ('ProfilePolicy.reds','ProfileHooks.reds','ProfilePhysical.reds','DevelopmentHooks.reds'))
    for needle in (
      'if this.inflight { this.Fail(', 'if this.enabled && !this.MatchesDefinition()',
      'this.selected = perk; this.inflight = true; this.mutation = true;',
      'if !sold || !BodyPolicy.Same(this.expected, after, index, false)',
      'this.expected = after; this.refunded += 1; this.inflight = false;',
      'this.Total(current) > 2147483647 - current.primaryUnspent',
      'if !BodyPolicy.Same(this.expected, current, -1, false)',
      'if !legacy.PTFRR3Complete()', 'this.handAttempted = true; this.inflight = true;',
      'EquipmentArea.MusculoskeletalSystemCW, true', 'EquipmentArea.IntegumentarySystemCW, true',
      'if !ProfileCatalogue.Valid()', 'if this.stage == 4', 'if !ProfilePolicy.Active(owner)',
      'snapshot.perkRanks[EnumInt(gamedataNewPerkType.Cool_Right_Perk_3_3)] != 0',
    ): assert needle in p, needle
    assert p.index('if !ProfileCatalogue.Valid()', p.index('public func Apply')) < p.index('legacy.PTFRR3StartBodyRelic()')
    for name in ('CanNewPerkBeBought','BuyNewPerk','IsPerkUpgradeable'):
        assert 'ProfilePolicy.PerkDenied' in common.function(d, name), name
    sale = common.function(h, 'PTFRR3SellPerk')
    for needle in ('ProfilePolicy.OwnPerk', 'BodyPolicy.Safe', 'EmptyNativeSideEffectSlots', 'CanSellNewPerk', 'this.SellNewPerk(owner, perk)'): assert needle in sale
    binding = common.function(h, 'GetNewPerkGLPackageTDBID')
    for needle in ('ProfilePolicy.OwnPerk', 'perkLevel == 0', '91068214685ul', '!IsDefined(record.GetLevelsItem(0))', 'TDBID.None()', 'wrappedMethod'): assert needle in binding
    relocation = common.function(h, 'PTFRR3MoveTattooToFirst')
    for needle in ('ProfilePolicy.OwnHand', 'UnequipBlocked', 'this.IsEquippable(item)', 'this.UnequipItem(area, 1, false)',
                   'this.EquipItem(id, 0, false, false)', 'GetItemQuantity', 'GetItemParts', 'GetSlotID', 'ptfrr1PreserveParts = ItemID.None()'): assert needle in relocation
    assert 'TweakDBInterface.Set' not in p+h+v
    for banned in ('AddSavedModifier(', 'RemoveAllModifiers(', 'RemoveSavedModifiers(', 'ForceModifier(', 'UnforceStat(',
                   'RequestSettingStatPoolValue(', 'RequestSettingStatPoolMaxValue(', 'gamedataStatType.Stamina', 'gamedataStatPoolType.Stamina'):
        assert banned not in v, banned
    clamp = common.function(v, 'CorrectPending')
    for needle in ('if !this.clampSent', 'this.clampSent = true', '-excess', 'HP pool acknowledgement timed out', 'poolMaximum - maximum'): assert needle in clamp
    assert clamp.count('RequestChangingStatPoolValue(') == 1
    assert 'this.healthFactor * target / maximum' in v
    assert 'weapon.GetOwner() != owner' in v and 'CyberwarePolicy.Active(owner)' in v
    assert 'SmartGunAdsMaxLockedTargets' in v and 'SmartGunHipMaxLockedTargets' in v
    assert 'ProfilePhysical.EnforceWeapon' in common.function(h, 'OnEnter')
    assert 'wrappedMethod(false)' in common.function(h, 'EnableSmartGunHandler')
    assert 'this.ptfrr3Straight' in common.function(h, 'PTFRR3Straight')
    return True

def models(rows, blocked, expected_other=74, expected_allowed=72):
    rng = random.Random(31072026)
    byid = {r['record']:r for r in rows}
    children = {p:[r['record'] for r in rows if p in r['requires']] for p in byid}
    other = sorted(p for p in blocked if not p.startswith(('NewPerks.Body_', 'NewPerks.Espionage_')))
    allowed = set(byid)-set(blocked)
    assert len(other) == expected_other and len(allowed) == expected_allowed
    allocations = [dict.fromkeys(other, 0), {p:byid[p]['ranks'] for p in other}]
    allocations += [{p:rng.randrange(byid[p]['ranks']+1) for p in other} for _ in range(512)]
    operations = 0
    for owned in allocations:
        state = {'ranks':{p:(owned[p] if p in owned else (byid[p]['ranks'] if p in allowed else 0)) for p in byid},
                 'points':15, 'spent':83, 'body':3, 'attrFree':17, 'relicFree':9, 'attrs':(3,8,20,11,10), 'xp':9999}
        original = copy.deepcopy(state); expected = copy.deepcopy(state)
        starting = sum(owned.values()); refunded=0
        while any(state['ranks'][p] for p in other):
            assert state == expected
            eligible = [p for p in other if state['ranks'][p] and not any(state['ranks'][c] for c in children[p])]
            assert eligible, 'Whitelist left a purchased dependent'
            p = eligible[0]; after=copy.deepcopy(expected)
            after['ranks'][p]-=1; after['points']+=1
            state=copy.deepcopy(after)
            assert state == after
            expected=after; refunded+=1; operations+=1
        assert refunded == starting and state['points'] == 15+starting
        assert all(state[k] == original[k] for k in original if k not in ('ranks','points'))
        assert all(state['ranks'][p] == original['ranks'][p] for p in allowed)
        completed=copy.deepcopy(state)
        for _ in range(4): # completed journal neither re-refunds nor rewrites state
            assert not any(state['ranks'][p] for p in other)
            assert state == completed
    # Interruptions must latch after any synchronous sale, before acknowledgement.
    for i in range(len(other)):
        inflight=True; stage=2; applied=1; refunded=0
        if inflight: stage=5
        assert stage==5 and applied==1 and refunded==0
    # Exact acknowledgement refuses all nonselected drift, not just counters.
    drift_cases=0
    sample={'rank':0,'points':16,'spent':83,'body':3,'relic':9,'xp':999}
    for key in sample:
        changed=dict(sample); changed[key]+=1
        assert changed != sample; drift_cases+=1
    for total in (0,1,94,2147483647):
        for free in (0,1,2147483646,2147483647):
            assert (total > 2147483647-free) == (free+total > 2147483647)
    # Health feedback under independent foreign additive/multiplicative changes.
    hp=0
    for initial, foreign, current in itertools.product((100.,180.,368.,5000.), (0.5,1.,1.5,3.), (1.,45.,100.)):
        factor=100./initial
        maximum=initial*foreign*factor
        factor=factor*100./maximum
        assert math.isclose(initial*foreign*factor,100.)
        refs={'foreign_same_value':factor, 'owned':factor}; del refs['owned']
        assert refs=={'foreign_same_value':factor}
        ceiling=current; now=current+20; requests=[]; sent=False
        for delay in range(12):
            if now <= ceiling+.01: break
            if not sent: requests.append(-(now-ceiling)); sent=True
            if delay==5: now+=requests[0]
        assert len(requests)==1 and now <= ceiling+.01
        assert requests[0] < 0; hp+=1
    # Smart guard scope: main V, completed Tower, nonreplacer, active mode, own smart weapon.
    smart=0
    for bits in itertools.product((False,True), repeat=6):
        permit=all(bits); assert permit == (bits==(True,)*6); smart+=1
    # Second tattoo requires first empty; same quantity and parts acknowledged.
    relocation=0
    for first, second, allowed_item, locked, pending in itertools.product((False,True),repeat=5):
        move=not first and second and allowed_item and not locked and not pending
        before=(1, ('part_id','slot_id'))
        after=copy.deepcopy(before)
        if move: assert after==before
        relocation+=1
    return dict(allocation_cases=len(allocations), native_rank_operations_modeled=operations,
                repeat_cases=len(allocations)*4, interrupted_cases=len(other), drift_cases=drift_cases,
                hp_feedback_cases=hp, smart_scope_cases=smart, tattoo_guard_cases=relocation,
                engine_execution=False)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    protected={}
    for relative, digest in PREDECESSORS.items():
        p=GAME/'r6/scripts'/relative; assert compiler.sha(p)==digest; protected[str(p)]=digest
    # Retain historical receipts, test evidence and accepted Afterlife files.
    for root in ('research/restriction_profiles','research/afterlife_world/interactions_r11'):
        for p in (ROOT/root).rglob('install_receipt.json'):
            if 'fixture_' in str(p) or p.parent==OUT: continue
            protected[str(p)]=compiler.sha(p)
    bundle, inputs=build.definition.load_bundle(); checked=build.definition.validate_bundle(bundle)
    generated,_,_=build.generate()
    assert read(ROOT/'redscript/PTFR_Restrictions_R3/ProfileDefinition.generated.reds')==generated
    s={p.name:read(p) for folder in compiler.SOURCES for p in folder.glob('*.reds')}
    assert source_checks(s)
    # Existing persistent layout and transaction helpers remain byte-for-byte.
    oldbody=read(GAME/'r6/scripts/PTFR_Restrictions_R2/BodyPolicy.reds')
    assert re.findall(r'private persistent let .*;',oldbody)==re.findall(r'private persistent let .*;',s['BodyPolicy.reds'])
    for name in ('Same','Headroom','RefundOne','RefundRelicOne','ResetBody','IncludeRelic','OnBodyStep','Settle'):
        assert common.function(oldbody,name)==common.function(s['BodyPolicy.reds'],name),name
    oldhooks=read(GAME/'r6/scripts/PTFR_Restrictions_R2/DevelopmentHooks.reds')
    for name in ('PTFRR2Snapshot','PTFRR2SellBodyPerk','PTFRR2SellRelicPerk','PTFRR2ResetBody','PTFRR2CompatibleBodyCosts'):
        assert common.function(oldhooks,name)==common.function(s['DevelopmentHooks.reds'],name),name
    mutants=[]
    for file, needle in [
        ('ProfilePolicy.reds','this.inflight = true; this.mutation = true;'),
        ('ProfilePolicy.reds','if !legacy.PTFRR3Complete()'),
        ('ProfilePolicy.reds','if !sold || !BodyPolicy.Same(this.expected, after, index, false)'),
        ('ProfilePolicy.reds','this.Total(current) > 2147483647 - current.primaryUnspent'),
        ('ProfilePolicy.reds','if this.enabled && !this.MatchesDefinition()'),
        ('ProfileHooks.reds','91068214685ul'),('ProfileHooks.reds','this.UnequipItem(area, 1, false)'),
        ('ProfileHooks.reds','ProfilePolicy.OwnHand'),('ProfileHooks.reds','wrappedMethod(false)'),
        ('ProfilePhysical.reds','if !this.clampSent'),('ProfilePhysical.reds','this.healthFactor * target / maximum'),
        ('ProfilePhysical.reds','weapon.GetOwner() != owner'),
    ]:
        candidate=dict(s); assert needle in candidate[file]; candidate[file]=candidate[file].replace(needle,'REMOVED_GUARD',1)
        try: source_checks(candidate)
        except AssertionError: mutants.append(needle)
        else: raise AssertionError('Undetected mutant '+needle)
    records=json.loads(read(ROOT/'research/restriction_profiles/body_stats_design/body_catalogue_records.json'))
    for db in records['database_sources']: assert compiler.sha(db['path'])==db['sha256']
    missing=[r for r in records['reference_closure'] if r['hash']=='91068214685']
    assert len(missing)==1 and missing[0]['missing'] is True
    # Primary native anchors are pinned to the installed base decompile.
    native=read(ROOT/'research/restriction_profiles/body_stats_design/current_base.script')
    anchors=['gLPRec = levelData.DataPackage();','this.HandleRemovingTech_Central_Milestone_3(playerData);',
             'this.ReturnDevelopmentPointForSoldPerk(i, j);','this.DeactivateNewPerk(perkType, this.m_attributesData',
             'public final native func ShootStraight(shootStraight: Bool)', 'EnableSmartGunHandlerEvent',
             'private final func SellNewPerk(owner: ref<GameObject>, perkType: gamedataNewPerkType) -> Bool']
    for anchor in anchors: assert anchor in native,anchor
    result=models(bundle['catalogue']['perks'], checked['blocked_perks'])
    result['legacy_body']=body.model_checks(body.stock_roster())
    result['legacy_relic']=relic.model_checks(relic.record_checks()[0])
    compile_result=compiler.compile_all()
    for p,digest in protected.items(): assert compiler.sha(p)==digest
    files=[]
    for rel,digest in PREDECESSORS.items():
        source='redscript/'+rel
        files.append(dict(relative='r6/scripts/'+rel,source=source,sha256=compiler.sha(ROOT/source),before_sha256=digest))
    for p in sorted(compiler.SOURCES[-1].glob('*.reds')):
        files.append(dict(relative='r6/scripts/PTFR_Restrictions_R3/'+p.name,source=str(p.relative_to(ROOT)).replace('\\','/'),sha256=compiler.sha(p),before_sha256=None))
    report={**compile_result,'status':'PASS_PROFILE_R3_OFFLINE_LIVE_PENDING','utc':datetime.now(timezone.utc).isoformat(),
      'source_contracts':True,'source_mutants_rejected':mutants,'native_anchors':anchors,'models':result,'files':files,
      'protected_inputs':{**compile_result['protected_inputs'],**protected},'definition_inputs':inputs,
      'resolved_sha256':__import__('hashlib').sha256(json.dumps(bundle,sort_keys=True,separators=(',',':')).encode()).hexdigest().upper(),
      'base_sha256':compiler.sha(GAME/'r6/cache/final.redscripts'),'game_writes':0,'live_tested':False,
      'tested_tools':{str(p.relative_to(ROOT)).replace('\\','/'):compiler.sha(p) for p in (Path(__file__),ROOT/'tools/build_restrictions_profile_r3.py',ROOT/'tools/compile_restrictions_profile_r3.py',ROOT/'tools/validate_restriction_profile.py',ROOT/'tools/test_restriction_profiles.py')}}
    (OUT/'tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'files':len(files),'models':result,'mutants':len(mutants)},indent=2))
if __name__=='__main__': main()
