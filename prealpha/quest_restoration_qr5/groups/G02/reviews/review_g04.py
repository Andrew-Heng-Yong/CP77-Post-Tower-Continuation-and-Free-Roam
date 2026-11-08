"""Independent G04 source review. Does not import G04/root verification code."""
from pathlib import Path
import argparse,collections,copy,json,sys
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent));import source_inputs as I
from common import read,write,sha,walk
from model import Resource
def adapt(x):
 x=copy.deepcopy(x)
 for a in walk(x):
  a.pop('payload_sha256',None)
  if isinstance(a.get('phaseResource'),dict) and a['phaseResource'].get('Flags')=='Embedded':a['phaseResource']['Flags']='Soft'
  if a.get('cookingPlatform')=='PLATFORM_None':a['cookingPlatform']='PLATFORM_PC'
 return x
def run(O):
 assert not O.exists();tests=[];pins=[];M={};Q=['sts_std_arr_10','sts_std_arr_12','sts_std_arr_11'];recipes=[r for r in I.U['recipes'] if r.get('id') in Q]
 def ck(name,ok,e=None):tests.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e));assert ok,(name,e)
 def load(d):
  if d not in M:m,p=I.load(d);M[d]=m;pins.append(p);ck('exact source '+d,not m['errors'],p)
  return M[d]
 for r in recipes:
  d=r['depot'];cur=load(d);don=load('recipe:'+r['raw']);gp='root/10' if r['kind']=='entry' and r['id']=='sts_std_arr_12' else 'root';cg=cur['graphs'][gp];ng=don['graphs'][r['graph']]
  for i in r['ids']:
   if i==0:continue
   ck('actual native recipe node/socket '+d+str(i),adapt(cg['nodes'][str(i)]['payload'])==adapt(ng['nodes'][str(i)]['payload']) and cg['nodes'][str(i)]['sockets']==ng['nodes'][str(i)]['sockets'],dict(native=r['raw'],graph=r['graph'],node=i))
  ck('actual recipe exact edges '+d,collections.Counter(map(tuple,cg['edges']))==collections.Counter(tuple(map(str,e)) for e in r['edges']),cg['edges'])
  for p,g in cur['graphs'].items():
   if p.startswith(gp+'/'):ck('whole native copied inline '+d+p,g==don['graphs'][r['graph']+p[len(gp):]],p)
  if r.get('native'):load(r['native'])
 for d in list(M):
  if not d.startswith('recipe:'):continue
  for e in M[d]['embedded_files']:
   dep=e['depot']
   if not any('\\'+q+'\\' in dep for q in Q):continue
   try:cur=load(dep)
   except KeyError:continue
   pref=e['graph_prefix']+'/';aa={k[len(pref):]:adapt(v) for k,v in M[d]['graphs'].items() if k.startswith(pref)};bb={k:adapt(v) for k,v in cur['graphs'].items()};ck('independent native embedded graph/prefab parity '+dep,aa==bb and adapt(e['metadata'])==adapt(cur['metadata']),dict(donor=d,root_prefabs=e['root_prefabs']))
 parent=I.H.parent/'G04';results=read(parent/'results.json');rows=[];keys={'entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies'}
 for r in results['quest_results']:
  ck('frozen report contract hash '+r['quest_id'],sha(r['contracts'])==r['contracts_sha256'],r['contracts']);c=read(r['contracts']);ck('ten actual dispositions '+r['quest_id'],set(c['contracts'])==keys and not c['fully_static_verified'],{k:v['status'] for k,v in c['contracts'].items()});rows.append(dict(id=r['quest_id'],contracts=r['contracts'],sha256=sha(r['contracts']),statuses={k:v['status'] for k,v in c['contracts'].items()}))
 for q,tail,gp2,node in [('sts_std_arr_10','sts_std_arr_10_open_world.questphase','root/4',185),('sts_std_arr_11','sts_std_arr_11_openworld.questphase','root/2',73)]:
  d=next(d for d in I.MI if '\\'+q+'\\' in d and d.endswith(tail));g=load(d)['graphs'][gp2];ck('actual native timing '+q,g['nodes'][str(node)]['payload']['condition']['type']['seconds']==(3 if q.endswith('_10') else 5),dict(resource=d,graph=gp2,node=node))
  if q.endswith('_10'):ck('Severance auto SMS is native timed writer',all(list(map(str,e)) in g['edges'] for e in [(124,'Out',185,'In'),(185,'Out',200,'In'),(200,'Out',199,'Active'),(199,'Out',171,'In')]),g['nodes']['171']['writes'])
  else:ck('Hacking Hacker drop reward actual device acknowledgement',g['nodes']['71']['payload']['condition']['type']['deviceConditionFunction']['$value']=='IsRewardCollected' and ['74','CutSource','73','CutDestination'] in g['edges'],dict(node71=g['nodes']['71']['payload'],cut=[74,'CutSource',73,'CutDestination']))
 cp=parent/'shared_core.json';core=read(cp);ck('frozen Muamar core',sha(cp)=='E18670F1292E0AB60C325EFCA7151F46107E79B58769E9C6B4DAE7BA985142AC',str(cp))
 for p in core['sources']:ck('actual shared source still applicable '+p['depot'],sha(p['binary'])==p['sha256'] and sha(p['json'])==p['json_sha256'],p['binary'])
 arr=H/'ARR12_serialized/verification_02/review.json';ck('separate actual serialized ARR12 review linked',sha(arr)=='3575A51433D9CDB6D2916680E72CBCEB0B7B56721D2687C7C859CD6E8762DE60',str(arr))
 write(O/'source_pins.json',pins);write(O/'tests.json',dict(count=len(tests),checks=tests));out=dict(status='APPROVE_SOURCE_FINDINGS_WITH_EXPLICIT_EPOCH_AND_MODEL_LIMITS',group='G04',quests=rows,checks=len(tests),tests=str(O/'tests.json'),tests_sha256=sha(O/'tests.json'),source_pins=str(O/'source_pins.json'),source_pins_sha256=sha(O/'source_pins.json'),code_sha256=sha(__file__),source_epoch='QR5epoch00/QR4candidate; ARR12 after reviewed separately',actual_repairs_review=str(arr),actual_repairs_review_sha256=sha(arr),findings=['No independent contradiction found in exact native recipe/embedded body/source-specific timing/SMS/drop ACK claims.','ARR12 four FAIL dispositions correctly describe frozen epoch00; the serialized future-only fix is a separate explicitly pinned result, not grounds to rewrite frozen contracts.','G04 ev helper rejects absent scalar keys conservatively. This is an explicit fixture-presence policy, not engine semantics; independent ARR12 review uses absent0 and confirms positives provide provenance. No G04 test was interpreted as proof that missing expected0 is refused by engine.','World target contents/placement, saved owners and dynamic scheduling retain conditional/opaque/live bounds; static parity has not become gameplay success.'],runtime_writes=[]);write(H/'G04.json',out);print(json.dumps(dict(checks=len(tests),review=str(H/'G04.json'))))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);run(Path(p.parse_args().output).resolve())
