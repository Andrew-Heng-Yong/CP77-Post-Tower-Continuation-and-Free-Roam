"""Implant-profile selection/migration tests; no engine or save execution."""
import copy, hashlib, itertools, json, random, re
from datetime import datetime, timezone
from pathlib import Path
import build_restrictions_profile_r3 as build
import compile_restrictions_profile_r3 as compiler
import test_restrictions_profile_r3 as original
from test_restrictions_r1 import function

ROOT, GAME = compiler.ROOT, compiler.GAME
OUT = ROOT / 'research/restriction_profiles/profile_implant_r3_2'
V1 = '995DFBEA743A4FD89745DA7A5F880B033057D6AF470C57546C305E8DD17E31A1'
V2 = '117BF6C7A6E0FE29A4E64C7A0583DB9E3A9914D5FE8C42F82637D5D6DB8DE1E1'
NEW = 'EA4423FBE8A6DF1A3977417061BB8E582522C4EA9DFACCA5BC92F3906EDFD7D0'

def read(path): return Path(path).read_text(encoding='utf-8-sig')
def fingerprint(bundle): return hashlib.sha256(json.dumps(bundle,sort_keys=True,separators=(',',':')).encode()).hexdigest().upper()

GUARDS = ('!this.enabled', 'this.inflight', 'this.stage < 1', 'this.stage > 4',
          'NotEquals(this.profileID, n"tower_strict")', 'this.revision == 1', 'this.healthTarget == 100.00',
          'this.revision == 2', 'this.healthTarget == 150.00', V1, V2, NEW, '!versionOne && !versionTwo',
          'NotEquals(ProfileDefinition.ID(), "tower_implant_focused")', 'ProfileDefinition.Revision() != 1',
          'ProfileDefinition.Health() != 150.00', 'ArraySize(previous) != ArraySize(this.blocked)',
          'NotEquals(previous[i], this.blocked[i])', 'ArraySize(selection) >= ArraySize(previous)',
          '!ArrayContains(previous, selection[i])')

def check_migration(text):
    f = function(text, 'UpgradeImplantProfile')
    for guard in GUARDS: assert guard in f, guard
    assert re.findall(r'this\.(\w+)\s*=(?!=)', f) == ['profileID','blocked','healthTarget','revision','fingerprint']
    for forbidden in ('SellNewPerk', 'BuyNewPerk', 'ResetBody', 'AddDevelopment', 'QueueRequest',
                      'RequestChanging', 'RequestSetting', 'this.Apply(', 'PTFRR3StartBodyRelic'):
        assert forbidden not in f, forbidden
    restore = function(text, 'Restored')
    assert restore.index('this.UpgradeImplantProfile();') < restore.index('if this.enabled && !this.MatchesDefinition()')
    assert 'if this.inflight { this.Fail(' in restore

def migration_models(rows, strict_blocked, new_blocked):
    old = tuple(sorted(p for p in strict_blocked if not p.startswith(('NewPerks.Body_', 'NewPerks.Espionage_'))))
    new = tuple(sorted(p for p in new_blocked if not p.startswith(('NewPerks.Body_', 'NewPerks.Espionage_'))))
    assert len(old)==74 and len(new)==53 and set(new)<set(old)
    def upgrade(s):
        if not s['enabled'] or s['inflight'] or not 1<=s['stage']<=4: return
        if s['id']!='tower_strict' or (s['rev'],s['hp'],s['hash']) not in ((1,100,V1),(2,150,V2)): return
        if s['selection']!=old: return
        s.update(id='tower_implant_focused',rev=1,hp=150,hash=NEW,selection=new)
    cases=0
    for stage,enabled,inflight,vitals,rev,changed in itertools.product(range(6),(False,True),(False,True),(False,True),(1,2),range(8)):
        s=dict(stage=stage,enabled=enabled,inflight=inflight,vitals=vitals,id='tower_strict',rev=rev,hp=100 if rev==1 else 150,
               hash=V1 if rev==1 else V2,selection=old,refunded=12,starting=87,expected={'points':27,'xp':999},legacy_refunds=14,handAttempted=True)
        if changed==1: s['id']='other'
        if changed==2: s['rev']=7
        if changed==3: s['hp']=101
        if changed==4: s['hash']='unknown'
        if changed==5: s['selection']=old[:-1]
        if changed==6: s['selection']=tuple(reversed(old))
        if changed==7: s['hash']=V2 if rev==1 else V1
        before=copy.deepcopy(s);upgrade(s)
        if enabled and not inflight and 1<=stage<=4 and changed==0:
            assert (s['id'],s['rev'],s['hp'],s['hash'],s['selection'])==('tower_implant_focused',1,150,NEW,new)
            assert all(s[k]==v for k,v in before.items() if k not in ('id','rev','hp','hash','selection'))
        else: assert s==before
        again=copy.deepcopy(s);upgrade(s);assert s==again
        cases+=1
    byid={r['record']:r for r in rows}
    children={p:[r['record'] for r in rows if p in r['requires']] for p in byid}
    rng=random.Random(8102026);operations=0;transitions=0
    # Switch at every position of several old-policy refund sequences.
    for trial in range(12):
        initial={p:(byid[p]['ranks'] if trial==0 else rng.randrange(byid[p]['ranks']+1)) for p in old}
        ranks={p:initial.get(p,0) for p in byid};prefix=[(copy.deepcopy(ranks),0)]
        while any(ranks[p] for p in old):
            leaf=next(p for p in old if ranks[p] and not any(ranks[c] for c in children[p]))
            ranks[leaf]-=1;prefix.append((copy.deepcopy(ranks),len(prefix)))
        for ranks,previous_refunds in prefix:
            before=copy.deepcopy(ranks);points=10+previous_refunds;new_refunds=0
            while any(ranks[p] for p in new):
                leaf=next(p for p in new if ranks[p] and not any(ranks[c] for c in children[p]))
                ranks[leaf]-=1;points+=1;new_refunds+=1;operations+=1
            assert new_refunds==sum(before[p] for p in new)
            assert points==10+previous_refunds+new_refunds
            assert all(ranks[p]==before[p] for p in byid if p not in new)
            # Newly allowed ranks may be repurchased after stage 4 without a repeat refund.
            for p in set(old)-set(new): ranks[p]=byid[p]['ranks']
            assert not any(ranks[p] for p in new)
            transitions+=1
    return dict(saved_state_cases=cases,repeat_cases=cases,partial_refund_transitions=transitions,
                post_switch_rank_operations=operations,engine_execution=False)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    previous=ROOT/'research/restriction_profiles/profile_hp_r3_1'
    report=json.loads(read(previous/'tests.json'))
    protected={str(previous/n):compiler.sha(previous/n) for n in ('tests.json','install_receipt.json','deployment_tests.json')}
    for source,digest in report['checked_sources'].items():
        p=GAME/source.replace('redscript/','r6/scripts/');assert compiler.sha(p)==digest;protected[str(p)]=digest
    for source,digest in report['definition_inputs'].items():
        assert compiler.sha(ROOT/source)==digest, 'Strict profile modified: '+source
        protected[str(ROOT/source)]=digest
    bundle,_=build.definition.load_bundle();assert fingerprint(bundle)==NEW
    strict,_=build.definition.load_bundle(build.definition.PROFILES/'tower_strict/profile.json');assert fingerprint(strict)==V2
    for module in ('vitals','nerf_rules','cyberware','catalogue'): assert bundle[module]==strict[module]
    generated,inputs,checked=build.generate()
    strict_checked=build.definition.validate_bundle(strict)
    assert checked['perk_counts']==dict(catalogue=188,allowed=93,blocked=95)
    audit=build.definition.read_json(ROOT/'research/restriction_profiles/body_stats_design/other_perk_policy.json')
    relaxed={p['record'] for p in audit['perks'] if p['classification'] in ('proposed_full_nerf','dependency_full_nerf')}
    assert set(strict_checked['blocked_perks'])-set(checked['blocked_perks'])==relaxed and len(relaxed)==21
    src=ROOT/'redscript/PTFR_Restrictions_R3'
    assert read(src/'ProfileDefinition.generated.reds')==generated
    olddef=read(GAME/'r6/scripts/PTFR_Restrictions_R3/ProfileDefinition.generated.reds')
    assert generated[generated.index('public abstract class ProfileCatalogue'):]==olddef[olddef.index('public abstract class ProfileCatalogue'):]
    assert function(generated,'PreviousStrictBlocked')==function(olddef,'OtherBlocked')
    policy=read(src/'ProfilePolicy.reds');check_migration(policy)
    oldpolicy=read(GAME/'r6/scripts/PTFR_Restrictions_R3/ProfilePolicy.reds')
    def strip(text,name):
        return text.replace('  private func '+name+'() -> Void {'+function(text,name)+'}\n','',1).replace('    this.'+name+'();\n','',1)
    assert strip(policy,'UpgradeImplantProfile')==strip(oldpolicy,'UpgradeHealthRevision'), 'Unrelated policy delta'
    changed={'redscript/PTFR_Restrictions_R3/'+n for n in ('ProfileDefinition.generated.reds','ProfilePolicy.reds')}
    for source,digest in report['checked_sources'].items():
        if source not in changed: assert compiler.sha(ROOT/source)==digest
    sources={p.name:read(p) for folder in compiler.SOURCES for p in folder.glob('*.reds')}
    assert original.source_checks(sources)
    mutants=[]
    for guard in GUARDS:
        f=function(policy,'UpgradeImplantProfile');altered=policy.replace(f,f.replace(guard,'REMOVED',1),1)
        try: check_migration(altered)
        except AssertionError: mutants.append(guard)
        else: raise AssertionError('Missing guard undetected: '+guard)
    models=migration_models(bundle['catalogue']['perks'],strict_checked['blocked_perks'],checked['blocked_perks'])
    models['new_perk_refunds']=original.models(bundle['catalogue']['perks'],checked['blocked_perks'],53,93)
    models['strict_regression']=original.models(strict['catalogue']['perks'],strict_checked['blocked_perks'])
    compiler.OUT=OUT;compiled=compiler.compile_all()
    flat=read(OUT/'compiled_flat.script');assert 'func UpgradeImplantProfile(' in flat
    df=flat[flat.index('class PTFR.RestrictionsR3.ProfileDefinition'):]
    assert NEW in function(df,'Fingerprint') and 'tower_implant_focused' in function(df,'ID')
    assert float(re.search(r'return ([0-9.]+);',function(df,'Health'))[1])==150
    for method,count in (('AllowedPerks',93),('OtherBlocked',53),('PreviousStrictBlocked',74)):
        assert function(df,method).count('ArrayPush(')==count,(method,count)
    for p,digest in protected.items(): assert compiler.sha(p)==digest
    files=[dict(source=s,relative=s.replace('redscript/','r6/scripts/'),before_sha256=report['checked_sources'][s],sha256=compiler.sha(ROOT/s)) for s in sorted(changed)]
    tested=[Path(__file__),ROOT/'tools/build_restrictions_profile_r3.py',ROOT/'tools/compile_restrictions_profile_r3.py',
            ROOT/'tools/validate_restriction_profile.py',ROOT/'tools/test_restriction_profiles.py',ROOT/'tools/test_restrictions_profile_r3.py']
    result={**compiled,'status':'PASS_PROFILE_IMPLANT_R3_2_OFFLINE_LIVE_PENDING','utc':datetime.now(timezone.utc).isoformat(),
            'source_contracts':True,'source_mutants_rejected':mutants,'models':models,'files':files,'definition_inputs':inputs,
            'resolved_sha256':NEW,'base_sha256':compiler.sha(GAME/'r6/cache/final.redscripts'),
            'protected_inputs':{**compiled['protected_inputs'],**protected},'game_writes':0,
            'tested_tools':{str(p.relative_to(ROOT)).replace('\\','/'):compiler.sha(p) for p in tested}}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],models=models,mutants=len(mutants)),indent=2))

if __name__=='__main__': main()
