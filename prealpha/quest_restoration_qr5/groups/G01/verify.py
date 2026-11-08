"""QR5 G01: exact native recipe/body comparisons and four case-specific contracts.
Pure inputs. Mutations affect in-memory copies of actual serialized JSON only.
Run with --output NEW_DIRECTORY. No builder, archive, game, or deployment calls.
"""
from pathlib import Path
import argparse,collections,copy,json,re,sys
import source_inputs as I
from common import walk,value
from model import Resource,compare_graph,digest,reachable
Q=I.Q;H=I.H;W=I.W
S={
 Q[0]:dict(title='Fifth Column',contact='padre',region='hey',body=2,pois=[67],ow='phases/sts_hey_gle_04_ow.questphase',finish=['root/5',84],reward=['root/6',8],achievement=['root/6',60],tier_nodes=[59,61],prefix='gle_04'),
 Q[1]:dict(title='Getting Warmer...',contact='wakako',region='wbr',body=43,pois=[44,54],ow='phases/sts_hey_rey_09_openworld.questphase',finish=['root/3',145],reward=['root/5',25],achievement=['root/5',30],tier_nodes=[],prefix='rey_09'),
 Q[2]:dict(title='Jeopardy',contact='padre',region='hey',body=7,pois=[61],ow='phases/sts_hey_rey_06_openworld.questphase',finish=['root/4',57],reward=['root/4',14],achievement=['root/4',65],tier_nodes=[53,55],prefix='rey_06'),
 Q[3]:dict(title='Old Friends',contact='padre',region='hey',body=9,pois=[43],ow='sts_hey_rey_08_openworld.questphase',finish=['root/8',5],reward=['root/0',88],achievement=['root/8',28],tier_nodes=[58,59],prefix='rey_08'),
}
def path(g,a,b):
 a,b=str(a),str(b);todo=collections.deque([[a]]);seen={a}
 while todo:
  p=todo.popleft()
  if p[-1]==b:return p
  for x,so,y,si in g['edges']:
   if x==p[-1] and so!='CutSource' and si!='CutDestination' and not (g['nodes'][x]['type']=='scnCutControlNode' and so.startswith('1:')) and y not in seen:seen.add(y);todo.append(p+[y])
 return None
def ev(x,f):
 t=x['$type']
 if t=='questLogicalCondition':
  a=[ev(y,f) for y in x['conditions']];return all(a) if x['operation']=='AND' else any(a) if x['operation']=='OR' else not any(a) if x['operation']=='NOR' else False
 if t=='questFactsDBCondition':return ev(x['type'],f)
 if t=='questVarComparison_ConditionType':
  a,b=f.get(x['factName'],0),x['value'];return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[x['comparisonType']]
 raise ValueError(t)
def fixture(c):
 return {x['factName']:x['value']+1 if x['comparisonType']=='Greater' else x['value']-1 if x['comparisonType']=='Less' else x['value'] for x in walk(c) if x.get('$type')=='questVarComparison_ConditionType'}
def external(x):
 """ONLY already-approved Embedded->Soft, PC cooking envelope, derived hashes."""
 x=copy.deepcopy(x)
 for a in walk(x):
  a.pop('payload_sha256',None)
  if isinstance(a.get('phaseResource'),dict) and a['phaseResource'].get('Flags')=='Embedded':a['phaseResource']['Flags']='Soft'
  if a.get('cookingPlatform')=='PLATFORM_None':a['cookingPlatform']='PLATFORM_PC'
 return x
def run(O):
 assert not O.exists(),'Fresh output required'
 tests=[];mutations=[];models={};raws={};pins=[];evidence={}
 def ck(name,ok,ev=None,q=None):
  tests.append(dict(name=name,status='PASS' if ok else 'FAIL',quest_id=q,evidence=ev))
  if not ok:raise AssertionError(name+' '+json.dumps(ev,ensure_ascii=True)[:1200])
 for d in I.selected():
  m,p=I.load(d);models[d]=m;pins.append(p);raws[d]=I.read(p['json']);ck('resource parse '+d,not m['errors'],p['sha256'])
 def g(d,gp='root'):return models[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def edge(d,e,gp='root'):return list(map(str,e)) in g(d,gp)['edges']
 def wr(node,f,v):return any(w.get('factName')==f and w.get('value')==v for w in node['writes'])
 def rd(node,f,v):return any(w.get('factName')==f and w.get('value')==v for w in node['reads'])
 def loc(d,gp,i):
  nn=n(d,i,gp);return dict(resource=d,graph=gp,node=str(i),payload=nn['payload'],incoming=[e for e in g(d,gp)['edges'] if e[2]==str(i)],outgoing=[e for e in g(d,gp)['edges'] if e[0]==str(i)])
 corepath=H/'shared_core.json';core=I.read(corepath);ck('frozen shared core',I.sha(corepath)=='A7B283A909C8BE28E02D4C0D82AB5501F2AA23ECC0FF44270C86B403BBB5712F',str(corepath))
 for p in core['sources']:ck('shared applicability '+p['depot'],I.sha(p['binary'])==p['sha256'] and I.sha(p['json'])==p['json_sha256'],p['binary'])
 planpath=W/'research/gig_restoration/native_gigs_u9/build_plan.json';ck('manifest pinned native recipe plan',I.sha(planpath)==I.U['plan_sha256'],str(planpath));plan=I.read(planpath)
 scriptrel='r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds';script=I.C/'package'/scriptrel;sp=next(x for x in I.E['package_files'] if x['path']==scriptrel);ck('current consolidated producer',I.sha(script)==sp['sha256'],str(script));pins.append(dict(kind='current_redscript',path=str(script),sha256=I.sha(script)))
 code=script.read_text(encoding='utf8');catalog=code.split('public abstract class NativeGigDataU9 {',1)[1].split('public class NativeGigsU9',1)[0];producer=code.split('public class NativeGigsU9 extends ScriptableSystem {',1)[1].split('public class NativeGigsTickU9',1)[0]
 def arr(method):return json.loads(re.search(r'func '+method+r'\([^\n]+?array<\w+>\s*=\s*(\[[^;]+\])',catalog).group(1))
 ids=json.loads(re.search(r'func IDs\(\).*?return (\[.*?\]);',catalog).group(1))
 def data(method,i):
  body=re.search(r'func '+method+r'\(i: Int32\).*?(?=public static func|\Z)',catalog,re.S).group(0);m=re.search(r'if i\s*==\s*'+str(i)+r'\s*\{\s*return (\[.*?\]);',body);return json.loads(m.group(1)) if m else []
 for needle in ['if this.State(paths[k],classes[k])!=1 { return false; }','if this.Fact(a[k])!=0 { return false; }','if !this.EntrySafe(i)','this.Own(id,"Started")!=0','this.OldUnused(k) && this.EntrySafe(k)','this.Root(k)==1 && !this.Terminal(k)','history.Certified(id)','snapshot.FreshU9(id)']:
  ck('effective admission source '+needle,needle in producer,dict(path=str(script),source=needle))
 voice_rel='r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds';voice=I.C/'package'/voice_rel;vp=next(x for x in I.E['package_files'] if x['path']==voice_rel);vcode=voice.read_text(encoding='utf8');ck('current Tower voice-only presentation policy pin',I.sha(voice)==vp['sha256'] and 'visual.TemporaryHide(true)' in vcode and 'Character.Silverhand' in vcode and 'private func Hide' in vcode and 'SetFact(' not in vcode,dict(path=str(voice),sha256=I.sha(voice),limit='Visual-component hiding policy only; scene actor/timing/audio retained; independent props not covered. Actual attachment/hide timing LIVE_ONLY.'));pins.append(dict(kind='current_redscript_voice_policy',path=str(voice),sha256=I.sha(voice)))
 for q,s in S.items():
  rr=[r for r in I.RECIPES if r['id']==q];er=next(r for r in rr if r['kind']=='entry');entry,main=er['depot'],er['native'];s.update(entry=entry,native=main);base=main[:main.index(q)]+q+'\\';ow=base+s['ow'].replace('/','\\');s['openworld']=ow;pfx='PTFRU9_'+q;copies=[];embedded=[]
  for r in rr:
   d=r['depot'];native=models['recipe:'+r['raw']];ng=native['graphs'][r['graph']]
   ck('exact compiled root routes '+d,collections.Counter(map(tuple,g(d)['edges']))==collections.Counter(tuple(map(str,e)) for e in r['edges']),dict(native_graph=r['graph'],edges=r['edges']),q)
   for i in r['ids']:
    if i==0:continue
    original=ng['nodes'][str(i)];expected=copy.deepcopy(original['payload'])
    if r['kind']=='entry' and i==s['body'] and expected.get('phaseResource',{}).get('Flags')=='Embedded':expected['phaseResource']['Flags']='Soft'
    ck('native payload/socket '+d+':'+str(i),n(d,i)['payload']==expected and n(d,i)['sockets']==original['sockets'],dict(native=r['raw'],graph=r['graph'],node=i),q)
   for gp,gr in models[d]['graphs'].items():
    if gp=='root':continue
    srcgp=r['graph']+gp[4:];expected=copy.deepcopy(native['graphs'][srcgp]);edits=next(j for j in plan['jobs'] if j['id']==q)['parent'].get('edits',[]) if r['kind']=='entry' else []
    for edit in edits:
     if edit['graph']==srcgp:
      expected['edges'].remove(list(map(str,edit['remove'])))
      if edit.get('add'):expected['edges'].append(list(map(str,edit['add'])))
    expected['edges'].sort();seen=reachable(expected['nodes'],expected['edges'],expected['entries'].values());expected['reachable']=sorted(seen);expected['unreachable']=sorted(set(expected['nodes'])-seen)
    ck('whole native nested graph '+d+':'+gp,gr==expected,dict(native=r['raw'],graph=srcgp,approved_edits=edits),q)
   copies.append(dict(resource=d,kind=r['kind'],native='recipe:'+r['raw'],native_graph=r['graph'],native_node_ids=r['ids'],approved_difference='Embedded to Soft body handle; additive private guards/receipts; selected per-job routes from original parent, no unrelated content owner'))
  # Independently compare each original embedded main/openworld/combat/gameplay body.
  for d,native in models.items():
   if not d.startswith('recipe:'):continue
   for emb in native['embedded_files']:
    depot=emb['depot']
    if '\\'+q+'\\' not in depot or depot not in models:continue
    prefix=emb['graph_prefix']+'/';a={gp[len(prefix):]:external(gr) for gp,gr in native['graphs'].items() if gp.startswith(prefix)};b={gp:external(gr) for gp,gr in models[depot]['graphs'].items()}
    ck('embedded stock body graphs '+q+':'+depot+':'+d,a==b,dict(donor=d,prefix=prefix,standalone=depot),q)
    ck('embedded stock prefab/envelope '+q+':'+depot+':'+d,external(emb['metadata'])==external(models[depot]['metadata']),dict(donor=d,root_prefabs=emb['root_prefabs']),q);embedded.append(dict(donor=d,standalone=depot,prefix=prefix,graphs=len(a),approved_difference='Only Embedded to Soft nested phase handles and PLATFORM_None to PLATFORM_PC cooking envelope; all identities, edges, predicates and target payloads exact'))
  ck('body not evidence-free externalization '+q,any(x['standalone']==main for x in embedded),embedded,q)
  ck('actual body input '+q,n(entry,s['body'])['refs']==[main] and er['main_input'] in g(main)['entries'] and edge(entry,[65004,'Out',s['body'],er['main_input']]),dict(resource=entry,body=s['body'],input=er['main_input']),q)
  ck('native POI before one-time started '+q,all(edge(entry,[i,'Out',65004,'In']) for i in s['pois']) and wr(n(entry,65004),pfx+'_Started',1),s['pois'],q)
  guard=n(entry,65002)['payload']['condition'];fs=fixture(guard);ck('facts guard positive '+q,ev(guard,fs),fs,q)
  for fact in [pfx+'_ParentEntered',pfx+'_Fault','PTFRU9_Support_Fault']:
   ck('fault/used rejection '+q+fact,not ev(guard,fs|{fact:1}),fact,q)
  ck('absent scalar facts are zero but positive provenance required '+q,not ev(guard,{}),dict(policy='FactsDB absent scalar modeled0, not universally rejected'),q)
  ci=ids.index(q);cat={method:data(method,ci) for method in ['Paths','Classes','Facts','TerminalFacts','LegacyTags','LegacyOwnerFacts']};cat.update(index=ci,Region=arr('Region')[ci],Counter=arr('Counter')[ci],MapCount=arr('MapCount')[ci],NeedsRetaliation=arr('NeedsRetaliation')[ci],RetaliationGang=arr('RetaliationGang')[ci])
  ck('case actual region and district credit '+q,cat['Region']==s['region'] and cat['Counter']==s['region']+'_sts_counter' and s['prefix']+'_finished' in cat['TerminalFacts'],cat,q)
  cr=next(r for r in rr if r['kind']=='credit');credit=cr['depot'];cg=n(credit,65000)['payload']['condition'];cf=fixture(cg);ck('native credit single claim '+q,ev(cg,cf) and all(not ev(cg,cf|{pfx+'_'+f:1}) for f in ['CreditEntered','CreditDone']) and not ev(cg,cf|{pfx+'_Started':0}),loc(credit,'root',65000),q)
  ck('one additive native counter '+q,n(credit,3)['writes']==[{'$type':'questSetVar_NodeType','factName':s['region']+'_sts_counter','setExactValue':0,'value':1}],loc(credit,'root',3),q)
  ck('native completion and target record '+q,wr(n(ow,s['finish'][1],s['finish'][0]),s['prefix']+'_finished',1) and any(value(x)==('QuestRewards.'+q+'_completion') for x in walk(n(ow,s['reward'][1],s['reward'][0])['payload']) if x.get('$type')=='TweakDBID'),dict(finish=loc(ow,*s['finish']),reward=loc(ow,*s['reward'])),q)
  native_ds=[d for d in models if d.startswith('base\\') and '\\'+q+'\\' in d];facts=[];journals=[];rewards=[];assets=[];calls=[];phones=[];sms=[];owners=[];dependencies=[]
  for d in native_ds:
   owners.append(dict(resource=d,root_prefabs=models[d]['root_prefabs'],metadata=models[d]['metadata']))
   for gp,gr in models[d]['graphs'].items():
    for i,nn in gr['nodes'].items():
     pin=loc(d,gp,i)
     if nn['reads'] or nn['writes']:facts.append(pin|dict(reads=nn['reads'],writes=nn['writes']))
     if nn['journal_paths']:journals.append(pin|dict(paths=nn['journal_paths']))
     if nn['reward']:rewards.append(pin)
     if nn['node_refs'] or nn['prefabs']:assets.append(pin|dict(node_refs=nn['node_refs'],phase_instance_prefabs=nn['prefabs']))
     if nn['sms']:sms.append(pin)
     for target in nn['refs']:
      dependencies.append(pin|dict(target=target,indexed=target in I.IDX,current_source=target in models))
      if '_holocall_' in target and target.endswith('.scene'):
       for e in pin['incoming']:
        if target in models and e[3] in g(target,'scene')['entries']:calls.append(pin|dict(scene=target,input=e[3],entry_node=g(target,'scene')['entries'][e[3]]))
  ck('native actual prebrief and debrief callers '+q,any('_prebrief.scene' in x['scene'] for x in calls) and any('_debriefs.scene' in x['scene'] for x in calls),calls,q)
  hc='base\\quest\\holocalls\\'+s['contact']+'\\'+s['contact']+'_holocall.questphase';hs=hc.replace('.questphase','.scene')
  for call in calls:
   d=call['scene'];sg=g(d,'scene')
   for i,nn in sg['nodes'].items():
    for w in nn['writes']:
     req=w.get('factName','')
     if w.get('value')!=1 or not req.startswith('holo_'+s['contact']+'_') or not req.endswith('_activate') or not path(sg,call['entry_node'],i):continue
     base_req=req.removesuffix('_activate');ack=base_req+'_done';allwaits=[j for j,node in sg['nodes'].items() if any(r.get('factName')==ack and r.get('comparisonType')=='Greater' and r.get('value')==0 for r in node['reads'])];waits=[j for j in allwaits if path(sg,i,j)];clears=[j for j,node in sg['nodes'].items() if wr(node,ack,0) and any(path(sg,k,j) for k in waits)]
     readers=[j for j,node in g(hc)['nodes'].items() if any(r.get('factName')==req for r in node['reads'])];acks=[j for j,node in g(hs,'scene')['nodes'].items() if wr(node,ack,1) and base_req in g(hs,'scene')['entries'] and path(g(hs,'scene'),g(hs,'scene')['entries'][base_req],j)]
     forkcontext=[dict(wait=j,entry_to_wait=path(sg,call['entry_node'],j)) for j in allwaits if path(sg,call['entry_node'],j)]
     ck('actual request listener receipt waiting context '+q+d+i,bool(readers and acks) and (bool(waits and clears) or bool(forkcontext)),dict(request=req,producer=i,waits=waits,clears=clears,controller_readers=readers,ack_writers=acks,fork_context=forkcontext),q)
     phones.append(dict(scene=d,input=call['input'],entry=call['entry_node'],producer=i,request=req,controller=hc,readers=readers,ack_scene=hs,ack_writers=acks,waits=waits,clears=clears,prearmed_parallel_context=forkcontext,entry_to_request=path(sg,call['entry_node'],i),status='PASS_STRUCTURAL_PROTOCOL' if waits and clears else 'CONDITIONAL_NATIVE_RETRY_SHARED_WAIT'))
  phones=list({(p['scene'],p['input'],p['producer'],p['request']):p for p in phones}.values())
  ck('actual communications found '+q,bool(phones),dict(calls=len(calls),requests=len(phones),sms=len(sms)),q)
  for r in rr:
   if r['kind']=='map':ck('native fixer visit map gate '+q+r['depot'],rd(n(r['depot'],2),s['contact']+'_visited',0) and any(q in jp for nn in g(r['depot'])['nodes'].values() for jp in nn['journal_paths']),dict(depot=r['depot'],graph=r['graph'],contact=s['contact']),q)
  # Bounded scalar/journal model is tied to the extracted actual EntrySafe source.
  # Missing scalar is0; missing journal is-1, matching current State implementation.
  jf={p:1 for p in cat['Paths']};ff={f:0 for f in cat['Facts']}
  admissible=lambda facts,journal:all(journal.get(p,-1)==1 for p in cat['Paths']) and all(facts.get(f,0)==0 for f in cat['Facts'])
  ck('extracted EntrySafe clean scalar and journal witness '+q,admissible(ff,jf) and admissible({},jf),dict(paths=len(jf),facts=len(ff),missing_scalar_policy=0,missing_journal_policy=-1),q)
  for jp in cat['Paths']:ck('each recorded native journal protects progress '+q+jp,all(not admissible(ff,jf|{jp:v}) for v in [2,3,4,-1]),jp,q)
  for fact in cat['Facts']:ck('each recorded fact protects native history '+q+fact,not admissible(ff|{fact:1},jf),fact,q)
  nativej={p for row in journals for p in row['paths'] if p.startswith('quests/') and q in p};nativef={x.get('factName') for row in facts for x in row['reads']+row['writes'] if x.get('factName','').startswith(s['prefix']+'_')}
  apppath=I.F/'shared/tdb_applicability_02'/f'{q}.json';app=I.read(apppath);ck('stock TDB query exact requested reward '+q,any(('QuestRewards.'+q+'_completion') in t.get('requested_aliases',[]) and t.get('exists_in_stock') for t in app['targets']),str(apppath),q);pins.append(dict(kind='shared_stock_tdb_applicability',path=str(apppath),sha256=I.sha(apppath)))
  for pk,hk in [('path','sha256'),('targets_path','targets_sha256')]:ck('shared stock target capture hash '+q+pk,I.sha(app['capture'][pk])==app['capture'][hk],app['capture'][pk],q)
  evidence[q]=dict(spec=s,recipes=copies,embedded_native_comparisons=embedded,entry_guard=guard,entry_fixture=fs,native_entry_tier_nodes=[loc(entry,'root',i) for i in s['tier_nodes']],effective_producer=dict(path=str(script),sha256=I.sha(script),catalogue=cat,reference_coverage=dict(native_journal_refs_not_catalogued=sorted(nativej-set(cat['Paths'])),native_fact_refs_not_catalogued=sorted(nativef-set(cat['Facts'])),note='Uncatalogued reference does not establish valid started history; exact journal definitions and saved-owner witness still required.')),calls=calls,phone_protocols=phones,sms_nodes=sms,facts=facts,journals=journals,rewards=rewards,assets=assets,owners=owners,dependencies=dependencies,stock_tdb_applicability=dict(path=str(apppath),sha256=I.sha(apppath),limits=app['limits']))
  # Against independent native payload oracle, mutate actual raw serialized resources.
  for label,d,gp,i,edit in [
   ('district credit doubles',credit,'root',3,lambda a:next(x for x in walk(a) if x.get('$type')=='questSetVar_NodeType').update(value=2)),
   ('saved body node identity changed',entry,'root',s['body'],lambda a:a.update(id=69991)),
   ('reward target missing',ow,s['reward'][0],s['reward'][1],lambda a:next(x for x in walk(a) if x.get('$type')=='TweakDBID').update({'$value':'QuestRewards.QR5_nonexistent'})),
  ]:
   bad=copy.deepcopy(raws[d]);res=Resource(bad)
   def rawgraph(gp):
    gr=res.d(res.root['graph'])
    for piece in gp.split('/')[1:]:gr=res.d(next(res.d(h) for h in gr['nodes'] if str(res.d(h)['id'])==piece)['phaseGraph'])
    return gr
   target=next(res.d(h) for h in rawgraph(gp)['nodes'] if str(res.d(h)['id'])==str(i));edit(target);bm=Resource(bad).normalize();det=bool(compare_graph(models[d],bm))
   mutations.append(dict(quest_id=q,fault=label,resource=d,graph=gp,node=i,detected=det,oracle='Exact native recipe/current raw independently pinned; structural compare detects changed payload/identity; does not simulate engine'))
   ck('raw mutation '+q+label,det,mutations[-1],q)
  # Mutate an actual guard and caller receipt wait, not a synthetic graph fixture.
  bad=copy.deepcopy(raws[entry]);res=Resource(bad);gr=res.d(res.root['graph']);rn=next(res.d(h) for h in gr['nodes'] if res.d(h).get('id')==65002);res.d(rn['condition'])['operation']='OR'
  bm=Resource(bad).normalize();mutguard=bm['graphs']['root']['nodes']['65002']['payload']['condition'];det=ev(mutguard,{}) and not ev(guard,{}) and bool(compare_graph(models[entry],bm));mutations.append(dict(quest_id=q,fault='entry required AND changed to OR admits zero provenance',resource=entry,node=65002,detected=det));ck('actual guard semantics mutation '+q,det,mutations[-1],q)
  phone=next(p for p in phones if '_prebrief.scene' in p['scene'] and p['request'].endswith('_start_activate'));d=phone['scene'];wait=phone['waits'][0];bad=copy.deepcopy(raws[d]);res=Resource(bad);sg=res.d(res.root['sceneGraph']);removed=0
  for h in sg['graph']:
   sn=res.d(h)
   for sock in sn.get('outputSockets',[]):
    old=sock.get('destinations',[]);sock['destinations']=[dst for dst in old if str(dst['nodeId']['id'])!=wait];removed+=len(old)-len(sock['destinations'])
  bm=Resource(bad).normalize();det=removed>0 and path(bm['graphs']['scene'],phone['producer'],wait) is None and bool(compare_graph(models[d],bm));mutations.append(dict(quest_id=q,fault='all actual prebrief receipt-wait incoming routes removed',resource=d,node=wait,removed_edges=removed,detected=det));ck('actual phone wait route mutation '+q,det,mutations[-1],q)
 # Distinct specific behavioral predicates and their actual outgoing sockets.
 def expect(q,d,gp,i,reads,edges):
  ck('case branch '+q+gp+':'+str(i),all(rd(n(d,i,gp),f,v) for f,v in reads) and all(edge(d,e,gp) for e in edges),loc(d,gp,i),q)
 q=Q[0];ow=S[q]['openworld'];expect(q,ow,'root/5',133,[('gle_04_drink_with_bouncer',2)],[(133,'Out',128,'Failed')]);expect(q,ow,'root/5',134,[('gle_04_drink_with_bouncer',3)],[(134,'Out',129,'Succeeded')]);expect(q,ow,'root/6',64,[('gle_04_gang_retaliation',1)],[(64,'False',63,'In'),(64,'True',67,'In')]);ck('Valentinos consequence required only real requesting gig',evidence[q]['effective_producer']['catalogue']['NeedsRetaliation'] and evidence[q]['effective_producer']['catalogue']['RetaliationGang']=='valentinos',evidence[q]['entry_guard'],q)
 for q in [Q[0],Q[2],Q[3]]:
  entry=S[q]['entry'];a,b=S[q]['tier_nodes'];tier1='sts_hey_'+('gle' if q==Q[0] else 'rey')+'_tier_1';pa=n(entry,a)['payload']['condition'];pb=n(entry,b)['payload']['condition'];ck('native tier alternatives zero and earned witnesses '+q,not(ev(pa,{}) or ev(pb,{})) and (ev(pa,fixture(pa)) or ev(pb,fixture(pa))) and ev(pb,{tier1:1}),dict(primary=loc(entry,'root',a),fallback=loc(entry,'root',b),missing_scalar=0),q)
 q=Q[1];entry=S[q]['entry'];ck('Getting Warmer exact tier2 predicate',rd(n(entry,3,'root/3'),'sts_wbr_jpn_tier_2',0) and not ev(n(entry,3,'root/3')['payload']['condition'],{}) and ev(n(entry,3,'root/3')['payload']['condition'],{'sts_wbr_jpn_tier_2':1}),loc(entry,'root/3',3),q)
 q=Q[1];ow=S[q]['openworld'];combat=next(d for d in models if '\\'+q+'\\' in d and d.endswith('_combat.questphase'));expect(q,combat,'root/2/9',86,[('rey_09_cooled',1)],[(86,'True',54,'In')]);expect(q,ow,'root/5',43,[('rey_09_finished',1)],[(43,'Out',41,'Active')]);expect(q,ow,'root/5',44,[('rey_09_target_died',1)],[(44,'Out',42,'Active')]);credit=next(r['depot'] for r in I.RECIPES if r['id']==q and r['kind']=='credit');ck('Getting Warmer native failure OR success single Westbrook credit',g(credit)['nodes']['16']['type']=='questLogicalXorNodeDefinition' and all(edge(credit,e) for e in [(10,'Out',16,'In1'),(14,'Out',16,'In2'),(16,'Out1',3,'In')]),g(credit)['edges'],q)
 q=Q[2];ow=S[q]['openworld'];rec=next(d for d in models if '\\'+q+'\\' in d and d.endswith('_receptionist.scene'));ck('Jeopardy native receptionist real progression writer',wr(n(rec,216,'scene'),'rey_06_go_to_the_morgue',1),loc(rec,'scene',216),q);expect(q,ow,'root/5',318,[('rey_06_go_to_the_morgue',0)],[(318,'Out',124,'Active')]);ck('Jeopardy scene and rejection/SMS both reward routes native',all(edge(ow,e,'root/4') for e in [(55,'End1',14,'In'),(75,'Out',14,'In'),(14,'Out',27,'In'),(27,'Out',57,'In')]),g(ow,'root/4')['edges'],q)
 q=Q[3];ow=S[q]['openworld'];pre=next(d for d in models if d.endswith('_prestate_control.questphase'));er=next(r for r in I.RECIPES if r['id']==q and r['kind']=='entry');ck('Old Friends parallel native prestate preserved',n(er['depot'],64000)['refs']==[pre] and edge(er['depot'],[65003,'Out',64000,'In1']) and all(edge(pre,e) for e in [(0,'Out',3,'In'),(3,'False',5,'In'),(5,'False',6,'In'),(8,'Out',12,'In')]),dict(prestate=pre,edges=g(pre)['edges']),q);expect(q,ow,'root/0/108',30,[('rey_08_karubo_dead',0)],[(30,'True',44,'In'),(30,'False',32,'In')]);expect(q,ow,'root/0',215,[('rey_08_in_combat',0)],[(215,'True',163,'In'),(215,'False',134,'In')]);loot=n(ow,5,'root/2/10');ck('Old Friends native unknown item startup gate retained',any(x.get('$type')=='TweakDBID' and str(value(x))=='131215478384' for x in walk(loot['payload'])) and edge(ow,[4,'Out',5,'In'],'root/2/10') and edge(ow,[5,'Out',2,'In1'],'root/2/10'),loc(ow,'root/2/10',5),q)
 evidence[q]['unknown_stock_item']=dict(id='131215478384',location=loc(ow,'root/2/10',5),role='Native Karubo startup InjectLoot after spawned wait4; output enters 3-way AND2, not reward target. Same exact payload in original Vista embedded body. Missing base+EP1 record is native evidence discrepancy; engine invalid-item semantics and external record providers unresolved, no restoration-specific defect proven.')
 # Real raw native loot record and startup dependency mutations.
 for label,d,gp,i,field,new in [('Old Friends loot record removed',ow,'root/2/10',5,'$value','Items.QR5_missing'),('Old Friends shared prestate binding lost',er['depot'],'root',64000,'$value','towercontinued\\QR5_missing.questphase')]:
  bad=copy.deepcopy(raws[d]);res=Resource(bad);gr=res.d(res.root['graph'])
  for piece in gp.split('/')[1:]:gr=res.d(next(res.d(h) for h in gr['nodes'] if str(res.d(h)['id'])==piece)['phaseGraph'])
  nn=next(res.d(h) for h in gr['nodes'] if str(res.d(h)['id'])==str(i));target=next(x for x in walk(nn) if x.get('$type')==('TweakDBID' if i==5 else 'ResourcePath'));target[field]=new;det=bool(compare_graph(models[d],Resource(bad).normalize()));mutations.append(dict(quest_id=q,fault=label,resource=d,graph=gp,node=i,detected=det));ck('raw mutation '+label,det,mutations[-1],q)
 I.write(O/'source_pins.json',pins);I.write(O/'graph_evidence.json',dict(quests=evidence,source_epoch=str(I.F/'source_epoch_00.json'),source_epoch_sha256=I.sha(I.F/'source_epoch_00.json'),shared_core=str(corepath),shared_core_sha256=I.sha(corepath),code_path=str(Path(__file__).resolve()),code_sha256=I.sha(__file__)))
 I.write(O/'tests.json',dict(status='PASS_SCOPED_STATIC_CHECKS',count=len(tests),checks=tests,mutations=mutations,resources=len(models),source_pins=str(O/'source_pins.json'),source_pins_sha256=I.sha(O/'source_pins.json'),evidence_sha256=I.sha(O/'graph_evidence.json'),code_sha256=I.sha(__file__),runtime_changes=[],limits='MAY reachability and raw parity are not proof of engine execution, ownership retirement, streamed placement, target record full closure or live reward safety.'))
 return dict(checks=len(tests),mutations=len(mutations),resources=len(models),quests=len(evidence))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(run(Path(a.output).resolve())))
