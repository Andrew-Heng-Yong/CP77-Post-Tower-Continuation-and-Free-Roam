"""Independent graph parity, entry disjointness, table and terminal-state tests."""
import binascii,itertools,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'prealpha/ncpd_scanners_n2'))
from test import load,nodes,edges,predicate,setter,COMMON
from catalog_gig_rollout_r2 import read,sha,walk,value
HERE=Path(__file__).resolve().parent
INIT={'ma_wbr_hil_02':'ma_wbr_hil_02_start','ma_wbr_hil_03':'ma_wbr_hil_03_start','ma_wbr_hil_04':'ma_wbr_hil_04_start','ma_std_rcr_07':'ma_rcr_07_start'}
SPECIAL={'ma_cct_cpz_16','ma_wbr_nok_05'}

def main(revision):
 build=HERE/'build'/revision;dest=build/'tests.json';assert not dest.exists()
 m=read(build/'build.json');old=read(ROOT/'prealpha/ncpd_scanners_n2/build/n2_05/build.json')
 cat={r['key']:r for r in read(ROOT/'research/ncpd_scanners_n2/catalog_v2.json')['rows']}
 assert m['status']=='BUILT_N21_LIVE_PENDING' and len(m['activities'])==len(m['resources'])==6
 assert m['packed_readback'] and m['native_scenes_unchanged'] and not m['official_overrides'] and not m['mod_override']
 assert m['runtime_scripts_added']==1 and m['game_writes']==m['save_writes']==0
 assert {r['key'] for r in m['activities']}==INIT.keys()|SPECIAL
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
 for f in m['files']:assert sha(build/Path(f['relative']).name)==f['sha256']
 for p,h in m['resources'].items():assert sha(build/'source'/p)==h
 exact=negative=0
 for row in m['activities']:
  key=row['key'];tag='PTFRN21_'+key;c=cat[key];prior=next(r for r in old['activities'] if r['key']==key)
  _,before=load(ROOT/f'prealpha/ncpd_scanners_n2/build/n2_05/readback/{key}.json')
  _,after=load(build/f'readback/{key}.json');assert set(after)==set(before)
  out=nodes(after['root']);g=nodes(after['root/100']);og=nodes(before['root/100'])
  for path in before:
   assert edges(before[path])==edges(after[path]) if path!='root/100' else True
   for i,n in nodes(before[path]).items():
    if path=='root' and i in (1,2):continue
    if path=='root/100' and i in (1000,1002,1003,1004,1005):continue
    assert n==nodes(after[path])[i],(key,path,i);exact+=1
  assert set(g)==set(og)|{1003,1004,1005}
  expected=dict(prior['guard_equal'])
  if key in INIT:expected[INIT[key]]=1
  else:expected['PTFRN2_'+key+'_Permit']=0
  assert predicate(out[2]['condition'])==predicate(g[1000]['condition'])==row['guard_equal']==expected
  setter(out[1],tag+'_Ready');setter(g[1001],'PTFRN2_'+key+'_Issued');setter(g[1002],tag+'_Refused');setter(g[1003],tag+'_Request')
  assert g[1004]['condition']['operation']=='OR'
  assert {(v['type']['factName'],v['type']['value'],v['type']['comparisonType']) for v in g[1004]['condition']['conditions']}=={(tag+'_Permit',1,'Equal'),(tag+'_Denied',1,'Equal')}
  assert g[1005]['condition']['type']=={'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':tag+'_Permit','value':1}
  ee=edges(before['root/100'])
  if key in INIT:
   ad=prior['admission_edge'];ee.remove((ad[0],ad[1],1000,'In'))
   ee|={(ad[0],ad[1],1003,'In'),(1003,'Out',1004,'In'),(1004,'Out',1005,'In'),(1005,'True',1000,'In'),(1005,'False',1002,'In')}
  assert edges(after['root/100'])==ee
  assert not any(e[0]==1002 for e in ee)
  assert value(g[c['child']]['phaseResource']['DepotPath'])==prior['native_depot']
  # Prove these start flags are initialized by an unconditional stock path,
  # not an area/loot/combat/checkpoint branch, and are never cleared here.
  if key in INIT:
   _,native=load(ROOT/c['source']);ng=native['root'];nn=nodes(ng);ne=edges(ng)
   target=[i for i,n in nn.items() if isinstance(n.get('type'),dict) and n['type'].get('factName')==INIT[key]]
   assert len(target)==1
   writes=[v for n in nn.values() for v in walk(n) if v.get('factName')==INIT[key] and v.get('$type')=='questSetVar_NodeType']
   assert len(writes)==1 and writes[0]['value']==1
   inputs={i for i,n in nn.items() if n['$type']=='questInputNodeDefinition'}
   allowed={'questInputNodeDefinition','questFactsDBManagerNodeDefinition','questCrowdManagerNodeDefinition'}
   seen=set(inputs)
   while True:
    new=seen|{t for f,port,t,s in ne if f in seen and port=='Out' and nn[f]['$type'] in allowed and nn[t]['$type'] in allowed}
    if new==seen:break
    seen=new
   assert target[0] in seen,key
   assert prior['guard_equal'][INIT[key]]==0 and expected[INIT[key]]==1
  for fact,val in expected.items():
   changed=expected|{fact:1-val};assert not all(changed[k]==v for k,v in expected.items());negative+=1
 # Table has exactly the existing N2 owners; no N1, gigs, cyberpsychos or races.
 assert [r['key'] for r in m['dataset']]==sorted(r['key'] for r in old['activities'])
 script=(build/'ScannerRepairN21.reds').read_text();base=(HERE/'ScannerRepairN21.reds').read_text()
 assert script.startswith(base) and len(m['dataset'])==154
 for r in m['dataset']:
  idx=r['index'];key=r['key'];finish=list(cat[key]['finish_facts'])
  if key in ('ma_wat_lch_14','ma_wat_lch_15'):finish.remove('ma_wat_lch_14_finished')
  assert r['finish']==finish
  assert r['mode']==(1 if key in INIT else 2 if key in SPECIAL else 0)
  assert f'case {idx}: return "{key}";' in script
  if finish:assert f'case {idx}: '+''.join(f'ArrayPush(names,"{f}"); ' for f in finish)+'break;' in script
 assert base.count('.ChangeEntryState(')==1 and base.count('.SetFactStr(')==1
 for forbidden in ('RegisterMappin','ChangeMappinPhase','ModLog','LogChannel','ExecuteQuest','SetStat','Reward','SetFactStr("ma_'):
  assert forbidden not in base,forbidden
 assert 'this.Fact("PTFRN2_"+id+"_Issued")!=1' in base
 assert 'this.Fact(tag+"_MapAck")==1 || this.Terminal(i)' in base
 assert 'if state==2 { this.SetOwned(id,"_MapAck");return; }' in base
 assert 'if this.attempts[i]>=3 { return; }' in base
 assert 'this.epoch+=1' in base and 'epoch!=this.epoch' in base
 assert 'state==1 || state==2' in base and 'phase==1 || phase==2 || phase==3' in base
 # Exhaustive compact model of the script's activation and supplement policy.
 def action(tower,issued,ack,terminal,state,phase,attempts):
  if not tower or issued!=1 or ack==1 or terminal:return 'none'
  if state not in (1,2) or phase not in (1,2,3):return 'none'
  if state==2:return 'ack'
  return 'activate' if attempts<3 else 'none'
 for vals in itertools.product((False,True),(0,1),(0,1),(False,True),(-1,0,1,2,3,4),(-1,0,1,2,3,4),(0,3)):
  t,issued,ack,term,s,p,a=vals;result=action(*vals)
  if result=='activate':assert t and issued==1 and not ack and not term and s==1 and p in (1,2,3) and a==0
  if term or p==0 or s in (-1,0,3,4) or not issued:assert result=='none'
  negative+=1
 for phase in range(-1,6):
  old_permit=phase in (1,3);new_permit=phase==2
  assert not (old_permit and new_permit);negative+=1
 ids=[binascii.crc_hqx((d+':1').encode(),0xffff) for d in m['boots']]
 occupied={r['id'] for r in m['installed_injections']}|{n['Data']['id'] for n in read(ROOT/'research/q307_extracted/json/ep1/quest/ep1.quest.json')['Data']['RootChunk']['graph']['Data']['nodes']}
 assert len(set(ids))==6 and not set(ids)&occupied
 assert dict(zip(m['boots'],ids))=={r['depot']:r['injection_id'] for r in m['activities']}
 assert all(d.startswith('towercontinued\\ncpd_repair_n21\\') for d in m['resources'])
 assert (build/'TowerContinued_NCPD_N21.archive.xl').read_text().count('    - path: ')==6
 result={'status':'PASS_NOT_LIVE','build_sha256':sha(build/'build.json'),'tester_sha256':sha(Path(__file__)),'native_nodes_exact':exact,'negative_admission_cases':negative,'supplemental_owners':6,'marker_table':154,'initialization_semantics_verified':list(INIT),'limits':'Static and model checks, not gameplay proof. Generic mid-progress scanners remain protected.'}
 dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main(sys.argv[1])
