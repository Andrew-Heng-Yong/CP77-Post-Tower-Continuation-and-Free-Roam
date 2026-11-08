"""Source-specific U10 comparison against exact native donors. Fresh evidence only."""
from pathlib import Path
import sys,json,copy,collections,argparse,re
import inputs as I
from model import Resource,compare_graph,digest
def path(g,a,b):
 a,b=str(a),str(b);todo=[a];seen=set()
 while todo:
  x=todo.pop()
  if x==b:return True
  if x in seen:continue
  seen.add(x);todo += [e[2] for e in g['edges'] if e[0]==x and e[1]!='CutSource' and e[3]!='CutDestination' and not(g['nodes'][x]['type']=='scnCutControlNode' and e[1].startswith('1:'))]
 return False
def replace(x,mp):
 if isinstance(x,str):return mp.get(x,x)
 if isinstance(x,list):return [replace(v,mp) for v in x]
 if isinstance(x,dict):return {k:replace(v,mp) for k,v in x.items()}
 return x
def wr(n,f,v):return any(w.get('factName')==f and w.get('value')==v for w in n['writes'])
def ev(c,f,j,items):
 t=c['$type']
 if t=='questLogicalCondition':
  vals=[ev(x,f,j,items) for x in c['conditions']];return all(vals) if c['operation']=='AND' else any(vals) if c['operation']=='OR' else not any(vals)
 if t in ['questFactsDBCondition','questJournalCondition','questObjectCondition']:return ev(c['type'],f,j,items)
 if t=='questVarComparison_ConditionType':
  a,b=f.get(c['factName'],0),c['value'];return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[c['comparisonType']]
 if t=='questJournalEntryState_ConditionType':return (j.get(c['path']['realPath'])==c['state']) != bool(c['inverted'])
 if t=='questInventory_ConditionType':
  a,b=items.get(str(I.value(c['itemID'])),0),c['quantity'];return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[c['comparisonType']]
 raise ValueError(t)
def run(group,O):
 assert not O.exists();M={};pins=[];tests=[];issues=[];mutations=[];evidence={}
 def ck(name,ok,evidence=None,q=None):
  tests.append({'name':name,'status':'PASS' if ok else 'FAIL','quest_id':q,'evidence':evidence})
  if not ok:raise AssertionError((name,str(evidence)[:1000]))
 for d in I.selected(group):
  m,p=I.load(d);M[d]=m;pins.append(p);ck('pinned actual resource '+d,not m['errors'],p)
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def loc(d,gp,i):
  i=str(i);nd=n(d,i,gp);return {'depot':d,'graph':gp,'node':i,'payload':nd['payload'],'payload_sha256':nd['payload_sha256'],'reads':nd['reads'],'writes':nd['writes'],'refs':nd['refs'],'node_refs':nd['node_refs'],'prefabs':nd['prefabs'],'incoming':[e for e in g(d,gp)['edges'] if e[2]==i],'outgoing':[e for e in g(d,gp)['edges'] if e[0]==i]}
 cp=I.W/'prealpha/gigs_u10/native/build/native_06/component.json';pp=I.W/'research/gigs_u10/native/build_plan_01.json';co=I.W/I.D['contract'];plan=I.read(pp);contracts=I.read(co);PM=I.read(I.W/'prealpha/gigs_u10/presentation/build/presentation_03/component.json');mapping=PM['reference_replacements']
 for p in [cp,pp,co,I.W/'prealpha/gigs_u10/presentation/build/presentation_03/component.json']:
  pins.append({'kind':'construction_evidence','path':str(p),'sha256':I.sha(p)})
 for rel in [pp.relative_to(I.W).as_posix(),co.relative_to(I.W).as_posix()]:ck('historical recipe plan pin '+rel,I.sha(I.W/rel)==I.DP[rel],rel)
 # Reuse shared protocol evidence only after exact current-epoch byte applicability.
 shared=I.W/'prealpha/quest_restoration_qr5/groups/G02/shared_core.json';sc=I.read(shared);ap=[]
 for p in sc['sources']:
  if p['depot'] not in I.E['source_resources']:continue
  current=I.C/'archive_source'/p['depot'];ck('shared core current applicability '+p['depot'],I.sha(current)==p['sha256']==I.E['source_resources'][p['depot']],p);ap.append({'depot':p['depot'],'sha256':p['sha256'],'current':str(current)})
 pins.append({'kind':'shared_protocol_evidence','path':str(shared),'sha256':I.sha(shared),'applicability':ap})
 scripts={}
 for name in ['PTFR_GigsU10.reds','PTFR_ActivityStateR3.reds','PTFR_JohnnyVoiceJV1.reds']:
  p=I.C/'package/r6/scripts/PTFR_Consolidated'/name;assert p.is_file(),p;scripts[name]=p.read_text(encoding='utf8');pin=next(x for x in I.E['package_files'] if x['path'].endswith('/'+name));ck('effective script pin '+name,I.sha(p)==pin['sha256'],pin);pins.append({'kind':'effective_script','path':str(p),'sha256':I.sha(p)})
 rt=I.read(I.W/'prealpha/gigs_u10/runtime/build/runtime_02/manifest.json')
 for q in I.ASSIGN[group]:
  rows=[];recipe_results=[];bodies=[];ph=[];rqs=[r for r in I.D['recipes'] if r['id']==q];er=next(r for r in rqs if r['kind']=='entry');job=next(x for x in plan['jobs'] if x['id']==q);owner=next(x for x in contracts['owners'] if x['id']==q);entry=er['depot'];tag=owner['tag'];main=er['native'];qev={'entry':entry,'native_main':main,'recipes':recipe_results,'bodies':bodies,'protocols':ph}
  for r in rqs:
   cur=r['depot'];ck('exact current recipe edges '+cur,g(cur)['edges']==sorted([[str(a),s,str(b),t] for a,s,b,t in r['edges']]),r['edges'],q)
   if not r.get('raw'):continue
   donor='recipe:'+r['raw'];gp=r['graph'];ns=g(donor,gp)['nodes'];diffs=[]
   for ni in r['ids']:
    expected=copy.deepcopy(ns[str(ni)]['payload'])
    if r['kind']=='entry' and ni==job['parent']['input_node']:expected['socketName']['$value']='In1'
    if r['kind']=='entry' and ni==job['parent']['child']['id']:expected['phaseResource']={'DepotPath':{'$type':'ResourcePath','$storage':'string','$value':main},'Flags':'Soft'}
    ck('native node payload '+cur+':'+str(ni),n(cur,ni)['payload']==expected,{'donor':donor,'graph':gp,'node':ni},q)
    pre=gp+'/'+str(ni)
    for p,gr in M[donor]['graphs'].items():
     if p==pre or p.startswith(pre+'/'):
      newgp='root'+p[len(gp):];ck('entire native nested graph '+cur+':'+newgp,g(cur,newgp)==gr,{'donor':donor,'graph':p},q)
   recipe_results.append({'resource':cur,'native':donor,'native_graph':gp,'native_nodes':r['ids'],'edges':r['edges'],'kind':r['kind']})
  # Every companion is compared to its actual native source and entire nested edges.
  for index,c in enumerate(job['companions']):
   d='recipe:'+c['source_raw']
   if d not in M:m,p=I.load(d);M[d]=m;pins.append(p)
   original=copy.deepcopy(n(d,c['source_node'],c['source_graph'])['payload']);original['id']=64000+index
   if c.get('depot'):original['phaseResource']={'DepotPath':{'$type':'ResourcePath','$storage':'string','$value':I.D.get('companion_replacements',{}).get(c['depot'],c['depot'])},'Flags':'Soft'}
   ck('native companion payload '+q+':'+str(index),n(entry,64000+index)['payload']==original,c,q)
   pre=c['source_graph']+'/'+str(c['source_node'])
   for gp,gr in M[d]['graphs'].items():
    if gp==pre or gp.startswith(pre+'/'):ck('native companion graph '+q+gp,g(entry,'root/'+str(64000+index)+gp[len(pre):])==gr,c,q)
  guard=n(entry,65002)['payload']['condition'];f={x['factName']:x['value']+(1 if x['comparisonType']=='Greater' else -1 if x['comparisonType']=='Less' else 0) for x in I.walk(guard) if x.get('$type')=='questVarComparison_ConditionType'};j={x['path']['realPath']:x['state'] for x in I.walk(guard) if x.get('$type')=='questJournalEntryState_ConditionType'};items={str(I.value(x['itemID'])):x['quantity'] for x in I.walk(guard) if x.get('$type')=='questInventory_ConditionType'}
  ck('actual admission positive '+q,ev(guard,f,j,items),{'facts':f,'journals':j,'items':items},q)
  ck('late recheck exact '+q,n(entry,65008)['payload']['condition']==guard and ['65008','True','65003','In'] in g(entry)['edges'] and ['65008','False','65002','In'] in g(entry)['edges'],loc(entry,'root',65008),q)
  for fact in f:
   bad=f.copy();bad[fact]=f[fact]+3;ck('admission contradicted fact rejects '+q+':'+fact,not ev(guard,bad,j,items),{'fact':fact,'value':bad[fact]},q)
  for jp in j:
   bad=j.copy();bad[jp]='Active' if j[jp]!='Active' else 'Succeeded';ck('admission nonfresh journal rejects '+q+jp,not ev(guard,f,bad,items),{'journal':jp,'value':bad[jp]},q)
  for item in items:
   bad=items.copy();bad[item]=1;ck('already held item rejects '+q+item,not ev(guard,f,j,bad),item,q)
  ck('one claim before tier support and body '+q,wr(n(entry,65003),tag+'_Issued',1) and wr(n(entry,65007),'PTFRU9_'+job['region']+'_TierRequest',1) and ['65004','Out',str(job['parent']['child']['id']),er['main_input']] in g(entry)['edges'],loc(entry,'root',65003),q)
  # The actual source-local handler inventory is retained in full, not a fact-name count.
  native_ds=[d for d in M if q in d and d.startswith('base\\open_world\\street_stories')]
  for d in native_ds:
   for gp,gr in M[d]['graphs'].items():
    for ni,nd in gr['nodes'].items():rows.append(loc(d,gp,ni)|{'type':nd['type'],'journal_paths':nd['journal_paths'],'reward':nd['reward'],'sms':nd['sms']})
  facts={w['factName'] for row in rows for w in row['writes']};allj={p for row in rows for p in row['journal_paths']};qev.update(native_handler_count=len(rows),guard=guard,guard_fixture={'facts':f,'journals':j,'items':items},native_fact_writers=sorted(facts),facts_not_zero_guarded=sorted(facts-set(f)),native_journal_paths=sorted(allj),journals_not_guarded=sorted(allj-set(j)),root_prefabs={d:M[d]['root_prefabs'] for d in native_ds})
  # Native original bodies remain exact; compare parent embedded roots where available.
  for donor in [d for d in M if d.startswith('recipe:')]:
   for emb in M[donor].get('embedded_files',[]):
    original=emb['depot']
    if q not in original or original not in M:continue
    pre=emb['graph_prefix']+'/root';a={'graphs':{'root'+p[len(pre):]:gr for p,gr in M[donor]['graphs'].items() if p==pre or p.startswith(pre+'/')},'metadata':emb['metadata'],'metadata_sha256':digest(emb['metadata'])};b=M[original]
    # Handle-envelope externalization is the only permitted vanilla-body delta here.
    def ext(x):
     x=copy.deepcopy(x)
     for z in I.walk(x):
      if z.get('Flags')=='Embedded':z['Flags']='Soft'
      if z.get('cookingPlatform')=='PLATFORM_None':z['cookingPlatform']='PLATFORM_PC'
     return x
    aa=ext(a);aa['metadata_sha256']=digest(aa['metadata']);diff=compare_graph(aa,b);ck('native embedded main full semantics '+original+donor,not diff,{'donor':donor,'prefix':pre,'diff':diff},q);bodies.append({'donor':donor,'standalone':original,'prefix':pre,'graph_count':len(a['graphs']),'allowed_envelope':['Embedded to Soft','cooking None to PC']})
  # Trace actual scene inputs from native phase callers and each request through real listener/ACK.
  contact={'sts_wbr_hil_06':'rogue','sts_wbr_jpn_12':'wakako','sts_std_arr_03':'muamar','sts_wat_nid_07':'reggie'}.get(q,'padre')
  for row in rows:
   for scene in row['refs']:
    if scene not in M or not scene.endswith('.scene') or 'holocall' not in scene:continue
    sg=g(scene,'scene');hc=f'base\\quest\\holocalls\\{contact}\\{contact}_holocall.questphase';hs=hc.replace('.questphase','.scene')
    if hc not in M:issues.append({'quest':q,'kind':'missing_contact_model','controller':hc});continue
    for edge in row['incoming']:
     inp=edge[3]
     if inp not in sg['entries']:continue
     en=sg['entries'][inp]
     for ni,nd in sg['nodes'].items():
      if not path(sg,en,ni):continue
      for w in nd['writes']:
       req=w['factName']
       if w['value']!=1 or not req.endswith('_activate') or not req.startswith(('holo_','audio_')):continue
       ack=req.removesuffix('_activate').replace('audio_','holo_')+'_done';readers=[i for i,x in g(hc)['nodes'].items() if any(r.get('factName')==req for r in x['reads'])];acks=[i for i,x in g(hs,'scene')['nodes'].items() if wr(x,ack,1)];waits=[i for i,x in sg['nodes'].items() if any(r.get('factName')==ack for r in x['reads']) and path(sg,en,i)];clears=[i for i,x in sg['nodes'].items() if wr(x,ack,0) and any(path(sg,wa,i) for wa in waits)]
       ck('caller real native request listener ack wait clear '+q+scene+inp+ni,bool(readers and acks and waits and clears),{'request':req,'producer':ni,'input':inp,'controller':hc,'readers':readers,'ack':ack,'ack_writers':acks,'waits':waits,'clears':clears},q)
       ph.append({'scene':scene,'input':inp,'entry':en,'producer':ni,'request':req,'listener':hc,'readers':readers,'ack_scene':hs,'ack_writers':acks,'ack':ack,'waits':waits,'clears':clears,'caller_direct_wait':any(path(sg,ni,wa) for wa in waits)})
  ph[:]=list({(x['scene'],x['input'],x['producer'],x['request']):x for x in ph}.values());ck('nonempty actual protocol cases '+q,bool(ph),len(ph),q)
  p=O/'quests'/q;I.write(p/'handlers.json',rows);I.write(p/'evidence.json',qev);evidence[q]=qev
 # Mutation controls modify exact raw JSON then independently normalize and compare against native oracle.
 for label,q,field in [('native_admission','sts_hey_gle_03' if group=='C01' else 'sts_wbr_hil_06','q307_done'),('native_reward','sts_hey_rey_02' if group=='C01' else 'sts_std_arr_03','reward'),('phone_ack','sts_hey_gle_05' if group=='C01' else 'sts_wbr_jpn_12','ack')]:
  if q not in evidence:continue
  if field=='q307_done':d=evidence[q]['entry'];fact=field
  elif field=='reward':d=next(d for d in M if q in d and d.startswith('base\\') and any(nn['reward'] and 'QuestRewards.'+q+'_completion' in str(nn['payload']) for gg in M[d]['graphs'].values() for nn in gg['nodes'].values()));fact='QuestRewards.'+q+'_completion'
  else:d=evidence[q]['protocols'][0]['ack_scene'];fact=evidence[q]['protocols'][0]['ack']
  ppn=next(x for x in pins if x.get('depot')==d);raw=copy.deepcopy(I.read(ppn['json']));changed=0
  for x in I.walk(raw):
   if field=='reward' and x.get('$type')=='TweakDBID' and x.get('$value')==fact:x['$value']='QuestRewards.QR6_mutation_missing';changed+=1
   elif field!='reward' and x.get('factName')==fact:x['value']=999;changed+=1
  mm=Resource(raw).normalize();caught=bool(compare_graph(M[d],mm));ck('raw mutation detected '+label,changed>0 and caught,{'depot':d,'field':fact,'changed':changed},q);mp=O/'mutations'/(label+'.json');I.write(mp,raw);mutations.append({'fault':label,'resource':d,'raw_mutant':str(mp),'sha256':I.sha(mp),'caught':caught})
 I.write(O/'tests.json',tests);I.write(O/'source_pins.json',pins);I.write(O/'issues.json',issues);I.write(O/'mutations.json',mutations);I.write(O/'summary.json',{'group':group,'status':'PASS_BOUNDED_SOURCE_COMPARISONS_WITH_EXPLICIT_LIMITS','checks':len(tests),'resources':len(M),'mutations':len(mutations),'quest_ids':I.ASSIGN[group],'issues':issues,'epoch':'QR5:08','gameplay_tested':False})
 print({'group':group,'checks':len(tests),'resources':len(M),'mutations':len(mutations),'issues':issues,'out':str(O)})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--group',required=True);p.add_argument('--output',required=True);a=p.parse_args();run(a.group,Path(a.output))
