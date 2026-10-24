"""Bind current 2.5 perk validators; preserve selected policy and transactions."""
from pathlib import Path
import hashlib,json,re,shutil,importlib.util
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';P=C/'package'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
sp=importlib.util.spec_from_file_location('parse',W/'prealpha/history_snapshot_hs1/build_catalogue_01.py');parse=importlib.util.module_from_spec(sp);sp.loader.exec_module(parse)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
report=json.loads((C/'diagnosis_01/perks_current.json').read_text(encoding='utf-8-sig'))
for source in report['database_sources']:assert sha(Path(source['path']))==source['sha256']
rows={r['id']:r for r in report['records']};named={r['name']:r for r in rows.values() if r['name']}
old=json.loads((W/'research/restriction_profiles/body_stats_design/body_catalogue_records.json').read_text())
prior={int(r['hash']):r for r in old['records']+old['reference_closure']}
def flat(v):
 if isinstance(v,dict) and 'hash' in v:return int(v['hash'])
 if isinstance(v,list):return [flat(x) for x in v]
 return v
changes=[];same=0
for id,r in rows.items():
 if id not in prior:continue
 o=prior[id];assert r['missing']==bool(o.get('missing')),(id,'missing')
 for k,v in r['fields'].items():
  if k in o.get('fields',{}):
   if v!=flat(o['fields'][k]):changes.append((r['name'] or o.get('name') or id,k,flat(o['fields'][k]),v))
   else:same+=1
assert [(a,b) for a,b,*_ in changes]==[('NewPerks.Cool_Central_Milestone_3','requiresPerks'),('NewPerks.CoolAttributeData','perks')],changes
assert changes[0][3]==[]
enum=json.loads((C/'diagnosis_01/enum_change.json').read_text())
added=list(enum['added']);assert len(added)==5 and enum['new_count']==194 and not enum['removed']
assert {x for x in changes[1][3] if x not in changes[1][2]}=={named['NewPerks.'+n]['id'] for n in added}
# Existing selected removals stay exact. New Cool branch is retained, not silently banned.
profile=(G/'r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R3/ProfileDefinition.generated.reds').read_text(encoding='utf-8-sig')
blocked=set(re.findall(r'gamedataNewPerkType\.(\w+)',parse.body(profile,'OtherBlocked')))
blocked|={r['name'].removeprefix('NewPerks.') for r in named.values() if r['name'].startswith(('NewPerks.Body_','NewPerks.Espionage_'))}
for n in added:
 r=named['NewPerks.'+n];assert not r['missing'] and r['fields']['attribute']==named['NewPerks.CoolAttributeData']['id']
 assert all(rows[d]['name'].removeprefix('NewPerks.') not in blocked for d in r['fields']['requiresPerks'])
 assert all(not rows[d]['missing'] for d in r['fields']['levels'])
targets=[]
def put(target,s):
 src=G/target;before=C/'before'/target;dest=P/target
 before.parent.mkdir(parents=True,exist_ok=True);dest.parent.mkdir(parents=True,exist_ok=True)
 assert not before.exists();shutil.copyfile(src,before);dest.write_text(s,encoding='utf-8')
 targets.append({'target':target,'before':sha(src),'after':sha(dest)})
for f in ['BodyCatalogue.reds','RelicCatalogue.reds']:
 target='r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R2/'+f;s=(G/target).read_text(encoding='utf-8-sig')
 assert s.count('Count) != 189')==1
 s=s.replace('Count) != 189','Count) != 194').replace('all 189 enum records','all 194 current enum records')
 put(target,s)
profile=profile.replace('Count) != 189','Count) != 194').replace('treeCool.GetPerksCount() != 37','treeCool.GetPerksCount() != 42')
match=re.search(r'  private static func R\d+\(\) -> Bool \{\s*let record = RPGManager.GetNewPerkRecord\(gamedataNewPerkType.Cool_Central_Milestone_3\)',profile)
assert match
name=re.search(r'func (R\d+)',match[0])[1];body=parse.body(profile,name)
oldline='    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Central_Milestone_1" { return false; }\n'
assert oldline in body and 'ArraySize(deps) != 1' in body
newbody=body.replace('ArraySize(deps) != 1','ArraySize(deps) != 0').replace(oldline,'')
profile=profile.replace(body,newbody,1)
# Add exact record/level/dependency validators without rewriting the frozen profile policy.
methods=[]
for i,n in enumerate(added):
 r=named['NewPerks.'+n];f=r['fields'];levels=f['levels'];deps=f['requiresPerks'];tier=rows[f['tier']]['fields']['requiredAttributePoints']
 lines=[f'  private static func LC2NewCool{i}() -> Bool {{',f'    let record=RPGManager.GetNewPerkRecord(gamedataNewPerkType.{n});',
 f'    if !IsDefined(record) || record.GetID()!=t"NewPerks.{n}" || NotEquals(record.Type(),gamedataNewPerkType.{n}) || !IsDefined(record.Attribute()) || record.Attribute().GetID()!=t"NewPerks.CoolAttributeData" ||',
 f'      record.GetLevelsCount()!={len(levels)} || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints()!={tier} {{ return false; }}',
 '    let deps:array<wref<NewPerk_Record>>;record.RequiresPerks(deps);',f'    if ArraySize(deps)!={len(deps)} {{ return false; }}']
 for j,d in enumerate(deps):lines.append(f'    if !IsDefined(deps[{j}]) || deps[{j}].GetID()!=t"{rows[d]["name"]}" {{ return false; }}')
 lines+=['    let levels=TweakDBInterface.GetForeignKeyArray(record.GetID()+t".levels");',f'    if ArraySize(levels)!={len(levels)} {{ return false; }}']
 for j,l in enumerate(levels):lines.append(f'    if TDBID.ToNumber(levels[{j}])!={l}ul || !IsDefined(record.GetLevelsItem({j})) || TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[{j}]+t".dataPackage"))!={rows[l]["fields"]["dataPackage"]}ul {{ return false; }}')
 lines+=['    return true;','  }'];methods.append('\n'.join(lines))
body=parse.body(profile,'Valid');newbody=body.replace('    return true;', ''.join(f'    if !ProfileCatalogue.LC2NewCool{i}() {{ return false; }}\n' for i in range(5))+'    return true;')
profile=profile.replace(body,newbody,1);profile=profile.rstrip()[:-1]+'\n'+'\n'.join(methods)+'\n}\n'
profile=profile.replace('// Generated from profiles/; do not hand-edit. Build-time loader, not hot reload.','// Frozen profile policy retained. LC2 binds its catalogue checks to audited 2.5 records.\n// Reproduce with prealpha/loading_cover_lc2/prepare_01.py; no hot reload.')
put('r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R3/ProfileDefinition.generated.reds',profile)
put('r6/scripts/TowerContinued_Loading_LC1/StartupCoverLC1.reds',(H/'StartupCoverLC1.reds').read_text())
n=json.loads((C/'native_01.json').read_text(encoding='utf-8-sig'));targets.append({k:n[k] for k in ['target','before','after']})
(C/'changes_01.json').write_text(json.dumps(targets,indent=2)+'\n')
(C/'catalogue_binding_01.json').write_text(json.dumps({'status':'AUDITED_CURRENT_STOCK_NOT_LIVE','existing_fields_unchanged':same,'existing_field_changes':changes,'added_perks_retained':added,'policy_blocked_methods_unchanged':True,'database_sources':report['database_sources'],'old_saved_ledger_not_reindexed':True},indent=2)+'\n')
print(json.dumps({'files':len(targets),'existing_fields_unchanged':same,'existing_field_changes':len(changes),'added_perks_retained':added}))
