"""Strict read-only registry/depot preflight, scoped to frozen owner04/marker04."""
from pathlib import Path
import sys,json,collections,binascii,copy,struct,hashlib
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,value,fnv,walk
from model import Resource
def plain(n):
 k=n['kind']
 if k=='scalar':return n.get('value')
 if k=='sequence':return [plain(x)for x in n['items']]
 if k=='mapping':
  entries=[(plain(x['key']),plain(x['value']))for x in n['entries']];assert all(isinstance(k,str)for k,v in entries),'non-scalar YAML mapping key';assert len({k for k,v in entries})==len(entries),'duplicate YAML key';return dict(entries)
 raise ValueError(('unsupported AST kind',k))
def connection(x):
 if x is None:return [],None
 if isinstance(x,list):nodes=x;socket=None
 elif isinstance(x,dict):
  if set(x)-{'node','socket'}:raise ValueError(('unsupported connection keys',set(x)))
  nodes=x.get('node');socket=x.get('socket')
 else:raise ValueError(('unsupported connection shape',x))
 if not isinstance(nodes,list)or any(not isinstance(n,str)or not n.isdecimal()or not 0<=int(n)<=65535 for n in nodes):raise ValueError(('invalid uint16 node path',nodes))
 if socket is not None and not isinstance(socket,str):raise ValueError(('invalid socket',socket))
 return list(map(int,nodes)),socket
def crc_bit(s):
 c=65535
 for b in s.encode():
  c^=b<<8
  for _ in range(8):c=((c<<1)^0x1021)&65535 if c&32768 else(c<<1)&65535
 return c
def parse_configs(configs,target):
 records=[];scope=collections.defaultdict(set);unsupported=[];parsed=[]
 for file in configs:
  try:
   if file['parse_status']!='PARSED':raise ValueError(file.get('error'))
   if len(file['documents'])>1:raise ValueError('multiple YAML documents are not assessed')
   root=plain(file['documents'][0])if file['documents']else{}
   if root is None:root={}
   if not isinstance(root,dict):raise ValueError('non-mapping XL root')
   meta=root.get('resource',{})
   if not isinstance(meta,dict):raise ValueError('non-mapping resource metadata')
   scopes=meta.get('scope',{})
   if not isinstance(scopes,dict):raise ValueError('unsupported ResourceMeta scope')
   for alias,targets in scopes.items():
    if isinstance(targets,str):targets=[targets]
    if not isinstance(targets,list)or not all(isinstance(t,str)for t in targets):raise ValueError('unsupported ResourceMeta scope targets')
    scope[alias].update(t for t in targets if t!=alias)
   q=root.get('quest')
   if q is None:parsed.append({'file':file['path'],'classification':'NO_QUEST_SECTION','empty_document':not file['documents']});continue
   if not isinstance(q,dict):raise ValueError('non-mapping quest section')
   if set(q)-{'phases'}:raise ValueError(('unsupported quest keys',set(q)))
   phases=q.get('phases',[])
   if not isinstance(phases,list):raise ValueError('non-sequence quest.phases')
   for index,p in enumerate(phases):
    if not isinstance(p,dict)or set(p)-{'path','parent','connection','input','output','intercept'}:raise ValueError(('unsupported quest phase shape',p))
    if not isinstance(p.get('path'),str)or not isinstance(p.get('parent'),str):raise ValueError('quest phase path/parent not scalar')
    nodes,socket=connection(p.get('connection'))
    if 'input'in p:nodes,socket=connection(p['input'])
    if 'output'in p:connection(p['output'])
    records.append({'path':p['path'],'parent':p['parent'],'input_node_path':nodes,'input_socket':socket,'source':file['path'],'source_sha256':file['sha256'],'ordinal':index,'candidate':file['candidate']})
   parsed.append({'file':file['path'],'classification':'QUEST_PHASES_PARSED','phases':len(phases)})
  except (AssertionError,ValueError,KeyError)as ex:unsupported.append({'file':file['path'],'error':str(ex)})
 def expand(p,seen=frozenset()):
  if p in seen:raise ValueError(('ResourceMeta scope cycle',p))
  return {z for q in scope.get(p,set())for z in expand(q,seen|{p})}if scope.get(p)else{p}
 for r in records:
  try:r['expanded_parents']=sorted(expand(r['parent']));r['targets_intended_parent']=target in r['expanded_parents']
  except ValueError as ex:unsupported.append({'file':r['source'],'error':str(ex)});r['targets_intended_parent']=None
 return records,parsed,unsupported
def run(o):
 assert not o.exists();ip=H/'ronald_namespace_inputs_01/manifest.json';I=read(ip);plan=read(Path(I['registration_plan']));q=plan['quest'];target=q['parent'];owner=q['path'];T=[]
 def ck(n,b,e=None):T.append({'name':n,'pass':bool(b),'evidence':e});assert b,n
 ck('frozen explicit intended registration plan pinned',sha(Path(I['registration_plan']))==I['registration_plan_sha256']=='169C3FBDE2584DF2ED363A9C6601313FFCDBE73099B90F08054C89BEC803E4ED');ck('actual intended EP1 parent/input/socket confirmed',target==r'ep1\quest\ep1.quest'and q['input']=={'node':[1],'socket':'Out'}and q['append_after_existing']);
 for key in ['owner_manifest','marker_manifest']:ck('frozen private manifest '+key,sha(Path(plan[key]['path']))==plan[key]['sha256'])
 owner_manifest=read(Path(plan['owner_manifest']['path']));markers=read(Path(plan['marker_manifest']['path']));depots=[owner,markers['intended_sector_depot'],markers['intended_block_depot']];ck('three exact new resource paths match declared namespace',set(depots)==set(I['depots'])-{target}and len(set(map(fnv,depots)))==3)
 ck('all current native/installed archive indexes consulted',len(I['archive_index_inventory'])==134 and all(x['read_status']=='NoError'for x in I['archive_index_inventory']));ck('zero installed/native FNV depot collisions for all three new paths',not any(x['depot']in depots for x in I['matching_providers']))
 candidate=W/'prealpha/quest_restoration_qr7/candidate_01/archive_source';keys=collections.defaultdict(list)
 for f in candidate.rglob('*'):
  if f.is_file():keys[fnv(f.relative_to(candidate).as_posix().replace('/','\\'))].append(str(f))
 for d in depots:ck('candidate source has no same or colliding new depot key '+d,fnv(d)not in keys,{'fnv64':fnv(d)})
 parent=next(x for x in I['matching_providers']if x['depot']==target);ck('native parent unique current provider',sum(x['depot']==target for x in I['matching_providers'])==1);ck('native parent raw/typed pins',sha(Path(parent['raw']))==parent['raw_sha256']and sha(Path(parent['json']))==parent['json_sha256']);pm=Resource(read(Path(parent['json']))).normalize();ng=pm['graphs']['root'];ck('native target is actual start1.Out',not pm['errors']and ng['nodes']['1']['type']=='questStartNodeDefinition'and {'name':'Out','type':'Output'}in ng['nodes']['1']['sockets']);nativeids=set(map(int,ng['nodes']));newid=crc_bit(owner+':1');ck('independent CRC matches native algorithm and plan',newid==binascii.crc_hqx((owner+':1').encode(),65535)==q['derived_crc_ccitt_false']==19913)
 configs=I['xl_configs'];ck('all captured XL files still exact',all(sha(Path(x['path']))==x['sha256']for x in configs));regs,classified,unsupported=parse_configs(configs,target);write(o/'yaml_classification.json',classified);write(o/'unsupported_yaml.json',unsupported);ck('no unsupported quest YAML or scope shape silently skipped',not unsupported,unsupported)
 candidatefile=next(x for x in configs if x['candidate']);installedfile=next(x for x in configs if not x['candidate']and Path(x['path']).name==Path(candidatefile['path']).name)
 installed=[r for r in regs if not r['candidate']and r['targets_intended_parent']];effective=[r for r in regs if r['targets_intended_parent']and(r['candidate']or r['source']!=installedfile['path'])]
 for r in regs:
  if r['targets_intended_parent']:
   np=r['input_node_path'];ck('all actual EP1 root addition targets resolve supported node1 '+r['path'],np in [[],[1]])
   r['generated_key']=r['path']+':1';r['generated_id']=crc_bit(r['generated_key']);ck('independent CRC for existing root registration '+r['path'],r['generated_id']==binascii.crc_hqx(r['generated_key'].encode(),65535))
 for label,rows in [('installed',installed),('candidate_effective',effective)]:
  ids=[r['generated_id']for r in rows];ck('new ID absent from '+label+' additions',newid not in ids);ck('new ID absent from native parent '+label,newid not in nativeids);ck('existing '+label+' root additions and native IDs are collision-free',len(ids)==len(set(ids))and not(set(ids)&nativeids))
 oldcand=[r for r in regs if r['source']==candidatefile['path']];oldinstalled=[r for r in regs if r['source']==installedfile['path']];ck('candidate retains every installed PTFR registration in original order',[(r['path'],r['parent'],r['input_node_path'],r['input_socket'])for r in oldcand]==[(r['path'],r['parent'],r['input_node_path'],r['input_socket'])for r in oldinstalled])
 # Source-pinned packed world IDs and exact full refs, independently of JSON's
 # obsolete NodeIndex slot. No global game-world collision claim is made.
 for field,shakey in [('buffer','buffer_sha256'),('raw','raw_sha256'),('block_raw','block_raw_sha256'),('json','json_sha256'),('block_json','block_json_sha256')]:ck('private marker artifact pin '+field,sha(Path(markers[field]))==markers[shakey])
 raw=Path(markers['buffer']).read_bytes();refs=markers['private_refs'];globals=[struct.unpack_from('<Q',raw,i*144+0x58)[0]for i in range(2)];ck('two packed private marker globals distinct',len(raw)==288 and globals[0]!=globals[1]and all(globals));ck('globals equal independent SDK full NodeRef hash',globals==[int(fnv(r.replace('#','')))for r in refs]);ck('packed indices and pointer placeholders exact',[struct.unpack_from('<Q',raw,i*144+0x70)[0]&0x7ffff for i in range(2)]==[0,1]and all(struct.unpack_from('<Q',raw,i*144+0x50)[0]==0 for i in range(2)))
 sd=read(Path(markers['json']))['Data']['RootChunk'];bd=read(Path(markers['block_json']))['Data']['RootChunk'];ck('serialized full private marker refs match globals',list(map(value,[x['QuestPrefabRefHash']for x in sd['nodeData']['Data']]))==refs);native_sector=read(Path(markers['native']['json']))['Data']['RootChunk'];retained_source_hashes=[n['Data']['sourcePrefabHash']for n in sd['nodes']];ck('sourcePrefabHash is explicitly retained native provenance, with lease semantics unresolved',retained_source_hashes==[native_sector['nodes'][i]['Data']['sourcePrefabHash']for i in [1,3]],retained_source_hashes);ck('descriptor names only the new sector and private prefab',len(bd['descriptors'])==1 and value(bd['descriptors'][0]['data']['DepotPath'])==markers['intended_sector_depot']and value(bd['descriptors'][0]['questPrefabNodeRef'])==markers['private_parent'])
 owner_model=Resource(read(Path(owner_manifest['json']))).normalize();ck('private owner actually references same private prefab',any(markers['private_parent']in n['prefabs']for g in owner_model['graphs'].values()for n in g['nodes'].values()))
 roots=plain(candidatefile['documents'][0]);blocks=roots.get('streaming',{}).get('blocks');ck('candidate existing streaming block list fully parsed',isinstance(blocks,list)and all(isinstance(b,str)for b in blocks));ck('new streaming block absent before append',markers['intended_block_depot']not in blocks)
 qtext='    - path: '+owner+'\n      parent: '+target+'\n      input:\n        node: [1]\n        socket: Out\n';btext='    - '+markers['intended_block_depot']+'\n';write(o/'implementation_plan.json',{'status':'PROVISIONAL_NAMESPACE_PREFLIGHT_PASS_FROZEN_OWNER04_MARKER04','registration_plan':I['registration_plan'],'registration_plan_sha256':I['registration_plan_sha256'],'new_depots':[{'depot':d,'fnv64':fnv(d)}for d in depots],'quest_append':q,'generated_id':newid,'native_parent_ids':sorted(nativeids),'existing_candidate_phase_count':len(oldcand),'streaming_blocks_append':[markers['intended_block_depot']],'existing_streaming_block_count':len(blocks),'append_only_preserve_existing_order':True,'source_guard':{'candidate_XL':candidatefile['path'],'candidate_XL_sha256':candidatefile['sha256'],'owner_manifest_sha256':plan['owner_manifest']['sha256'],'marker_manifest_sha256':plan['marker_manifest']['sha256']},'provisional':'Recheck if any intended depot, parent/input, marker full ref/global or current XL changes. This does not approve source lifecycle or final package.'});(o/'quest_phase_append.txt').write_text(qtext,encoding='utf-8');(o/'streaming_block_append.txt').write_text(btext,encoding='utf-8')
 # Deliberate controls on actual parsed registration/path inputs and raw setup.
 regmut=copy.deepcopy(configs);mc=next(x for x in regmut if x['candidate']);mq=next(x['value']for x in mc['documents'][0]['entries']if x['key']['value']=='quest');ml=next(x['value']for x in mq['entries']if x['key']['value']=='phases')['items'];entry=copy.deepcopy(ml[0]);next(x['value']for x in entry['entries']if x['key']['value']=='path')['value']=owner;ml.append(entry);mutregs,_,mrerr=parse_configs(regmut,target);ck('actual candidate AST already-registered new owner collision caught',not mrerr and newid in [crc_bit(r['path']+':1')for r in mutregs if r['candidate']and r['targets_intended_parent']]);write(o/'mutant_existing_registration_AST.json',mc)
 bad=copy.deepcopy(configs);cand=next(x for x in bad if x['candidate']);doc=cand['documents'][0];quest=next(x['value']for x in doc['entries']if x['key']['value']=='quest');next(x['value']for x in quest['entries']if x['key']['value']=='phases')['kind']='scalar';_,_,badshape=parse_configs(bad,target);ck('actual candidate AST unsupported quest shape rejected',bool(badshape));mut=bytearray(raw);mut[144+0x58:144+0x60]=mut[0x58:0x60];ck('raw duplicate-global mutation caught',struct.unpack_from('<Q',mut,0x58)[0]==struct.unpack_from('<Q',mut,144+0x58)[0]);(o/'mutant_duplicate_globals.bin').write_bytes(mut)
 write(o/'registration_inventory.json',regs);write(o/'tests.json',T);write(o/'evidence.json',{'status':'PASS_PROVISIONAL_DEPOT_AND_ARCHIVEXL_NAMESPACE_FROZEN_OWNER04_MARKER04','checks':len(T),'queried_archive_indexes':134,'new_depot_collisions':[],'new_generated_id':newid,'native_root_ids':sorted(nativeids),'installed_target_registrations':len(installed),'effective_candidate_target_registrations':len(effective),'all_parsed_quest_additions':len(regs),'XL_files':len(configs),'unsupported_quest_YAML':unsupported,'new_marker_globals':globals,'new_marker_refs':refs,'capture':str(ip),'capture_sha256':sha(ip),'implementation_plan':str(o/'implementation_plan.json'),'limits':['Depot FNV collision inventory covers all134 native/installed current archive indexes plus current candidate source keys.','Generated phase ID collision proof covers the actual native EP1 root plus every installed and effective candidate addition targeting that graph, with ResourceMeta parent scopes parsed. Other-parent registrations are classified, not silently assumed to share this graph.','World globals are proved distinct and mapped to the exact private NodeRefs/owner; no full native/external world-global census was performed. That broader namespace remains a bounded unresolved collision risk.','Private prefab identity, marker ownership and source hashes are scoped to frozen04. Independent lifecycle review and final package readback remain separate gates.'],'candidate_or_XL_writes':0});print({'checks':len(T),'ID':newid,'installed':len(installed),'effective':len(effective),'evidence':str(o/'evidence.json')})
 # Keep the ownership field explicitly outside this namespace PASS. The first
 # attempt's extra equality assumption was unsupported; no rehash is proposed.
 final=read(o/'evidence.json');final['retained_native_sourcePrefabHash']=retained_source_hashes;final['unresolved_semantic_gates']=['Both trigger definitions retain native sourcePrefabHash8425604133833249267. Its runtime lease/provenance role is not established by depot/registration/global-ref checks; C ownership review must adjudicate it before integration.'];write(o/'evidence.json',final)
 impl=read(o/'implementation_plan.json');impl['unresolved_semantic_gates']=final['unresolved_semantic_gates'];write(o/'implementation_plan.json',impl)
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);run(Path(a.parse_args().output))
