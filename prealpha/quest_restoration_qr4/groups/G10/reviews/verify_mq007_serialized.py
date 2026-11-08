"""Independent actual serialized MQ007 readback review; no root checker import."""
from pathlib import Path
import sys,json,copy,collections,argparse
W=Path(__file__).resolve().parents[5];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,reachable
CAP=H/'MQ007_serialized/readback_01';C=W/'prealpha/quest_restoration_qr4/candidate_01';PATCH=C/'repair_mq007/patch.json';PROPOSAL=H.parents[1]/'G08/regina_proposal_01/proposal.json';APPROVAL=H/'MQ007_followup_addendum.json'
def raw_root_edges(doc):
 """Separate direct handle/socket traversal, not model.normalize's edge code."""
 handles={str(x['HandleId']):x['Data'] for x in walk(doc) if 'HandleId'in x and 'Data'in x}
 def deref(h):
  if 'Data'in h:return h['Data']
  return handles[str(h['HandleRefId'])]
 def hid(h):return str(h.get('HandleId',h.get('HandleRefId')))
 root=deref(doc['Data']['RootChunk']['graph']);nodes={str(deref(h)['id']):deref(h) for h in root['nodes']};sockets={}
 for i,node in nodes.items():
  for h in node.get('sockets',[]):
   s=deref(h);sockets[hid(h)]=(i,value(s['name']))
 out=[];used=set()
 for i,node in nodes.items():
  for h in node.get('sockets',[]):
   for ch in deref(h).get('connections',[]):
    if hid(ch) in used:continue
    used.add(hid(ch));co=deref(ch);out.append([*sockets[hid(co['source'])],*sockets[hid(co['destination'])]])
 return sorted(out)
def evalguard(c,f):
 t=c['$type']
 if t=='questLogicalCondition':
  a=[evalguard(x,f) for x in c['conditions']];return all(a) if c['operation']=='AND' else any(a)
 if t=='questFactsDBCondition':return evalguard(c['type'],f)
 if t=='questVarComparison_ConditionType':
  if c['factName'] not in f:return False
  assert c['comparisonType']=='Equal';return f[c['factName']]==c['value']
 raise AssertionError(t)
def raw_phase(doc,ids):
 r=Resource(doc);g=r.d(r.root['graph']);node=None
 for i in ids:
  node=next(r.d(h) for h in g['nodes'] if r.d(h)['id']==i)
  if 'phaseGraph'in node:g=r.d(node['phaseGraph'])
 return r,node
def run(O):
 assert not O.exists();patch=read(PATCH);proposal=read(PROPOSAL);sources=read(CAP/'sources.json');M={};D={};checks=[];mutations=[];pins=[];details={}
 def check(name,ok,e):checks.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e));assert ok,name
 check('exact independent preimplementation approval',sha(APPROVAL)==patch['review_sha256'] and read(APPROVAL)['status']=='APPROVED_PREIMPLEMENTATION_FUTURE_EVENT_ONLY_PRESERVE_NATIVE_HELPER',dict(path=str(APPROVAL),sha256=sha(APPROVAL)))
 check('patch unchanged since independent binary export',sha(PATCH)==sources['patch_sha256'],str(PATCH))
 for p in sources['resources']:
  label=p['label'];check('actual serialized binary '+label,sha(p['binary'])==p['sha256'] and sha(p['json'])==p['json_sha256'],p);D[label]=read(p['json']);M[label]=Resource(D[label]).normalize();check('decoded readback '+label,not M[label]['errors'],M[label]['errors']);check('independent raw socket traversal '+label,raw_root_edges(D[label])==M[label]['graphs']['root']['edges'],label);pins.append(p)
  rootlabel='native_bugfix' if label=='native' else label
  rootjson=C/'repair_mq007'/(rootlabel+'.json');check('root reported JSON matches fresh independent binary readback '+label,M[label]==Resource(read(rootjson)).normalize(),str(rootjson))
 native=M['native'];native_outer=native['graphs']['root']['nodes']['14'];nativegraphs={gp:g for gp,g in native['graphs'].items() if gp=='root/14' or gp.startswith('root/14/')};expected_edges=[['1101','Out','1200','In'],['1200','True','1201','In'],['1201','Out','1202','In1'],['1202','Out1','1203','In']]
 def native_copy_ok(m,prefix):
  return all(prefix+gp[len('root/14'):] in m['graphs'] and m['graphs'][prefix+gp[len('root/14'):]]==g for gp,g in nativegraphs.items())
 check('actual native positive control',native_copy_ok(native,'root/14'),dict(binary=proposal['native_source']['binary'],native_graphs=list(nativegraphs)))
 for row in patch['resources']:
  tag=row['prefix'];before=M[tag+'_before'];after=M[tag+'_after'];bg=before['graphs']['root'];ag=after['graphs']['root'];prop=next(x for x in proposal['resources'] if x['resource']==row['depot']);actual_source=next(p for p in sources['resources'] if p['label']==tag+'_after')
  check('actual after bytes equal patch manifest '+tag,actual_source['sha256']==row['after'],row)
  check('old saved root node set plus only four IDs '+tag,set(ag['nodes'])==set(bg['nodes'])|{'1200','1201','1202','1203'},dict(before_nodes=list(bg['nodes']),added=sorted(set(ag['nodes'])-set(bg['nodes']))))
  for i,n in bg['nodes'].items():check('all original node fields sockets identities unchanged '+tag+':'+i,ag['nodes'][i]==n,dict(resource=row['depot'],node=i))
  check('all original edge multiplicities unchanged plus four additions '+tag,collections.Counter(map(tuple,ag['edges']))==collections.Counter(map(tuple,bg['edges']))+collections.Counter(map(tuple,expected_edges)),dict(added_edges=expected_edges))
  for gp,g in before['graphs'].items():
   if gp!='root':check('all old nested graphs unchanged '+tag+gp,after['graphs'][gp]==g,gp)
  check('only native14 graph trees added '+tag,set(after['graphs'])-set(before['graphs'])=={'root/1202','root/1202/3'},list(after['graphs']))
  for k in ['type','metadata','metadata_sha256','refs','root_prefabs','embedded_files']:
   # Root metadata has no graph; dependency refs can gain native world/quest
   # prefab refs only through the exact copied native14 below.
   if k=='refs':continue
   check('resource root metadata preserved '+tag+k,after[k]==before[k],k)
  expected=copy.deepcopy(native_outer);expected['id']='1202';expected['payload']['id']=1202
  node=ag['nodes']['1202'];check('outer copied phase identity differs only14to1202 '+tag,all(node[k]==expected[k] for k in node if k!='payload_sha256'),dict(native=native_outer['payload'],actual=node['payload']))
  check('baseline misses and repaired contains exact native continuation '+tag,not native_copy_ok(before,'root/1202') and native_copy_ok(after,'root/1202'),dict(before='EXPECTED_FAIL_MISSING_CONSUMER',after='PASS_EXACT_NATIVE14_GRAPH'))
  cond=ag['nodes']['1200']['payload']['condition'];want=prop['enrollment_guard']['facts_equal'];actual={x['factName']:x['value'] for x in ag['nodes']['1200']['reads']};check('guard is immediate condition not latent PauseCondition '+tag,ag['nodes']['1200']['type']=='questConditionNodeDefinition' and cond['operation']=='AND' and actual==want and len(ag['nodes']['1200']['reads'])==len(want) and all(x['comparisonType']=='Equal' for x in ag['nodes']['1200']['reads']),dict(actual=cond,expected=want))
  check('only actual1101 event enters enrollment '+tag,[e for e in ag['edges'] if e[2]=='1200']==[['1101','Out','1200','In']] and not [e for e in ag['edges'] if e[0]=='1200' and e[1]=='False'],dict(incoming=[e for e in ag['edges'] if e[2]=='1200'],false='no edge, no retry or native mutation'))
  def enroll(facts,event):return event and evalguard(cond,facts)
  check('actual supported future event accepted '+tag,enroll(want,True),want)
  check('old Entered facts without event never enroll '+tag,not enroll(want,False),dict(event=False,entered=1))
  for key in want:
   wrong=1-want[key];check('actual serialized guard negative '+tag+key,not enroll(want|{key:wrong},True) and not enroll({k:v for k,v in want.items() if k!=key},True),dict(fact=key,wrong=wrong,missing='unknown rejected'))
  check('single shared durable claim + owned finished writes only '+tag,ag['nodes']['1201']['writes']==[{'$type':'questSetVar_NodeType','factName':'PTFRQR4_MQ007_ReacquisitionIssued','setExactValue':1,'value':1}] and ag['nodes']['1203']['writes']==[{'$type':'questSetVar_NodeType','factName':'PTFRQR4_MQ007_ReacquisitionFinished','setExactValue':1,'value':1}],dict(claim=1201,finished=1203))
  check('no root terminator and sibling not story descendant '+tag,not any(n['type']=='questOutputNodeDefinition' for n in ag['nodes'].values()) and '1202' in reachable(ag['nodes'],[e for e in ag['edges'] if e[0]!='21' and e[2]!='21'],['1101']),dict(story_child=21,sibling=1202,root_outputs=[]))
  cg=after['graphs']['root/1202'];helper=cg['nodes']['3'];check('native helper retained; no container lease invented '+tag,helper['prefabs']==['#mq007_pr_gun_re_acquiring'] and not node['prefabs'] and all('#mq007_pr_gun_return' not in nn['prefabs'] for gp,g in after['graphs'].items() for nn in g['nodes'].values()),dict(native_helper=helper['payload'],outer_prefabs=node['prefabs']))
  check('actual five-day timer and post-return order '+tag,cg['nodes']['4']['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':5,'hours':0,'minutes':0,'seconds':0} and ['2','Out','4','In'] in cg['edges'] and ['4','Out','3','In1'] in cg['edges'],cg['edges'])
  check('all context SMS variant receipt native writes exact '+tag,after['graphs']['root/1202/3']==native['graphs']['root/14/3'] and cg['nodes']['5']['writes']==native['graphs']['root/14']['nodes']['5']['writes'],dict(subtree='root/1202/3',postreceipt='root/1202/5'))
  # Mutation controls operate on the actual independently exported serialized
  # resource, then re-run the decoder/independent invariant predicate.
  bad=copy.deepcopy(D[tag+'_after']);r,p=raw_phase(bad,[1202,3]);p['phaseInstancePrefabs']=[];bm=Resource(bad).normalize();det=not native_copy_ok(bm,'root/1202');mutations.append(dict(resource=tag,fault='drop actual nested native helper prefab',detected=det));check('raw helper omission mutation '+tag,det,mutations[-1])
  bad=copy.deepcopy(D[tag+'_after']);r,p=raw_phase(bad,[1202,4]);cc=r.d(p['condition']);target=next(x for x in walk(cc) if x.get('$type')=='questGameTimeDelay_ConditionType');target['days']=1;bm=Resource(bad).normalize();det=not native_copy_ok(bm,'root/1202');mutations.append(dict(resource=tag,fault='change actual timer5days to1',detected=det));check('raw timer mutation '+tag,det,mutations[-1])
  bad=copy.deepcopy(D[tag+'_after']);r,p=raw_phase(bad,[1200]);cc=r.d(p['condition']);cc['conditions']=[h for h in cc['conditions'] if not any(x.get('$type')=='questVarComparison_ConditionType' and x.get('factName')=='mq007_done' for x in walk(r.d(h)))];bm=Resource(bad).normalize();det=not any(x.get('factName')=='mq007_done' for x in bm['graphs']['root']['nodes']['1200']['reads']);mutations.append(dict(resource=tag,fault='remove actual done0 enrollment guard',detected=det));check('raw enrollment guard omission mutation '+tag,det,mutations[-1])
  details[tag]=dict(resource=row['depot'],before_sha256=row['before'],after_sha256=row['after'],all_old_nodes_preserved=len(bg['nodes']),all_old_nested_graphs_preserved=len(before['graphs'])-1,added_edges=expected_edges,copied_graphs=['root/1202','root/1202/3'],enrollment_guard=cond,native_helper='#mq007_pr_gun_re_acquiring',native_context_variant_messages=after['graphs']['root/1202/3'],limits=['Already-returned/previously-entered saves have no retroactive enrollment; no elapsed-time reconstruction.','Hierarchical survival and exact serialization are source/structure proofs; engine scheduler, save reload timer persistence, sector streaming and actual message/pickup delivery remain live-only.'])
 report=dict(status='APPROVED_SERIALIZED_TWO_RESOURCE_MQ007_SUCCESSOR_FOR_PACKAGE_VALIDATION',reviewer='qr4_worker_a',independent=True,root_checker_imported=False,checks=len(checks),tests=checks,mutations=mutations,source_pins=pins,patch=dict(path=str(PATCH),sha256=sha(PATCH)),preimplementation_review=dict(path=str(APPROVAL),sha256=sha(APPROVAL)),resources=details,scope='Only these exact two serialized resource hashes. Epoch00 predecessor evidence is retained; successor epoch/package not yet certified by this review.',approval=['Independent fresh WolvenKit9.1 readbacks of actual native, both predecessor resources and both successor resources match the root-provided JSON and pinned binary hashes.','All old root nodes/payloads/sockets, nested graphs and edge multiplicities are preserved, with only four approved new nodes and four edges per wrapper. Copied native14 subtree is exact, including helper lease, five days, outside-office/content gate, native variant/messages/receipt.','Immediate condition1200 is entered only by future1101. Shared claim precedes native continuation; old Entered facts alone, done1/reacquired1/claimed1, missing or changed prerequisites do not enroll. No root termination, retroactive timer polling, native resets, item/reward grants or invented container lease introduced.'],remaining=['Package/archive integrity, unchanged-payload preservation, exact global dependency/provider and generated-ID proof, compile/reproduction checks remain root candidate-validation gates.','Existing MQ007 native11/51/95 admission gap remains separate and unchanged. No full-quest or gameplay success claim.','Actual engine save/scene/timer scheduling and persistent world/loot pickup remain LIVE_ONLY/OPAQUE as preserved in the approved addendum.'],runtime_writes_by_reviewer=[],game_writes=0,save_writes=0)
 write(O/'review.json',report);return dict(status=report['status'],checks=len(checks),mutations=len(mutations),after_hashes={k:v['after_sha256'] for k,v in details.items()})
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();print(json.dumps(run(Path(a.output).resolve())))
