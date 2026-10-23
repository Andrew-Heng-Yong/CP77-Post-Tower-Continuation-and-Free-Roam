"""N22 source-scope, frozen-data and negative-policy regression checks."""
import hashlib, itertools, json, re, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def methods(text):
 found={}
 for m in re.finditer(r'\bfunc\s+(\w+)\([^\n]*\)\s*->[^\n{]+\{',text):
  start=m.start();end=m.end();depth=1
  while depth:
   depth+=(text[end]=='{')-(text[end]=='}');end+=1
  found[m[1]]=text[start:end]
 return found
def main(revision):
 build=HERE/'build'/revision;dest=build/'tests.json';assert not dest.exists()
 manifest=read(build/'build.json')
 assert manifest['status']=='BUILT_N22_SCRIPT_REPAIR_LIVE_PENDING'
 assert manifest['relative']=='r6/scripts/TowerContinued_NCPD_N21/ScannerRepairN21.reds'
 assert manifest['old_sha256']=='B8B2182CA10EC1B5A4F5C82948FEEE15DD928B970E529D12781BADDC966E32BF'
 assert manifest['runtime_replacements']==1 and manifest['additions']==manifest['owners_changed']==manifest['archives_changed']==0
 assert manifest['supplemental_admission_changed'] is False and manifest['generated_table_unchanged'] is True
 for p,h in manifest['source_pins'].items():assert sha(ROOT/p)==h,p
 script=(build/'ScannerRepairN21.reds').read_text();assert sha(build/'ScannerRepairN21.reds')==manifest['sha256']
 old=(ROOT/'prealpha/ncpd_repair_n21/build/n21_01/ScannerRepairN21.reds').read_text()
 tag='public abstract class ScannerDataN21 {'
 assert script.split(tag)[1]==old.split(tag)[1]
 before=methods(old.split(tag)[0]);after=methods(script.split(tag)[0])
 assert set(after)-set(before)=={'CanRepairMissingRecord'} and not set(before)-set(after)
 changed={k for k in before if before[k]!=after[k]}
 assert changed=={'Phase','Activate','Inspect'},changed
 assert after['Permit']==before['Permit'] and after['Tower']==before['Tower'] and after['Terminal']==before['Terminal']
 assert after['Phase']==before['Phase'].replace('if !ms.GetPointOfInterestMappinSavedState', '// -1 means unavailable systems/entry/delayed journal; -2 means no saved record.\n    if !ms.GetPointOfInterestMappinSavedState').replace('phase,variant,active) { return -1; }','phase,variant,active) { return -2; }')
 assert after['Activate']==before['Activate'].replace('if !ScannerRepairN21.EligiblePOI(state,phase) { return; }','let finish=ScannerDataN21.Finish(i);\n    if !ScannerRepairN21.EligiblePOI(state,phase)\n      && !ScannerRepairN21.CanRepairMissingRecord(state,phase,ArraySize(finish)>0) { return; }')
 extra=after['CanRepairMissingRecord']
 expression=re.search(r'return (.+);',extra)[1]
 assert expression=='state==1 && phase==-2 && hasCompletionFacts'
 # Execute the extracted pure Boolean expression; no game code is executed.
 def missing(state,phase,hasCompletionFacts):
  return eval(expression.replace('&&','and'),{'__builtins__':{}},locals())
 cat={r['key']:r for r in read(ROOT/'research/ncpd_scanners_n2/catalog_v2.json')['rows']}
 prior=read(ROOT/'prealpha/ncpd_repair_n21/build/n21_01/build.json')
 assert manifest['dataset']==prior['dataset'] and len(manifest['dataset'])==154
 no_fallback=[];fact_checks=0
 for r in manifest['dataset']:
  if not r['finish']:no_fallback.append(r['key'])
  for f in r['finish']:
   writes=[w for w in cat[r['key']]['writes'] if w['factName']==f]
   assert writes and all(w['value']>0 for w in writes),(r['key'],f,writes)
   fact_checks+=len(writes)
 assert set(no_fallback)=={'ma_cct_cpz_16','ma_wat_lch_05','ma_wat_lch_14','ma_wat_lch_15','ma_wat_nid_14'}
 def action(tower,issued,ack,terminal,state,phase,hasCompletionFacts,attempts):
  if not tower or issued!=1 or ack==1 or terminal:return 'none'
  normal=state in (1,2) and phase in (1,2,3)
  if not normal and not missing(state,phase,hasCompletionFacts):return 'none'
  if state==2:return 'ack'
  return 'activate' if attempts<3 else 'none'
 cases=0;new_cases=0
 for args in itertools.product((False,True),(-1,0,1,2),(0,1,2),(False,True),range(-2,6),range(-2,6),(False,True),range(4)):
  t,issued,ack,term,s,p,has,a=args;result=action(*args)
  if not t or issued!=1 or ack==1 or term or s not in (1,2) or p in (-1,0,4,5):assert result=='none',args
  if result=='activate':assert t and issued==1 and ack!=1 and not term and s==1 and a<3 and (p in (1,2,3) or p==-2 and has)
  if p==-2 and result!='none':assert result=='activate' and s==1 and has;new_cases+=1
  if s==2 and p==-2:assert result=='none'
  if not has and p==-2:assert result=='none'
  cases+=1
 assert action(True,1,0,False,1,-2,True,0)=='activate'
 # Acknowledgement, reload, retry exhaustion and later completion regressions.
 assert action(True,1,0,False,2,2,True,1)=='ack'
 assert action(True,1,1,False,1,-2,True,0)=='none'
 assert action(True,1,0,False,1,-2,True,3)=='none'
 assert action(True,1,0,True,1,-2,True,0)=='none'
 assert 'ArrayClear(this.attempts);ArrayResize' in after['Restored']
 assert 'epoch!=this.epoch' in after['Poll'] and 'this.warmup>0' in after['Poll']
 assert script.count('.ChangeEntryState(')==script.count('.SetFactStr(')==1
 for token in ('RegisterMappin','ChangeMappinPhase','ModLog','LogChannel','ExecuteQuest','SetStat','SetFactStr("ma_'):
  assert token not in script,token
 # Saved evidence is not a runtime state decoder. Report its independent counts.
 live=read(ROOT/'research/ncpd_n21_live_20261014/assessment_01.json')
 assert sum(v['issued_1'] for v in live['summary'].values())==128
 assert sum(v['map_ack_1'] for v in live['summary'].values())==24
 result={'status':'PASS_NOT_LIVE','build_sha256':sha(build/'build.json'),'tester_sha256':sha(Path(__file__)),'policy_cases':cases,'new_missing_record_cases':new_cases,'native_positive_finish_writes_checked':fact_checks,'unchanged_methods':sorted(set(before)-changed),'changed_methods':sorted(changed),'generated_table_unchanged':True,'owners_unchanged':True,'no_missing_record_fallback':no_fallback,'limits':'Source and policy tests only; actual marker visibility and save/reload require game testing.'}
 dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main(sys.argv[1])
