"""Check packed parent slices, native references and negative admission cases.

This is offline evidence, not a rendered interaction or reward/reload pass.
"""
import binascii, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'prealpha/ncpd_scanner_n1'),str(ROOT/'tools')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import read,sha,walk,value

def graphs(p):
 r=SafeResource(read(p));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def nodes(g):return {n['id']:n for n in g['nodes']}
def edges(g):return {tuple(e) for e in g['edges']}
def evaluate(c,f,j):
 if c['$type']=='questLogicalCondition':
  v=[evaluate(x,f,j) for x in c['conditions']];return all(v) if c['operation']=='AND' else any(v)
 t=c['type']
 if c['$type']=='questJournalCondition':return j.get(t['path']['realPath'])==t['state']
 assert c['$type']=='questFactsDBCondition'
 a=f.get(t['factName'],0);b=t['value']
 return {'Equal':a==b,'Greater':a>b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[t['comparisonType']]

def verify(build):
 m=read(build/'build.json');cfg=read(HERE/'admission.json')
 assert m['status']=='BUILT_S2_LIVE_PENDING'
 assert len(m['resources'])==2 and len(m['files'])==3 and len(m['boots'])==2
 assert m['packed_readback'] and m['native_scenes_unchanged'] and not m['official_overrides'] and m['runtime_scripts_added']==1
 assert [x['key'] for x in m['activities']]==['mq032_sacrum','mq008_party']
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
 for p,h in m['resources'].items():assert sha(build/'source'/p)==h,p
 for f in m['files']:assert sha(build/Path(f['relative']).name)==f['sha256']
 assert sha(build/'SideJobsS2.reds')==sha(HERE/'SideJobsS2.reds')
 parent=graphs(ROOT/(m['parent_source'].replace('/raw/','/json/')+'.json'))
 expected_specs=[([0,81,83,84,4],4,84,'Out1'),([0,81,83,84,54,86,80,55,70,73,62,59,47,176,29],29,176,'False')]
 copied=negatives=positive=0
 for row,job,spec in zip(m['activities'],cfg['jobs'],expected_specs):
  ids,child,last,port=spec;assert (row['selected_nodes'],row['child'],row['last'],row['port'])==spec
  out=graphs(build/'readback'/f"{row['key']}.json");orig=parent['root'];n=nodes(out['root'])
  assert set(n)==set(ids)|set(range(1000,1006))
  assert {i:n[i] for i in ids}=={i:nodes(orig)[i] for i in ids},'Original parent payload drift'
  selected={path:g for path,g in parent.items() if path!='root' and int(path.split('/')[1]) in ids}
  assert set(out)=={'root'}|set(selected)
  for path,g in selected.items():assert out[path]==g,(row['key'],path)
  copied+=len(ids)+sum(len(g['nodes']) for g in selected.values())
  wanted={e for e in edges(orig) if e[0] in ids and e[2] in ids and e[0]!=0 and not(e[0]==last and e[2]==child)}
  wanted|={(0,'Out',1000,'In'),(1000,'Out',1001,'In'),(1001,'Out',81,'In1'),(last,port,1002,'In'),(1002,'True',1003,'In'),(1002,'False',1005,'In'),(1003,'Out',child,'In1'),(child,'Out1',1004,'In')}
  assert edges(out['root'])==wanted
  assert not any(x['$type']=='questOutputNodeDefinition' for x in n.values()),'Do not cancel child cleanup'
  tag='PTFRS2_'+row['tag']
  for node,suffix in [(1000,'Ready'),(1003,'Issued'),(1004,'Finished'),(1005,'Refused')]:
   assert n[node]['type']=={'$type':'questSetVar_NodeType','factName':tag+'_'+suffix,'setExactValue':1,'value':1}
  expected=cfg['common_guards']|{tag+'_Permit':1,tag+'_Issued':0,tag+'_Finished':0,tag+'_Fault':0}|{f:0 for f in job['zero_facts']}
  assert row['guard_equal']==expected and row['journals']==job['journals'] and row['allowed_passive_fields']==job['allowed_passive_fields']
  c=n[1001]['condition'];assert c==n[1002]['condition']
  terms=[x['type'] for x in c['conditions'] if x['$type']=='questFactsDBCondition']
  expected_terms=[(k,'Equal',v) for k,v in expected.items()]
  expected_terms += [(f['name'],op,f[bound]) for f in job['allowed_passive_fields'] for op,bound in [('GreaterOrEqual','min'),('LessOrEqual','max')]]
  assert sorted((x['factName'],x['comparisonType'],x['value']) for x in terms)==sorted(expected_terms)
  jt=[x['type'] for x in c['conditions'] if x['$type']=='questJournalCondition']
  assert sorted((x['path']['realPath'],value(x['path']['className']),x['state'],x['inverted']) for x in jt)==sorted((x['path'],x['class'],'Inactive',0) for x in job['journals'])
  routes=[x for x in c['conditions'] if x['$type']=='questLogicalCondition'];assert len(routes)==1 and routes[0]['operation']=='OR'
  assert [(x['type']['factName'],x['type']['comparisonType'],x['type']['value']) for x in routes[0]['conditions']]==[(tag+'_AuthorizedRoute','Equal',1),(tag+'_AuthorizedRoute','Equal',2)]
  j={x['path']:'Inactive' for x in job['journals']};good=expected|{tag+'_AuthorizedRoute':1}|{f['name']:0 for f in job['allowed_passive_fields']}
  assert evaluate(c,good,j);positive+=1
  assert evaluate(c,good|{tag+'_AuthorizedRoute':2},j);positive+=1
  for k,v in expected.items():
   for wrong in [-1,0,1,2]:
    if wrong!=v:assert not evaluate(c,good|{k:wrong},j),(k,wrong);negatives+=1
  for wrong in [-1,0,3]:assert not evaluate(c,good|{tag+'_AuthorizedRoute':wrong},j);negatives+=1
  for p in j:
   for wrong in [None,'Active','Succeeded','Failed','Invalid']:
    assert not evaluate(c,good,j|{p:wrong}),(p,wrong);negatives+=1
  for f in job['allowed_passive_fields']:
   assert evaluate(c,good|{f['name']:1},j);positive+=1
   for wrong in [-1,2,999]:assert not evaluate(c,good|{f['name']:wrong},j);negatives+=1
  assert n[child]['phaseResource']['DepotPath']['$value']==row['native_depot']
  crc=binascii.crc_hqx((row['depot']+':1').encode(),0xffff)
  assert row['injection_id']==crc and crc not in [x['id'] for x in m['installed_injections']]
  assert (build/'TowerContinued_SideJobs_S2.archive.xl').read_text().count(row['depot'])==1
 assert len({x['injection_id'] for x in m['activities']})==2
 # Native parent gate payloads are not substituted with a synthetic unlock.
 pn=nodes(parent['root'])
 for i,f in [(54,'q001_done'),(80,'q005_done'),(55,'q101_enable_side_content')]:assert pn[i]['condition']['type']['factName']==f
 assert pn[176]['condition']['type']=={'$type':'questVarComparison_ConditionType','comparisonType':'GreaterOrEqual','factName':'mq008_done','value':1}
 resources={}
 for p,h in m['source_pins'].items():
  if p.startswith('research/sidejobs_s2/') and '/raw/' in p:
   depot=p.split('/raw/',1)[1].replace('/','\\');resources[depot]=ROOT/(p.replace('/raw/','/json/')+'.json')
 assert len(resources)==m['official_resource_count']
 # Extra regional/persistent roots are audit-only evidence, never booted or
 # claimed to be the executable closure of these two direct native owners.
 content={d:read(p) for d,p in resources.items() if '\\minor_quests\\mq032\\' in d or '\\minor_quests\\mq008\\' in d}
 refs={x['$value'] for obj in content.values() for x in walk(obj) if x.get('$type')=='ResourcePath' and x.get('$storage')=='string' and x.get('$value','').endswith(('.questphase','.scene','.community'))}
 assert not(refs-set(resources)),refs-set(resources)
 scenes={d:obj['Data']['RootChunk'] for d,obj in content.items() if d.endswith('.scene')}
 assert len(scenes)==5
 assert len([d for d in content if d.endswith('.questphase')])==9
 for depot,obj in scenes.items():
  text=json.dumps(obj).lower()
  for name in ['panam','kerry','judy']:assert name not in text,(depot,name)
  if '\\mq008\\' in depot:assert 'silverhand' not in text and 'johnny' not in text
  else:
   assert 'silverhand' in text and 'johnny' in text
   assert not obj.get('props',[]),'Check Johnny props separately if native source changes'
 # No scene edits or new presentation suppression; existing JV1 is byte-exact.
 jv=ROOT/'prealpha/build/20261013T021845834Z/package/r6/scripts/PTFR_PreAlpha/PTFR_JohnnyVoiceJV1/JohnnyVoiceJV1.reds'
 live=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/r6/scripts/PTFR_PreAlpha/PTFR_JohnnyVoiceJV1/JohnnyVoiceJV1.reds')
 assert sha(jv)==sha(live)
 policy=subprocess.run([sys.executable,str(HERE/'test_policy.py')],capture_output=True,text=True,check=True)
 pr=json.loads(policy.stdout);assert pr['status']=='PASS'
 return {'status':'PASS_NOT_LIVE','build_sha256':sha(build/'build.json'),'tester_sha256':sha(Path(__file__)),'copied_parent_nodes':copied,'native_resources':len(resources),'native_scenes_unchanged':len(scenes),'negative_admissions':negatives,'positive_admissions':positive,'policy':pr,'johnny_policy_sha256':sha(jv),'not_proven':['live dialogue and voice-only rendering','interaction/gameplay/rewards','queued-admission save/reload ordering','fresh ending','all whitelist side jobs']}

if __name__=='__main__':
 build=Path(sys.argv[1]);dest=build/'tests.json';assert not dest.exists(),'Evidence pinned'
 result=verify(build);dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
