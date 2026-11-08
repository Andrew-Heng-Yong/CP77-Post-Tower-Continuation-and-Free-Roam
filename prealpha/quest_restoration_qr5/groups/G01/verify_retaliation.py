"""Fifth Column's actual shared Valentinos consequence, bounded independent proof."""
from pathlib import Path
import argparse,copy,json
import source_inputs as I
from common import walk
from model import Resource,compare_graph
from verify import ev,fixture,path
def run(O):
 assert not O.exists();checks=[]
 def ck(name,ok,e):
  checks.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e));assert ok,(name,e)
 mf=I.W/'research/gig_restoration/special_gigs_u9/manifest.json';historic=I.read(mf)['retaliation'];d=historic['depot'];m,pin=I.load(d);ngpath=I.W/'research/gig_restoration/lifecycle_sources/json/base/open_world/street_stories/street_stories_gang_retaliation.questphase.json';rawpath=I.W/'research/gig_restoration/lifecycle_sources/raw/base/open_world/street_stories/street_stories_gang_retaliation.questphase';pins=historic['source_pins']
 for p in [ngpath,rawpath]:ck('historically pinned native '+p.name,I.sha(p)==pins[p.relative_to(I.W).as_posix()],str(p))
 native=Resource(I.read(ngpath)).normalize();ck('native/current graph decode',not native['errors'] and not m['errors'],dict(native=native['errors'],current=m['errors']))
 def g(gp='root'):return m['graphs'][gp]
 def n(gp,i):return g(gp)['nodes'][str(i)]
 guard=n('root',65001)['payload']['condition'];f=fixture(guard)
 ck('no prior pending retaliation or active chase adopted',ev(guard,f) and not ev(guard,f|{'sts_gang_retaliation_cancel':1}) and not ev(guard,f|{'mws_chase_active':1}),guard)
 cg=n('root/22',64006)['payload']['condition'];cf=fixture(cg);ck('Valentinos fresh claim rejects historical gang pending',ev(cg,cf) and not ev(cg,cf|{'sts_valentinos_retaliation':1}) and not ev(cg,cf|{'PTFRU9_Retaliation_valentinos_Issued':1}),cg)
 ck('common and gang receipts actually precede native startup',all(list(map(str,e)) in g(gp)['edges'] for gp,e in [('root',(65001,'Out',65002,'In')),('root',(65002,'Out',22,'In1')),('root/22',(64006,'Out',64007,'In')),('root/22',(64007,'Out',58,'In')),('root/22',(58,'Out',57,'In')),('root/22',(57,'Out',33,'In1'))]),dict(common=[65001,65002,22],gang=[64006,64007,58,57,33]))
 expected=copy.deepcopy(native)
 # Current consolidated saved-owner wrappers: Fifth Column U9 and Bring Me ... U10.
 # Native inner condition and edges exact; historical 'excluded' label is obsolete.
 adaptations=[]
 for i,fact in [(35,'PTFRU9_sts_hey_gle_04_Started'),(37,'PTFRU10_sts_hey_rey_02_Started')]:
  old=expected['graphs']['root/33/227']['nodes'][str(i)]['payload'];cur=n('root/22/33/227',i)['payload'];c=cur['condition'];ck('native selector retained inside actual owner adapter '+str(i),c['$type']=='questLogicalCondition' and c['operation']=='AND' and len(c['conditions'])==2 and c['conditions'][0]=={'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':fact,'value':1}} and c['conditions'][1]==old['condition'],dict(node=i,owner=fact,old=old['condition'],current=c));old['condition']=c;adaptations.append(dict(node=i,owner=fact))
 a={'graphs':{k[7:]:v for k,v in expected['graphs'].items() if k.startswith('root/33')},'metadata':{},'metadata_sha256':''};b={'graphs':{k[10:]:v for k,v in m['graphs'].items() if k.startswith('root/22/33')},'metadata':{},'metadata_sha256':''};diff=compare_graph(a,b);ck('entire Valentinos native descendant graph after exact two receipt wrappers',not diff,diff)
 ck('root nonterminating shared lifetime',not any(n['type']=='questOutputNodeDefinition' for n in g()['nodes'].values()),dict(edges=g()['edges'],metadata=m['metadata']))
 # Actual raw guard's pending check removed: concrete negative fixture must flip.
 bad=I.read(pin['json']);res=Resource(bad);gr=res.d(res.root['graph']);gn=next(res.d(h) for h in gr['nodes'] if res.d(h).get('id')==65001);cond=res.d(gn['condition']);cond['conditions']=[h for h in cond['conditions'] if 'sts_gang_retaliation_cancel' not in json.dumps(res.d(h))];bm=Resource(bad).normalize();badguard=bm['graphs']['root']['nodes']['65001']['payload']['condition'];mut=not ev(guard,f|{'sts_gang_retaliation_cancel':1}) and ev(badguard,f|{'sts_gang_retaliation_cancel':1}) and bool(compare_graph(m,bm));ck('actual pending-history guard mutation detected',mut,dict(resource=d,node=65001,fact='sts_gang_retaliation_cancel',mutated_value=1))
 evidence=dict(current=pin,native=dict(binary=str(rawpath),sha256=I.sha(rawpath),json=str(ngpath),json_sha256=I.sha(ngpath)),historical_manifest=dict(path=str(mf),sha256=I.sha(mf),limit='Only exact native pins consumed; historical excluded selector37 classification is superseded by actual current U10 owner guard.'),actual_adaptations=adaptations,common_guard=guard,valentinos_guard=cg,valentinos_graphs={k:v for k,v in m['graphs'].items() if k.startswith('root/22/33')},shared_graph=g('root/22'),limits=['Only Valentinos descendant parity investigated, not other five gangs.','Content-lock/proximity conditions and DynamicSpawn actors/placement, actual chase/delivery/interrupt scheduling require engine evidence.','Receipt precedes native activation; no claim listener is running synchronously.','Current U10 sibling selector ownership is recorded without asserting that historical excluded label remains current.'])
 I.write(O/'evidence.json',evidence);I.write(O/'tests.json',dict(status='PASS_BOUNDED_VALENTINOS_SOURCE_CHECKS',count=len(checks),checks=checks,mutations=[dict(fault='actual missing historical pending guard',detected=mut)],code_sha256=I.sha(__file__),evidence_sha256=I.sha(O/'evidence.json')));return dict(checks=len(checks),mutations=1)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(run(Path(a.output).resolve())))
