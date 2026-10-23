"""HP-only 150 profile revision; read-only game checks, offline models/compile."""
import copy, hashlib, itertools, json, math, re
from pathlib import Path
from datetime import datetime, timezone
import build_restrictions_profile_r3 as build
import compile_restrictions_profile_r3 as compiler
import test_restrictions_profile_r3 as original
from test_restrictions_r1 import function

ROOT, GAME = compiler.ROOT, compiler.GAME
OUT = ROOT/'research/restriction_profiles/profile_hp_r3_1'
OLD = '995DFBEA743A4FD89745DA7A5F880B033057D6AF470C57546C305E8DD17E31A1'
NEW = '117BF6C7A6E0FE29A4E64C7A0583DB9E3A9914D5FE8C42F82637D5D6DB8DE1E1'
def read(p): return Path(p).read_text(encoding='utf-8-sig')
def fingerprint(bundle): return hashlib.sha256(json.dumps(bundle,sort_keys=True,separators=(',',':')).encode()).hexdigest().upper()
def check_upgrade(text):
    f=function(text,'UpgradeHealthRevision')
    for condition in ('!this.enabled', 'this.inflight', 'this.stage < 1', 'this.stage > 4',
                      'this.revision != 1', 'this.healthTarget != 100.00', OLD, NEW,
                      'ProfileDefinition.Revision() != 2', 'ProfileDefinition.Health() != 150.00',
                      'ArraySize(selection) != ArraySize(this.blocked)', 'NotEquals(selection[i], this.blocked[i])'):
        assert condition in f,condition
    writes=re.findall(r'this\.(\w+)\s*=(?!=)',f)
    assert writes==['healthTarget','revision','fingerprint'],writes
    assert not any(x in f for x in ('SellNewPerk','ResetBody','QueueRequest','RequestSetting','RequestChanging','this.Apply('))
    restore=function(text,'Restored')
    assert restore.index('this.UpgradeHealthRevision();') < restore.index('if this.enabled && !this.MatchesDefinition()')
    return True
def model_checks():
    cases=0
    def upgrade(s):
        if not s['enabled'] or s['inflight'] or not 1<=s['stage']<=4: return
        if s['id']!='tower_strict' or s['rev']!=1 or s['hp']!=100 or s['hash']!=OLD or s['selection']!=(1,2,3): return
        s.update(hp=150,rev=2,hash=NEW)
    for stage,enabled,inflight,vitals,changed in itertools.product(range(6),(False,True),(False,True),(False,True),range(6)):
        s=dict(stage=stage,enabled=enabled,inflight=inflight,vitals=vitals,id='tower_strict',rev=1,hp=100,hash=OLD,
               selection=(1,2,3),refunded=12,starting=12,expected={'points':27,'xp':999},legacy_refunds=14)
        if changed==1:s['id']='other'
        if changed==2:s['rev']=7
        if changed==3:s['hp']=101
        if changed==4:s['hash']='unknown'
        if changed==5:s['selection']=(1,2,4)
        before=copy.deepcopy(s);upgrade(s)
        permitted=enabled and not inflight and 1<=stage<=4 and changed==0
        if permitted:
            assert (s['hp'],s['rev'],s['hash'])==(150,2,NEW)
            assert all(s[k]==v for k,v in before.items() if k not in ('hp','rev','hash'))
        else:assert s==before
        after=copy.deepcopy(s);upgrade(s);assert s==after
        cases+=1
    hp_cases=0
    for raw,foreign,current in itertools.product((80.,150.,368.,5000.),(.5,1.,1.5,3.),(1.,45.,100.,150.)):
        factor=100./raw;effective=raw*foreign*factor
        factor=factor*150./effective
        assert math.isclose(raw*foreign*factor,150.)
        # Native max growth can scale the pool. A single negative correction
        # preserves the prechange absolute ceiling, never refilling to 150.
        scaled=current*1.5;delta=-max(0.,scaled-current)
        assert delta<=0 and math.isclose(scaled+delta,current)
        hp_cases+=1
    return dict(saved_state_cases=cases,repeat_cases=cases,hp150_feedback_cases=hp_cases,engine_execution=False)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    previous=ROOT/'research/restriction_profiles/profile_r3'
    report=json.loads(read(previous/'tests.json'))
    protected={str(previous/n):compiler.sha(previous/n) for n in ('tests.json','install_receipt.json','deployment_tests.json')}
    for source,digest in report['checked_sources'].items():
        p=GAME/source.replace('redscript/','r6/scripts/');assert compiler.sha(p)==digest;protected[str(p)]=digest
    bundle,inputs=build.definition.load_bundle();assert fingerprint(bundle)==NEW
    prior=copy.deepcopy(bundle);prior['profile']['revision']=1;prior['vitals']['health']['value']=100
    assert fingerprint(prior)==OLD, 'Non-HP module changed'
    generated,_,checked=build.generate()
    src=ROOT/'redscript/PTFR_Restrictions_R3'
    assert read(src/'ProfileDefinition.generated.reds')==generated
    olddef=read(GAME/'r6/scripts/PTFR_Restrictions_R3/ProfileDefinition.generated.reds')
    normalized=generated.replace('return 2;','return 1;',1).replace(NEW,OLD).replace('return 150.000000;','return 100.000000;',1)
    assert normalized==olddef, 'Unrelated generated definition delta'
    policy=read(src/'ProfilePolicy.reds');assert check_upgrade(policy)
    helper='  private func UpgradeHealthRevision() -> Void {'+function(policy,'UpgradeHealthRevision')+'}\n'
    assert helper in policy
    normalized=policy.replace(helper,'',1).replace('    this.UpgradeHealthRevision();\n','',1)
    assert normalized==read(GAME/'r6/scripts/PTFR_Restrictions_R3/ProfilePolicy.reds'), 'Unrelated policy delta'
    changed={'redscript/PTFR_Restrictions_R3/'+n for n in ('ProfileDefinition.generated.reds','ProfilePolicy.reds')}
    for source,digest in report['checked_sources'].items():
        if source not in changed:assert compiler.sha(ROOT/source)==digest
    sources={p.name:read(p) for folder in compiler.SOURCES for p in folder.glob('*.reds')}
    assert original.source_checks(sources)
    mutants=[]
    for guard in ('!this.enabled','this.inflight','this.stage < 1','this.stage > 4','this.revision != 1',
                  'this.healthTarget != 100.00',OLD,NEW,'ArraySize(selection) != ArraySize(this.blocked)',
                  'NotEquals(selection[i], this.blocked[i])'):
        f=function(policy,'UpgradeHealthRevision'); altered=policy.replace(f,f.replace(guard,'REMOVED',1),1)
        try:check_upgrade(altered)
        except AssertionError:mutants.append(guard)
        else:raise AssertionError('Missing guard undetected: '+guard)
    models=model_checks()
    models['perk_regression']=original.models(bundle['catalogue']['perks'],checked['blocked_perks'])
    compiler.OUT=OUT;compiled=compiler.compile_all()
    flat=read(OUT/'compiled_flat.script')
    assert 'func UpgradeHealthRevision(' in flat
    definition_flat=flat[flat.index('class PTFR.RestrictionsR3.ProfileDefinition'):]
    assert float(re.search(r'return ([0-9.]+);',function(definition_flat,'Health'))[1])==150
    for p,digest in protected.items():assert compiler.sha(p)==digest
    files=[dict(source=s,relative=s.replace('redscript/','r6/scripts/'),before_sha256=report['checked_sources'][s],sha256=compiler.sha(ROOT/s)) for s in sorted(changed)]
    tested=[Path(__file__),ROOT/'tools/build_restrictions_profile_r3.py',ROOT/'tools/compile_restrictions_profile_r3.py',
            ROOT/'tools/validate_restriction_profile.py',ROOT/'tools/test_restriction_profiles.py',ROOT/'tools/test_restrictions_profile_r3.py']
    result={**compiled,'status':'PASS_PROFILE_HP_R3_1_OFFLINE_LIVE_PENDING','utc':datetime.now(timezone.utc).isoformat(),
            'source_contracts':True,'source_mutants_rejected':mutants,'models':models,'files':files,'definition_inputs':inputs,
            'resolved_sha256':NEW,'base_sha256':compiler.sha(GAME/'r6/cache/final.redscripts'),
            'protected_inputs':{**compiled['protected_inputs'],**protected},'game_writes':0,
            'tested_tools':{str(p.relative_to(ROOT)).replace('\\','/'):compiler.sha(p) for p in tested}}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],models=models,mutants=len(mutants)),indent=2))
if __name__=='__main__':main()
