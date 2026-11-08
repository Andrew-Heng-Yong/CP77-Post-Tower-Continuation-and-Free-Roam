"""Handle-aware phase/scene normalization with explicit structural errors."""
from common import *
import collections
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest().upper()
def reachable(nodes,edges,seeds):
 adj=collections.defaultdict(list)
 for a,s,b,d in edges:
  if s!='CutSource' and d!='CutDestination':adj[str(a)].append(str(b))
 seen=set(map(str,seeds));todo=list(seen)
 while todo:
  for x in adj[todo.pop()]:
   if x not in seen:seen.add(x);todo.append(x)
 return seen
class Resource:
 def __init__(self,obj):
  self.obj=obj;self.root=obj['Data']['RootChunk'];self.handles={};self.errors=[]
  for x in walk(obj):
   if 'HandleId'in x and 'Data'in x:
    k=str(x['HandleId'])
    if k in self.handles and self.handles[k]!=x['Data']:self.errors.append({'kind':'DUPLICATE_HANDLE','handle':k})
    self.handles[k]=x['Data']
 def d(self,h):
  if not isinstance(h,dict):return h
  if 'Data'in h and 'HandleId'in h:return h['Data']
  if 'HandleRefId'in h:
   k=str(h['HandleRefId'])
   if k in ('-1','0') and k not in self.handles:return None
   if k not in self.handles:self.errors.append({'kind':'UNRESOLVED_HANDLE','handle':k});return None
   return self.handles[k]
  return h
 def hid(self,h):return str(h.get('HandleId',h.get('HandleRefId'))) if isinstance(h,dict) else ''
 def clean(self,x,seen=frozenset()):
  if isinstance(x,dict):
   if 'HandleId'in x or 'HandleRefId'in x:
    k=self.hid(x)
    if k in seen:return {'$cycle':True}
    return self.clean(self.d(x),seen|{k})
   return {k:self.clean(v,seen) for k,v in x.items() if k not in ('sockets','connections','phaseGraph','sceneGraph','graph','debugSymbols','sceneSolutionHash')}
  if isinstance(x,list):return [self.clean(v,seen) for v in x]
  return x
 def node(self,n,i):
  p=self.clean(n);items=list(walk(p));sockets=[{'name':str(value(s['name'])),'type':str(s.get('type'))} for h in n.get('sockets',[]) if isinstance(s:=self.d(h),dict)]
  reads=[x for x in items if x.get('$type') in ('questVarComparison_ConditionType','questVarVsVarComparison_ConditionType','questJournalEntryState_ConditionType')]
  writes=[x for x in items if x.get('$type')=='questSetVar_NodeType']
  return {'id':str(i),'type':n['$type'],'payload':p,'payload_sha256':digest(p),'sockets':sockets,'reads':reads,'writes':writes,'refs':depots(p),'journal_paths':sorted({x['realPath'] for x in items if 'realPath'in x}),'prefabs':[str(value(x['prefabNodeRef'])) for x in items if x.get('$type')=='questQuestPrefabEntry' and 'prefabNodeRef'in x],'reward':any('Reward' in x.get('$type','') or 'Achievement' in x.get('$type','') for x in items),'sms':any(x.get('$type') in ('questSendMessage_NodeType','questJournalPhoneMessage') or ('gameJournalPhoneMessage' in str(x.get('className',''))) for x in items),'conditions':[x for x in items if 'Condition' in x.get('$type','')],'node_refs':sorted({str(value(x)) for x in items if x.get('$type')=='NodeRef' and str(value(x)) not in ('0','None')})}
 def normalize(self):
  graphs={}
  def phase(gh,path):
   g=self.d(gh)
   if not isinstance(g,dict) or 'nodes' not in g:self.errors.append({'kind':'MISSING_GRAPH','graph':path});return
   ns={};socks={};ids=[]
   for h in g['nodes']:
    n=self.d(h)
    if not isinstance(n,dict) or 'id'not in n:self.errors.append({'kind':'MISSING_NODE','graph':path});continue
    i=str(n['id']);ids.append(i);ns[i]=n
    for sh in n.get('sockets',[]):
     s=self.d(sh)
     if isinstance(s,dict):socks[self.hid(sh)]=(i,str(value(s.get('name',''))))
   if len(ids)!=len(set(ids)):self.errors.append({'kind':'DUPLICATE_NODE_ID','graph':path})
   edges=[];connections=set()
   for i,n in ns.items():
    for sh in n.get('sockets',[]):
     s=self.d(sh)
     for ch in (s or {}).get('connections',[]):
      co=self.d(ch)
      if not isinstance(co,dict):self.errors.append({'kind':'MISSING_CONNECTION','graph':path});continue
      a=socks.get(self.hid(co.get('source')));b=socks.get(self.hid(co.get('destination')))
      if not a or not b:self.errors.append({'kind':'DANGLING_EDGE','graph':path,'from':a,'to':b});continue
      # A connection is listed at both ends; count each connection handle once, not each edge tuple.
      key=self.hid(ch)
      if key in connections:continue
      connections.add(key);edges.append([*a,*b])
   nodes={i:self.node(n,i) for i,n in ns.items()};entry_nodes=[n for n in ns.values() if n['$type'] in ('questInputNodeDefinition','questStartNodeDefinition')];entries={str(value(n.get('socketName',''))):str(n['id']) for n in entry_nodes}
   if len(entries)!=len(entry_nodes):self.errors.append({'kind':'DUPLICATE_ENTRY_NAME','graph':path})
   may=reachable(nodes,edges,entries.values())
   graphs[path]={'nodes':nodes,'edges':sorted(edges),'entries':entries,'reachable':sorted(may),'unreachable':sorted(set(nodes)-may)}
   for i,n in ns.items():
    child=self.d(n.get('phaseGraph'))
    if isinstance(child,dict) and 'nodes'in child:phase(n['phaseGraph'],path+'/'+i)
  if 'graph'in self.root:phase(self.root['graph'],'root')
  if 'sceneGraph'in self.root:
   sg=self.d(self.root['sceneGraph']);ns={};edges=[]
   for h in (sg or {}).get('graph',[]):
    n=self.d(h)
    if not isinstance(n,dict) or 'nodeId'not in n:self.errors.append({'kind':'MISSING_SCENE_NODE'});continue
    i=str(n['nodeId']['id'])
    if i in ns:self.errors.append({'kind':'DUPLICATE_NODE_ID','graph':'scene','node':i})
    ns[i]=self.node(n,i)
    # Embedded quest sockets carry scene/quest interface contracts even when empty.
    ns[i]['embedded_sockets']=[{'name':str(value(x.get('name',''))),'type':x.get('type')} for x in walk(self.clean(n.get('questNode'))) if x.get('$type')=='questSocketDefinition']
    qn=self.d(n.get('questNode'))
    if isinstance(qn,dict):
     ns[i]['embedded_sockets']=[{'name':str(value(s.get('name',''))),'type':s.get('type')} for sh in qn.get('sockets',[]) if isinstance(s:=self.d(sh),dict)]
     if isinstance(self.d(qn.get('phaseGraph')),dict):phase(qn['phaseGraph'],'scene/'+i)
    for si,s in enumerate(n.get('outputSockets',[])):
     stamp=s.get('stamp',{});out=str(stamp.get('name',0))+':'+str(stamp.get('ordinal',si))
     for d in s.get('destinations',[]):
      st=d.get('isockStamp',{});edges.append([i,out,str(d['nodeId']['id']),str(st.get('name',0))+':'+str(st.get('ordinal',0))])
   for e in edges:
    if e[2] not in ns:self.errors.append({'kind':'DANGLING_EDGE','graph':'scene','edge':e})
   entries={str(value(x['name'])):str(x['nodeId']['id']) for x in self.root.get('entryPoints',[])}
   may=reachable(ns,edges,entries.values());graphs['scene']={'nodes':ns,'edges':sorted(edges),'entries':entries,'reachable':sorted(may),'unreachable':sorted(set(ns)-may)}
  embedded=[]
  for e in self.obj.get('Data',{}).get('EmbeddedFiles',[]):
   content=e.get('Content',{});name=str(value(e.get('FileName','')));prefix='embedded/'+name
   if 'graph'in content:phase(content['graph'],prefix+'/root')
   elif 'sceneGraph'in content:self.errors.append({'kind':'UNSUPPORTED_EMBEDDED_SCENE','resource':name})
   embedded.append({'depot':name,'graph_prefix':prefix,'metadata':self.clean(content),'refs':depots(content),'root_prefabs':[str(value(x['prefabNodeRef'])) for x in content.get('phasePrefabs',[])]})
  meta=self.clean(self.root)
  return {'type':self.root['$type'],'graphs':graphs,'metadata':meta,'metadata_sha256':digest(meta),'refs':depots(self.obj),'root_prefabs':[str(value(x['prefabNodeRef'])) for x in self.root.get('phasePrefabs',[])],'embedded_files':embedded,'errors':self.errors}
def compare_graph(a,b,relocations=None):
 """Compare keyed nodes/sockets and edge multiplicity. No policy approval here."""
 diffs=[];relocations=relocations or {}
 def rewrite(x):
  if isinstance(x,dict):return {k:rewrite(v) for k,v in x.items()}
  if isinstance(x,list):return [rewrite(v) for v in x]
  return relocations.get(x,x) if isinstance(x,str) else x
 for gp in sorted(set(a['graphs'])|set(b['graphs'])):
  if gp not in a['graphs'] or gp not in b['graphs']:diffs.append({'kind':'GRAPH_ADDED' if gp in b['graphs'] else 'GRAPH_REMOVED','graph':gp});continue
  x=a['graphs'][gp];y=b['graphs'][gp]
  for i in sorted(set(x['nodes'])|set(y['nodes'])):
   if i not in x['nodes'] or i not in y['nodes']:diffs.append({'kind':'NODE_ADDED' if i in y['nodes'] else 'NODE_REMOVED','graph':gp,'node':i});continue
   p=x['nodes'][i];q=y['nodes'][i]
   if rewrite(p['payload'])!=q['payload']:diffs.append({'kind':'NODE_PAYLOAD_CHANGED','graph':gp,'node':i,'native_sha256':p['payload_sha256'],'restored_sha256':q['payload_sha256'],'condition_changed':rewrite(p['conditions'])!=q['conditions'],'reward_changed':p['reward'] or q['reward']})
   if p['sockets']!=q['sockets']:diffs.append({'kind':'SOCKETS_CHANGED','graph':gp,'node':i})
   if p.get('embedded_sockets')!=q.get('embedded_sockets'):diffs.append({'kind':'EMBEDDED_SOCKETS_CHANGED','graph':gp,'node':i})
  ca=collections.Counter(map(tuple,x['edges']));cb=collections.Counter(map(tuple,y['edges']))
  for e,n in (ca-cb).items():diffs.append({'kind':'EDGE_REMOVED','graph':gp,'edge':list(e),'multiplicity':n})
  for e,n in (cb-ca).items():diffs.append({'kind':'EDGE_ADDED','graph':gp,'edge':list(e),'multiplicity':n})
  lost=set(x['reachable'])&set(y['nodes'])-set(y['reachable'])
  for i in sorted(lost):diffs.append({'kind':'BRANCH_BECAME_UNREACHABLE','graph':gp,'node':i})
 if rewrite(a['metadata'])!=b['metadata']:diffs.append({'kind':'RESOURCE_METADATA_CHANGED','native_sha256':a['metadata_sha256'],'restored_sha256':b['metadata_sha256']})
 if rewrite(a.get('embedded_files',[]))!=b.get('embedded_files',[]):diffs.append({'kind':'EMBEDDED_RESOURCE_METADATA_CHANGED'})
 return diffs
