"""QR5 second Arroyo source contracts; writes evidence only below --out."""
import sys,copy,json,argparse
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
import collections
def path(g,a,b):
 q=collections.deque([[str(a)]]);seen={str(a)}
 while q:
  p=q.popleft()
  if p[-1]==str(b):return p
  for x,s,y,t in g['edges']:
   cut=g['nodes'].get(x,{}).get('type')=='scnCutControlNode'and s.startswith('1:')
   if x==p[-1]and s!='CutSource'and t!='CutDestination'and not cut and y not in seen:seen.add(y);q.append(p+[y])
 return None
from common import read,write,sha,walk
from model import Resource,compare_graph,digest
def ext(x):
 if isinstance(x,list):return [ext(v)for v in x]
 if isinstance(x,dict):
  o={k:ext(v)for k,v in x.items()}
  if 'DepotPath'in o and o.get('Flags')=='Embedded':o['Flags']='Soft'
  if o.get('$type')=='questQuestPhaseResource'and o.get('cookingPlatform')=='PLATFORM_None':o['cookingPlatform']='PLATFORM_PC'
  return o
 return x
def ev(c,f):
 t=c['$type']
 if t=='questLogicalCondition':
  r=[ev(x,f)for x in c['conditions']];return all(r)if c['operation']=='AND'else any(r)if c['operation']=='OR'else not any(r)if c['operation']=='NOR'else False
 if t=='questFactsDBCondition':return ev(c['type'],f)
 if t=='questVarComparison_ConditionType':
  if c['factName']not in f:return False
  a,b=f[c['factName']],c['value'];return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b}[c['comparisonType']]
 raise ValueError(t)
def run(O):
 assert not O.exists();M={};pins=[];tests=[];mut=[]
 def ck(name,ok,evidence):tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':evidence});assert ok,name
 for d in I.selected():
  m,p=I.load(d);M[d]=m;pins.append(p);ck('source_pin '+d,True,p);ck('graph_integrity '+d,not m['errors'],m['errors'])
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def e(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(d,gp)['edges']
 def wr(d,i,f,v,gp='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(d,i,gp)['writes'])
 def find(tail):return next(d for d in M if d.endswith('\\'+tail))
 cp=H.parent/'G04/shared_core.json';core=read(cp);ck('Muamar_core_frozen',sha(cp)=='E18670F1292E0AB60C325EFCA7151F46107E79B58769E9C6B4DAE7BA985142AC'and sha(core['tests'])==core['tests_sha256']and sha(core['source_pins'])==core['source_pins_sha256'],{'path':str(cp),'sha256':sha(cp),'checks':core['checks']})
 bodies=[]
 for d in [d for d in M if d.startswith('recipe:')]:
  for item in M[d]['embedded_files']:
   nd=item['depot']
   if nd not in M or not any(q in nd for q in I.Q):continue
   pre=item['graph_prefix']+'/root';graphs={'root'+gp[len(pre):]:gr for gp,gr in M[d]['graphs'].items()if gp==pre or gp.startswith(pre+'/')};orig={'graphs':graphs,'metadata':item['metadata'],'metadata_sha256':digest(item['metadata'])};adapt=ext(copy.deepcopy(orig));adapt['metadata_sha256']=digest(adapt['metadata'])
   ck('embedded_body_native_semantics '+nd,not compare_graph(adapt,M[nd]),{'original':d,'prefix':pre,'allowed_envelope':['Embedded→Soft handles','cookingPlatform None→PC'],'root_prefabs':item['root_prefabs']});bodies.append({'depot':nd,'donor':d,'prefix':pre,'allowed_envelope':['Embedded→Soft','None→PC'],'differences_before_envelope':compare_graph(orig,M[nd]),'differences_after_envelope':compare_graph(adapt,M[nd]),'root_prefabs':item['root_prefabs']})
 for r in I.RECIPES:
  cur=r['depot'];don='recipe:'+r['raw'];gp=r['graph'];cg='root/9'if r['id']=='sts_std_arr_06'else'root'
  for ni in r['ids']:
   if ni==0:continue
   ck('recipe_payload '+cur+':'+str(ni),n(cur,ni,cg)['payload']==ext(n(don,ni,gp)['payload']),{'donor':don,'graph':gp,'node':ni})
   pre=cg+'/'+str(ni);np=gp+'/'+str(ni)
   for child,gr in M[cur]['graphs'].items():
    if child==pre or child.startswith(pre+'/'):ck('recipe_nested '+cur+child,gr==g(don,np+child[len(pre):]),{'native':np+child[len(pre):]})
  ck('recipe_exact_edges '+cur,g(cur,cg)['edges']==sorted([[str(a),s,str(b),t]for a,s,b,t in r['edges']]),r['edges'])
 script=I.C/'package/r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds';s=script.read_text(encoding='utf8');pins.append({'path':str(script),'sha256':sha(script)});cl=s[s.index('class NativeGigDataU9'):];line=next(x for x in cl.splitlines()if'func IDs()'in x);ids=json.loads(line[line.index('['):line.rindex(']')+1])
 def array(method,i):
  b=cl[cl.index('public static func '+method+'('):];b=b[:b.index('\n  public static func',1)];l=next(x for x in b.splitlines()if'if i=='+str(i)+' 'in x);return json.loads(l[l.index('['):l.rindex(']')+1])
 admission=[];inventory={};protocol=[]
 for q in I.Q:
  i=ids.index(q);data={k:array(k,i)for k in ['Paths','Classes','Facts','TerminalFacts']};entry='towercontinued\\native_gigs_u9\\'+q+'_entry.questphase';gp='root/9'if q=='sts_std_arr_06'else'root';node=n(entry,65002,gp);cond=node['payload']['condition'];fs={x['factName']:x['value']for x in node['reads']if'factName'in x};ck('actual_guard_positive '+q,ev(cond,fs),fs)
  for fact,value in [('q307_done',0),('q307_finished',0),('PTFRU9_Support_Issued',0),('PTFRU9_'+q+'_ParentEntered',1),('PTFRU9_'+q+'_Fault',1),('PTFRU7_Support_Issued',1),('PTFRU6_Padre_Issued',1)]:ck('actual_guard_reject '+q+fact,not ev(cond,fs|{fact:value}),{'fact':fact,'value':value})
  factrows={};jp={};rows=[];prefix=q.replace('sts_std_','')
  for d,m in M.items():
   if not d.startswith('base\\open_world')or q not in d:continue
   for ng,gr in m['graphs'].items():
    for ni,nd in gr['nodes'].items():
     row={'depot':d,'graph':ng,'node':ni,'type':nd['type'],'payload_sha256':nd['payload_sha256'],'reads':nd['reads'],'writes':nd['writes'],'journal_paths':nd['journal_paths'],'refs':nd['refs'],'prefabs':nd['prefabs'],'node_refs':nd['node_refs'],'incoming':[x for x in gr['edges']if x[2]==ni],'outgoing':[x for x in gr['edges']if x[0]==ni]};rows.append(row)
     for w in nd['writes']:
      if prefix in w['factName']:factrows.setdefault(w['factName'],[]).append(row)
     for x in walk(nd['payload']):
      if x.get('$type')=='gameJournalPath'and x.get('realPath','').startswith('quests/'):
       p=x['realPath'];jp.setdefault(p,[]).append({'depot':d,'graph':ng,'node':ni,'class':x.get('className',{}).get('$value'),'type':nd['type'],'incoming':row['incoming']})
  omittedfacts={f:r for f,r in factrows.items()if f not in data['Facts']};omittedpaths={p:r for p,r in jp.items()if p not in data['Paths']};admission.append({'quest_id':q,'index':i,**data,'guard':cond,'positive_fixture':fs,'all_local_writers':factrows,'omitted_native_facts':omittedfacts,'omitted_native_journal':omittedpaths});inventory[q]=rows
  missing={f for f in factrows if f.startswith(prefix+'_')and f not in data['Facts']};expected=set();ck('exact_local_fact_guard_coverage '+q,missing==expected and not omittedfacts,{'missing_local_progress_facts':sorted(missing),'omitted_other_namespace':list(omittedfacts),'paths_omitted':list(omittedpaths),'limit':'Every discovered local gig writer is covered by the exact current fact list. Omitted journal targets are classified independently; zero scalar values alone do not prove history.'})
  for d,m in M.items():
   if q not in d or not d.endswith('.scene'):continue
   gr=g(d,'scene')
   for ni,nd in gr['nodes'].items():
    for w in nd['writes']:
     if not(w['factName'].startswith(('holo_muamar_','holo_rogue_','audio_v_calls_karl_ginsky_'))and w['factName'].endswith('_activate')and w['value']==1):continue
     done=w['factName'][:-9].replace('audio_','holo_')+'_done';entries=list(gr['entries'].values());waits=[a for a,x in gr['nodes'].items()if any(z.get('factName')==done for z in x['reads'])and(any(path(gr,en,a)for en in entries))];clear=[a for a,x in gr['nodes'].items()if any(z.get('factName')==done and z.get('value')==0 for z in x['writes'])and any(path(gr,wa,a)for wa in waits)];direct=[a for a in waits if path(gr,ni,a)];forks=[a for a in gr['nodes']if len([z for z in gr['edges']if z[0]==a])>1 and path(gr,a,ni)and any(path(gr,a,wa)for wa in waits)]
     ck('caller_real_wait_clear '+d+ni,bool(waits)and bool(clear)and(bool(direct)or bool(forks)),{'request':ni,'fact':w['factName'],'waits':waits,'clears':clear,'direct_waits':direct,'parallel_forks':forks});protocol.append({'depot':d,'producer':ni,'fact':w['factName'],'waits':waits,'clears':clear,'direct_waits':direct,'parallel_forks':forks})
 ck('EntrySafe_policy',all(x in s for x in ['if this.State(paths[k],classes[k])!=1','if this.Fact(a[k])!=0','return poi==1 || poi==2;']),'Inactive listed journals, zero progress; native POI may already be Active')
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'admission.json',admission);write(O/'handler_inventory.json',inventory);write(O/'protocols.json',protocol);write(O/'embedded_bodies.json',bodies);write(O/'summary.json',{'checks':len(tests),'resources':len(M),'quests':I.Q});print({'checks':len(tests),'resources':len(M),'out':str(O)})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);run(Path(p.parse_args().out))
