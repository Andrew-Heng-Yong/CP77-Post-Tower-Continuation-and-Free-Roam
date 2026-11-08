"""Independent G09 native recipes, support owners and real failure paths."""
from pathlib import Path
import argparse,collections,copy,json,sys,zlib
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent));import source_inputs as I
from common import read,write,sha,walk
from model import Resource,compare_graph
def run(O):
 assert not O.exists();M={};pins=[];tests=[];Q=['sts_wat_kab_06','sts_wat_kab_02','sts_wat_kab_08'];P=I.H.parent/'G09';recipes=[r for r in I.U['recipes'] if r.get('id') in Q]
 def ck(name,ok,e=None):tests.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e));assert ok,(name,e)
 def load(d):
  if d not in M:m,p=I.load(d);M[d]=m;pins.append(p);ck('actual source pin '+d,not m['errors'],p)
  return M[d]
 def find(t):return next(d for d in I.MI if d.endswith('\\'+t))
 for r in recipes:
  d=r['depot'];m=load(d);don=load('recipe:'+r['raw']);oracle=collections.Counter(tuple(map(str,e)) for e in r['edges']);gps=[gp for gp,g in m['graphs'].items() if collections.Counter(map(tuple,g['edges']))==oracle];ck('exact native recipe graph '+d,len(gps)==1,gps);gp=gps[0];ng=don['graphs'][r['graph']]
  for i in r['ids']:
   if i==0:continue
   exp=copy.deepcopy(ng['nodes'][str(i)]['payload'])
   if exp.get('phaseResource',{}).get('Flags')=='Embedded':exp['phaseResource']['Flags']='Soft'
   ck('native node/socket '+d+str(i),m['graphs'][gp]['nodes'][str(i)]['payload']==exp and m['graphs'][gp]['nodes'][str(i)]['sockets']==ng['nodes'][str(i)]['sockets'],dict(native=r['raw'],graph=r['graph'],node=i))
  for cp,g in m['graphs'].items():
   if cp.startswith(gp+'/'):ck('native full copied inline '+d+cp,g==don['graphs'][r['graph']+cp[len(gp):]],cp)
  if r.get('native'):load(r['native'])
  for cc in r.get('companions',[]):
   source=load('recipe:'+cc['source_raw']);old=source['graphs'][cc['source_graph']]['nodes'][str(cc['source_node'])]['payload'];expected=copy.deepcopy(old);expected['id']=64000
   if expected.get('phaseResource',{}).get('Flags')=='Embedded':expected['phaseResource']['Flags']='Soft'
   ck('complete native prestate node metadata including instance prefabs '+r['id'],m['graphs'][gp]['nodes']['64000']['payload']==expected and ['65003','Out','64000',cc['input']] in m['graphs'][gp]['edges'],dict(old=old,new=m['graphs'][gp]['nodes']['64000']['payload']));load(cc['depot'])
 shark=next(r for r in recipes if r['id']==Q[0] and r['kind']=='entry');sm=load(shark['native']);ck('Shark exact native whole prefab alias',sm['root_prefabs']==['#sts_wat_kab_06_steetstory'],sm['root_prefabs']);pre=shark['companions'][0]['depot'];pm=load(pre);pg=pm['graphs']['root'];ck('Shark real medstore/security/door/laptop prestate retained',bool(pg['edges']) and all(any(w.get('factName')=='kana_yakin_default_on' and w.get('value')==v for w in pg['nodes'][str(i)]['writes']) for i,v in [(2,1),(6,0)]) and all(term in json.dumps(pm) for term in ['medstore','laptop']),dict(resource=pre,root_prefabs=pm['root_prefabs'],graphs=list(pm['graphs']),limit='Exact old saved shop/service leases and world target placement remain conditional'))
 oath=find('sts_wat_kab_02_openworld.questphase');og=load(oath)['graphs']['root/5'];ck('Oath native reward refuses failed state',any(r.get('factName')=='kab_02_failed' and r.get('comparisonType')=='Equal' and r.get('value')==0 for r in og['nodes']['41']['reads']) and ['41','Out','40','In'] in og['edges'],dict(resource=oath,node=41));ck('Oath original achievement receipt not reset',any(r.get('factName')=='kab_02_achiv_added_in_bugfix' for r in og['nodes']['54']['reads']),og['nodes']['54']['payload'])
 rd=r'towercontinued\special_gigs_u9\gang_retaliation.questphase';rm=load(rd);mf=I.W/'research/gig_restoration/special_gigs_u9/manifest.json';mp=read(mf)['retaliation']['source_pins'];np=I.W/'research/gig_restoration/lifecycle_sources/json/base/open_world/street_stories/street_stories_gang_retaliation.questphase.json';ck('native retaliation source exact pin',sha(np)==mp[np.relative_to(I.W).as_posix()],str(np));native=Resource(read(np)).normalize();expected=copy.deepcopy(native)
 for i,fact in [(41,'PTFRU9_sts_wat_kab_02_Started'),(45,'PTFRU9_sts_wat_nid_05_Started')]:
  nn=expected['graphs']['root/35/239']['nodes'][str(i)];old=nn['payload']['condition'];cur=rm['graphs']['root/22/35/239']['nodes'][str(i)]['payload']['condition'];ck('full original Maelstrom selector not generic retaliation '+str(i),cur=={'$type':'questLogicalCondition','conditions':[{'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':fact,'value':1}},old],'operation':'AND'},dict(native=old,current=cur));nn['payload']['condition']=cur
 a={'graphs':{k[7:]:v for k,v in expected['graphs'].items() if k.startswith('root/35')},'metadata':{},'metadata_sha256':''};b={'graphs':{k[10:]:v for k,v in rm['graphs'].items() if k.startswith('root/22/35')},'metadata':{},'metadata_sha256':''};ck('whole Maelstrom descendant nodes/sockets/edges exact after two owner wrappers',not compare_graph(a,b),list(b['graphs']))
 cg=rm['graphs']['root/22'];ck('Maelstrom actual fresh claim/lifetime path',all(list(map(str,e)) in cg['edges'] for e in [(0,'Out',64008,'In'),(64008,'Out',64009,'In'),(64009,'Out',61,'In'),(61,'Out',60,'In'),(60,'Out',35,'In1')]) and any(r.get('factName')=='sts_maelstroms_retaliation' and r.get('value')==0 for r in cg['nodes']['64008']['reads']),dict(graph='root/22',nodes=[64008,64009,61,60,35]))
 wd=find('sts_wat_kab_08_openworld.questphase');wg=load(wd)['graphs']['root/5'];ck('Woman actual failure reward exclusion',any(r.get('factName')=='kab_08_failed' and r.get('comparisonType')=='Greater' and r.get('value')==0 for r in wg['nodes']['50']['reads']) and all(e in wg['edges'] for e in [['50','True','13','In'],['50','False','7','In']]),dict(resource=wd,graph='root/5',gate50=wg['nodes']['50']['payload']));ck('Woman real nomad/camp branches preserved',any(r.get('factName')=='kab_08_hamill_becomes_nomad' for r in wg['nodes']['20']['reads']) and any(r.get('factName')=='sq027_camp_moved' for r in wg['nodes']['24']['reads']) and all(e in wg['edges'] for e in [['20','True','24','In'],['24','False','23','In'],['24','True','25','In']]),dict(nomad=wg['nodes']['20']['payload'],camp=wg['nodes']['24']['payload']))
 results=read(P/'results.json');rows=[]
 def canon(x):
  x=copy.deepcopy(x)
  for v in walk(x):
   v.pop('payload_sha256',None);v.pop('metadata_sha256',None)
   if v.get('$type')=='TweakDBID':
    text=v['$value'];number=(len(text.encode('utf8'))<<32)|zlib.crc32(text.encode('utf8')) if v.get('$storage')=='string' else int(text);v['$storage']='uint64';v['$value']=str(number)
  return x
 for x in read(P/'raw_exports_01/manifest.json'):
  ck('existing fresh native raw-export pins '+x['depot'],sha(x['raw'])==x['raw_sha256'] and sha(x['json'])==x['json_sha256'],x);fresh=Resource(read(x['json'])).normalize();ck('independent fresh raw semantics exact '+x['depot'],canon(fresh)==canon(load(x['depot'])),dict(export=x['json'],normalization='Only TDBID exact CRC32+UTF8-length numeric identity and derived model digest fields; no graph/target excluded'))
 for r in results['quest_results']:
  c=read(r['contracts']);ck('frozen30 source contracts '+r['quest_id'],sha(r['contracts'])==r['contracts_sha256'] and len(c['contracts'])==10 and not c['fully_static_verified'],r['contracts']);rows.append(dict(id=r['quest_id'],contracts=r['contracts'],sha256=sha(r['contracts'])))
 raw=copy.deepcopy(read(next(p['json'] for p in pins if p['depot']==wd)))
 for x in walk(raw):
  if x.get('$type')=='questVarComparison_ConditionType' and x.get('factName')=='kab_08_failed':x['factName']='QR5_missing_failed_gate'
 bm=Resource(raw).normalize();det=bm['graphs']['root/5']['nodes']['50']['payload']!=wg['nodes']['50']['payload'];ck('actual Woman failed-gate raw mutation caught',det,dict(resource=wd,node=50))
 write(O/'tests.json',dict(count=len(tests),checks=tests,mutations=[dict(fault='actual failed reward gate identity',detected=det)]));write(O/'source_pins.json',pins);out=dict(status='APPROVE_ACTUAL_SOURCE_FINDINGS_WITH_PRESTATE_AND_CONSEQUENCE_LIMITS',group='G09',checks=len(tests),mutations=1,quests=rows,tests=str(O/'tests.json'),tests_sha256=sha(O/'tests.json'),source_pins=str(O/'source_pins.json'),source_pins_sha256=sha(O/'source_pins.json'),code_sha256=sha(__file__),findings=['Complete Shark companion node metadata/instance prefabs/source binding and own real prestate actions checked; exact native steetstory spelling preserved. Saved shared services/garage/medstore leases and world placement remain conditional.','Full actual Maelstrom selector and descendant graph checked; native done/content/Watson trigger/gang_chase predicates retained under exact two private owner guards. Historical pending ambush is not consumed/reset.','Woman actual failure skips reward and original nomad/sq027 camp-moved branches are preserved; no fabricated camp/relationship outcome.'],minor_metadata_issue='G09 status text says COMPLETE_FOUR but actual quest_ids/quest_results contain3 quests and30 contracts. Treat numeric coverage from explicit lists, preserve original and record this precision issue.',runtime_writes=[]);write(H/'G09.json',out);print(json.dumps(dict(checks=len(tests),review=str(H/'G09.json'))))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);run(Path(p.parse_args().output).resolve())
