"""Fresh QR8 four-depot/EP1 generated-ID and actual appended XL verifier."""
from inspect_archivexl import ROOT,HERE
import json,hashlib,binascii,collections,sys,struct,copy
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from model import Resource

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def plain(n):
 k=n['kind']
 if k=='scalar':return n.get('value')
 if k=='sequence':return [plain(x) for x in n['items']]
 if k=='mapping':
  entries=[(plain(x['key']),plain(x['value'])) for x in n['entries']]
  assert all(isinstance(k,str) for k,v in entries),'non-scalar key'
  assert len({k for k,v in entries})==len(entries),'duplicate key'
  return dict(entries)
 raise ValueError('Unsupported YAML AST '+str(k))
def fnv(s):
 a=0xcbf29ce484222325
 for b in s.encode():a=((a^b)*0x100000001b3)&0xffffffffffffffff
 return a
def crc(s):return binascii.crc_hqx(s.encode(),65535)
def parse(configs):
 scopes=collections.defaultdict(set);records=[];failures=[];classifications=[];docs={}
 for f in configs:
  try:
   assert f['parse_status']=='PARSED';assert len(f['documents'])<=1,'multiple documents'
   d=plain(f['documents'][0]) if f['documents'] else {};d={} if d is None else d
   assert isinstance(d,dict),'root not mapping';docs[f['path']]=d
   meta=d.get('resource',{});assert isinstance(meta,dict),'resource not mapping'
   ss=meta.get('scope',{});assert isinstance(ss,dict),'scope not mapping'
   for alias,values in ss.items():
    values=[values] if isinstance(values,str) else values
    assert isinstance(values,list) and all(isinstance(v,str) for v in values),'scope value shape'
    scopes[alias].update(v for v in values if v!=alias)
   q=d.get('quest');n=0
   if q is not None:
    assert isinstance(q,dict) and not set(q)-{'phases'},'quest section shape'
    phases=q.get('phases',[]);assert isinstance(phases,list),'quest phases not sequence'
    for i,p in enumerate(phases):
     assert isinstance(p,dict) and not set(p)-{'path','parent','connection','input','output','intercept'},'phase shape'
     assert isinstance(p.get('path'),str) and isinstance(p.get('parent'),str),'phase path/parent shape'
     node=[];socket=None
     for key in ['connection','input','output']:
      if key not in p:continue
      connection=p[key]
      if isinstance(connection,list):ns=connection;so=None
      else:
       assert isinstance(connection,dict) and not set(connection)-{'node','socket'},'connection shape'
       ns=connection.get('node');so=connection.get('socket')
      assert isinstance(ns,list) and all(isinstance(s,str) and s.isdecimal() and int(s)<=65535 for s in ns),'node path shape'
      assert so is None or isinstance(so,str),'socket shape'
      if key!='output':node=list(map(int,ns));socket=so
     records.append({'path':p['path'],'parent':p['parent'],'node':node,'socket':socket,'source':f['path'],'candidate':f['candidate'],'ordinal':i});n+=1
   classifications.append({'source':f['path'],'phases':n,'has_scope':bool(ss),'classification':'QUEST_PHASES' if q is not None else 'NO_QUEST'})
  except (AssertionError,ValueError,KeyError,TypeError) as ex:failures.append({'source':f['path'],'error':str(ex)})
 def expand(p,seen=frozenset()):
  assert p not in seen,'scope cycle'
  return {v for q in scopes[p] for v in expand(q,seen|{p})} if scopes[p] else {p}
 for r in records:
  try:r['expanded_parents']=sorted(expand(r['parent']))
  except AssertionError as ex:failures.append({'source':r['source'],'error':str(ex)})
 return docs,records,classifications,failures

def main():
 out=HERE/'namespace_verification_01';out.mkdir(exist_ok=False);I=load(HERE/'namespace_capture_01/manifest.json');checks=[]
 def ck(n,b,e=None):
  checks.append({'name':n,'pass':bool(b),'evidence':e});assert b,n
 target=r'ep1\quest\ep1.quest';owner=r'towercontinued\quest_restoration_qr7\ronald_news_future.questphase';block=r'towercontinued\quest_restoration_qr7\ronald_news_markers.streamingblock'
 ck('all captured indexes read without failure',all(a['read_status']=='NoError' for a in I['archive_index_inventory']))
 ck('expanded scope includes ArchiveXL Bundle and ModSettings plugin providers',all(any(s in a['path'] for a in I['archive_index_inventory']) for s in ['ArchiveXL\\Bundle\\ArchiveXL.archive','mod_settings\\ModSettings.archive']))
 for f in I['xl_configs']:ck('XL SHA stable '+f['path'],sha(__import__('pathlib').Path(f['path']))==f['sha256'])
 D,R,C,F=parse(I['xl_configs']);ck('no unsupported YAML shape skipped',not F,F)
 cand=next(f for f in I['xl_configs'] if f['candidate']);inst=next(f for f in I['xl_configs'] if not f['candidate'] and f['path'].endswith('zzzz_PTFR_Combined.archive.xl'))
 cd=D[cand['path']];base=D[inst['path']]
 old=load(ROOT/'prealpha/quest_restoration_qr7/worker_a/ronald_namespace_inputs_01/manifest.json');previous=next(f for f in old['xl_configs'] if f['candidate']);before=plain(previous['documents'][0])
 expected=copy.deepcopy(before);expected['quest']['phases'].append({'path':owner,'parent':target,'input':{'node':['1'],'socket':'Out'}});expected['streaming']['blocks'].append(block)
 ck('final staged XL equals entire prior tree plus only two approved appends',expected==cd)
 ck('same installed counterpart replacement preserves existing source order',before['quest']['phases']==cd['quest']['phases'][:-1])
 targetrows=[r for r in R if target in r['expanded_parents']];effective=[r for r in targetrows if r['candidate'] or r['source']!=inst['path']]
 parent=next(h for h in I['matching_providers'] if h['depot']==target);pm=Resource(load(__import__('pathlib').Path(parent['json']))).normalize();g=pm['graphs']['root'];native=set(map(int,g['nodes']))
 ck('exact native parent raw/hash freshly read',sha(__import__('pathlib').Path(parent['raw']))==parent['raw_sha256']=='A7021A4BF056C48DBDDE4C526E5C6462E7F71B5307861875000B100598048632')
 ck('native start1 Out resolves',g['nodes']['1']['type']=='questStartNodeDefinition' and {'name':'Out','type':'Output'} in g['nodes']['1']['sockets'])
 groups=collections.defaultdict(list)
 for r in effective:
  ck('supported root input '+r['path'],r['node'] in [[],[1]])
  r['generated_id']=crc(r['path']+':1');groups[r['generated_id']].append(r['path'])
 ck('every effective target-root generated ID unique',all(len(v)==1 for v in groups.values()))
 ck('every generated ID clear of native graph',not native&set(groups))
 new=[r for r in effective if r['path']==owner];ck('new exact registration sole owner19913',len(new)==1 and new[0]['generated_id']==19913 and new[0]['node']==[1] and new[0]['socket']=='Out')
 selected=I['depots'][:-1];providers=[]
 for d in selected:
  hs=[h for h in I['matching_providers'] if h['depot']==d]
  ck('no current on-disk provider competes with new depot '+d,len(hs)==1 and hs[0]['candidate'])
  h=hs[0];source=ROOT/'prealpha/quest_restoration_qr7/candidate_01/archive_source'/d.replace('\\','/')
  ck('fresh staged archive payload equals canonical source '+d,sha(source)==h['raw_sha256']==sha(__import__('pathlib').Path(h['raw'])))
  providers.append({'depot':d,'fnv64':fnv(d),'current_installed_resolution':'ABSENT','staged_successor_resolution':h['provider'],'payload_sha256':h['raw_sha256']})
 # Mutations use actual final YAML AST/tree, not an invented registration fixture.
 bad=copy.deepcopy(I['xl_configs']);bc=next(x for x in bad if x['candidate']);q=next(x['value'] for x in bc['documents'][0]['entries'] if x['key']['value']=='quest');next(x['value'] for x in q['entries'] if x['key']['value']=='phases')['kind']='scalar'
 ck('unsupported actual quest-YAML mutation rejected',bool(parse(bad)[3]))
 mutant=copy.deepcopy(effective);mutant.append(copy.deepcopy(new[0]));ck('duplicate actual phase-ID mutation rejected',len({r['generated_id'] for r in mutant})!=len(mutant))
 result={'status':'PASS_BOUNDED_STATIC_REGISTRATION_NAMESPACE_AND_PROVIDER_UNIQUENESS','checks':len(checks),'archive_index_count':len(I['archive_index_inventory']),'XL_file_count':len(I['xl_configs']),'all_parsed_phase_additions':len(R),'effective_target_root_registrations':len(effective),'native_root_ids':sorted(native),'new_generated_id':19913,'providers':providers,'unsupported_YAML':F,'controls':2,'limits':['All on-disk archives form a conservative collision superset; storage archives are explicitly not asserted to execute. Runtime ResourceDepot group registrations can only be observed live.','QR7 is staged, not installed: its three new resources are correctly absent from the current game. Unique staged provider makes relative precedence immaterial for those three keys.','Root baseline verifies canonical archive SHA; this targeted run reads every queried index and SHA-checks extracted payloads, using stable size/mtime for large source containers rather than hashing entire native archives.','No full world-global namespace census: two private marker identities are source/readback checked under QR7 peer evidence; arbitrary external world-global collisions remain unexcluded.'],'source_capture':str(HERE/'namespace_capture_01/manifest.json'),'source_capture_sha256':sha(HERE/'namespace_capture_01/manifest.json'),'runtime_writes':0}
 for name,data in [('result.json',result),('checks.json',checks),('registration_inventory.json',R),('classification.json',C),('unsupported.json',F)]: (out/name).write_text(json.dumps(data,indent=2),encoding='utf8')
 print(json.dumps(result,indent=2))

if __name__=='__main__':main()
