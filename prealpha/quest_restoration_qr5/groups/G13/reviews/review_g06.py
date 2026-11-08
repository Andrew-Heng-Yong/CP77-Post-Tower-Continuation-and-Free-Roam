"""Independent G06 raw-source/known-diagnostic review, no peer checker imports."""
from pathlib import Path
import argparse,collections,copy,gzip,json,sys
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent));import source_inputs as I
from common import read,write,sha,walk
from model import Resource,compare_graph
def path(g,a,b):
 todo=collections.deque([[str(a)]]);seen={str(a)}
 while todo:
  p=todo.popleft()
  if p[-1]==str(b):return p
  for x,so,y,si in g['edges']:
   if x==p[-1] and so!='CutSource' and si!='CutDestination' and not(g['nodes'][x]['type']=='scnCutControlNode' and so.startswith('1:')) and y not in seen:seen.add(y);todo.append(p+[y])
 return None
def run(O):
 assert not O.exists();M={};pins=[];tests=[];Q=['sts_std_rcr_02','sts_std_rcr_05','sts_std_rcr_01','sts_std_rcr_03'];P=I.H.parent/'G06';rr=[r for r in I.U['recipes'] if r.get('id') in Q]
 def ck(name,ok,e=None):tests.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e));assert ok,(name,e)
 def load(d):
  if d not in M:
   if d.endswith(r'\sts_std_rcr_02\phases\sts_std_rcr_02_phase.questphase'):
    row=I.IDX[d];j=Path(row['json']);raw=j.with_suffix('')
    if not raw.exists():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
    ck('actual RCR02 raw byte pin',sha(raw)==row['sha256'],str(raw));m=Resource(read(j)).normalize();cached=json.loads(gzip.decompress(Path(I.MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[]);ck('native diagnostic tuple/list JSON-equivalent model',json.loads(json.dumps(m))==cached,dict(limit='Only canonicalizes error endpoint tuple/list serialization; no graph/error omitted'))
    p=dict(depot=d,binary=str(raw),sha256=sha(raw),json=str(j),json_sha256=sha(j),model=I.MI[d]['normalized_model'],model_sha256=sha(I.MI[d]['normalized_model']))
   else:m,p=I.load(d)
   M[d]=m;pins.append(p);allowed=bool(m['errors']) and all(x.get('kind')=='DANGLING_EDGE' and ('sts_std_rcr_02_phase.questphase/root' in x.get('graph','') or x.get('graph')=='root') for x in m['errors']) and len(m['errors'])==4;ck('pinned source with explicit scoped diagnostics '+d,not m['errors'] or allowed,dict(pin=p,known_RCR02_diagnostics=m['errors']))
  return M[d]
 def find(t):return next(d for d in I.MI if d.endswith('\\'+t))
 for r in rr:
  d=r['depot'];m=load(d);don=load('recipe:'+r['raw']);ee=collections.Counter(tuple(map(str,e)) for e in r['edges']);gps=[p for p,g in m['graphs'].items() if collections.Counter(map(tuple,g['edges']))==ee];ck('fixed exact native recipe topology '+d,len(gps)==1,gps);gp=gps[0];ng=don['graphs'][r['graph']]
  for i in r['ids']:
   if i==0:continue
   exp=copy.deepcopy(ng['nodes'][str(i)]['payload'])
   if exp.get('phaseResource',{}).get('Flags')=='Embedded':exp['phaseResource']['Flags']='Soft'
   ck('exact source node/socket '+d+str(i),m['graphs'][gp]['nodes'][str(i)]['payload']==exp and m['graphs'][gp]['nodes'][str(i)]['sockets']==ng['nodes'][str(i)]['sockets'],dict(native=r['raw'],graph=r['graph'],node=i))
  for cp,g in m['graphs'].items():
   if cp.startswith(gp+'/'):ck('exact copied inline '+d+cp,g==don['graphs'][r['graph']+cp[len(gp):]],cp)
  if r.get('native'):load(r['native'])
 d=find('sts_std_rcr_02_dixon.scene');g=load(d)['graphs']['scene'];c=g['nodes']['86']['payload']['questNode']['condition']['type'];ck('Dixon exact missing-stock inventory predicate',c['$type']=='questInventory_ConditionType' and c['isPlayer']==1 and c['quantity']==1 and c['comparisonType']=='GreaterOrEqual' and c['itemID']['$value']=='114327022403',c)
 ck('Dixon actual inventory fallback routing',all(e in g['edges'] for e in [['86','0:0','158','0:0'],['86','0:1','152','0:1'],['158','0:0','6','0:0']]) and bool(path(g,152,6)) and bool(path(g,152,82)),dict(fallback_to_choice=path(g,152,6),fallback_to_ready=path(g,152,82),limit='MAY path through actual guard/choice, not guaranteed execution'))
 en=g['nodes']['152']['payload']['questNode']['condition']['type'];ck('Dixon fallback requires actual enemy005 incapacitation',en['defeated']==1 and en['killed']==1 and en['unconscious']==1 and en['objectRef']['names'][0]['$value']=='enemy_005',en)
 stock=I.F/'shared/tdb_applicability_02/sts_std_rcr_02.json';st=read(stock);ck('missing stock remains visible',next(x for x in st['targets'] if x['id']=='114327022403')['exists_in_stock'] is False,dict(path=str(stock),sha256=sha(stock)))
 r2=find('sts_std_rcr_02_phase.questphase');body=load(r2);ck('four inherited exact RCR02 root diagnostics retained',len(body['errors'])==4 and {tuple(x['to']) for x in body['errors']}=={('11','In'),('13','In'),('15','In'),('2','In')},body['errors']);ck('partial native body active inputs remain',all(e in body['graphs']['root']['edges'] for e in [['0','Out','17','In'],['17','False','8','In1'],['17','False','9','In1']]),body['graphs']['root']['edges'])
 a3=find('sts_std_rcr_03_openworld.questphase');g3=load(a3)['graphs']['root/4'];cut=copy.deepcopy(g3);cut['edges']=[e for e in cut['edges'] if e[0]!='197'];ck('GoingAway actual Active objective dominated by guarded start197',bool(path(g3,0,195)) and path(cut,0,195) is None and any(w.get('factName')=='rcr_03_start' and w.get('value')==1 for w in g3['nodes']['197']['writes']),dict(path=path(g3,0,195),removed_outgoing197_path=None,limit='Only current native graph domination; old/external writers not inferred absent'))
 b3=find('sts_std_rcr_03_bugfixing.questphase');bug=load(b3);ck('GoingAway force-end/nomad helpers are immediate snapshot conditions',all(bug['graphs']['root/8']['nodes'][str(i)]['type']=='questConditionNodeDefinition' for i in [4,16,18]) and bug['graphs']['root/37']['nodes']['14']['type']=='questConditionNodeDefinition',dict(force_end_graph='root/8',nomad_graph='root/37',not_future_monitor='No passive new controller enrollment justified solely from these old conditions'))
 loop='recipe:research/gig_restoration/lifecycle_sources/raw/base/open_world/street_stories/street_stories_new_fixer_loop.questphase';lg=load(loop)['graphs']['root/2/3'];ck('Union exact native credit disconnection',any(x.get('factName')=='rcr_01_finished' for x in lg['nodes']['7']['reads']) and not any(e[0]=='7' for e in lg['edges']) and not any(r['id']=='sts_std_rcr_01' and r['kind']=='credit' for r in rr),dict(wait=lg['nodes']['7']['payload'],outgoing=[]))
 init=r'towercontinued\gig_phone_u9\fixer_initializer.questphase';rog=r'base\quest\holocalls\rogue\rogue_holocall.questphase';ck('Union actual Rogue caller owner distinct from Muamar',load(init)['graphs']['root']['nodes']['86']['refs']==[rog],dict(initializer=86,controller=rog))
 adp=P/'addenda/reference_precision_01.json';ad=read(adp);ck('preserved G06 precision addendum exact frozen result pin',sha(P/'results.json')==ad['results_sha256'],dict(path=str(adp),sha256=sha(adp)));b1=load(find('sts_std_rcr_01_bugfixing.questphase'));allfacts={r.get('factName') for gg in b1['graphs'].values() for n in gg['nodes'].values() for r in n['reads']+n['writes']};ck('exact Union CYB receipts verified not shorthand',set(ad['correction']['exact_source_receipts'])<=allfacts,ad['correction']['exact_source_receipts'])
 rows=[];results=read(P/'results.json')
 for r in results['quest_results']:
  c=read(r['contracts']);ck('frozen40contract rows '+r['quest_id'],sha(r['contracts'])==r['contracts_sha256'] and len(c['contracts'])==10 and not c['fully_static_verified'],r['contracts']);rows.append(dict(id=r['quest_id'],contracts=r['contracts'],sha256=sha(r['contracts'])))
 raw=copy.deepcopy(read(next(p['json'] for p in pins if p['depot']==d)))
 for x in walk(raw):
  if x.get('$type')=='questInventory_ConditionType' and x.get('itemID',{}).get('$value')=='114327022403':x['quantity']=999
 bm=Resource(raw).normalize();det=bm['graphs']['scene']['nodes']['86']['payload']!=M[d]['graphs']['scene']['nodes']['86']['payload'];ck('actual raw Dixon inventory predicate mutation caught',det,dict(resource=d,node=86,quantity=999))
 write(O/'source_pins.json',pins);write(O/'tests.json',dict(count=len(tests),checks=tests,mutations=[dict(fault='Dixon raw quantity predicate',detected=det)]));out=dict(status='APPROVE_SOURCE_FINDINGS_WITH_NATIVE_UNKNOWN_OPAQUE_AND_ADDENDUM_LIMITS',group='G06',checks=len(tests),mutations=1,quests=rows,tests=str(O/'tests.json'),tests_sha256=sha(O/'tests.json'),source_pins=str(O/'source_pins.json'),source_pins_sha256=sha(O/'source_pins.json'),addendum=str(adp),addendum_sha256=sha(adp),code_sha256=sha(__file__),findings=['Dixon missing114327022403 is player inventory predicate; native guard-incapacitation fallback to same choice/ready exists. This narrows total-block claims while item semantics/record provenance remains UNKNOWN.','Four original RCR02 dangling sources are explicitly OPAQUE; active main branch preserved, no blanket full-graph validity.','GoingAway real Active omitted objective195 is dominated by guarded start197 in current graph. Historical/external state remains conditional. Old snapshot repair conditions do not justify ARR12-style future monitor patch.','Union native disconnected credit wait7 and no current private credit match; no invented district accounting. Exact CYB receipt addendum independently pinned and preserved.'],runtime_writes=[]);write(H/'G06.json',out);print(json.dumps(dict(checks=len(tests),review=str(H/'G06.json'))))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);run(Path(p.parse_args().output).resolve())
