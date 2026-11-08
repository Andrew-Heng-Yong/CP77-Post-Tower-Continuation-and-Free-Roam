"""Independent G05 actual resource review; no peer/root checker imports."""
from pathlib import Path
import argparse,collections,copy,json,sys
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent));import source_inputs as I
from common import read,write,sha,walk
from model import reachable
def run(O):
 assert not O.exists();M={};pins=[];checks=[];Q=['sts_std_arr_05','sts_std_arr_06','sts_std_arr_01'];P=I.H.parent/'G05';recipes=[r for r in I.U['recipes'] if r.get('id') in Q]
 def ck(name,ok,e=None):checks.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e));assert ok,(name,e)
 def load(d):
  if d not in M:m,p=I.load(d);M[d]=m;pins.append(p);ck('actual raw/current pin '+d,not m['errors'],p)
  return M[d]
 def find(tail):return next(d for d in I.MI if d.endswith('\\'+tail))
 for r in recipes:
  d=r['depot'];m=load(d);orig=load('recipe:'+r['raw']);oracle=collections.Counter(tuple(map(str,e)) for e in r['edges']);gps=[gp for gp,g in m['graphs'].items() if collections.Counter(map(tuple,g['edges']))==oracle];ck('fixed native recipe graph routed '+d,len(gps)==1,gps);gp=gps[0];ng=orig['graphs'][r['graph']]
  for i in r['ids']:
   if i==0:continue
   exp=copy.deepcopy(ng['nodes'][str(i)]['payload'])
   if exp.get('phaseResource',{}).get('Flags')=='Embedded':exp['phaseResource']['Flags']='Soft'
   ck('native old node/socket '+d+str(i),m['graphs'][gp]['nodes'][str(i)]['payload']==exp and m['graphs'][gp]['nodes'][str(i)]['sockets']==ng['nodes'][str(i)]['sockets'],dict(native=r['raw'],graph=r['graph'],node=i))
  for cp,g in m['graphs'].items():
   if cp.startswith(gp+'/'):ck('full copied native inline '+d+cp,g==orig['graphs'][r['graph']+cp[len(gp):]],cp)
  if r.get('native'):load(r['native'])
 a5=find('sts_std_arr_05_openworld.questphase');b5=find('sts_std_arr_05_bugfixing.questphase');a6=find('sts_std_arr_06_ow.questphase');a1=find('sts_std_arr_01_openworld.questphase')
 for d in [a5,b5,a6,a1]:load(d)
 ck('BreakingNews old security predicate already owned in body',M[b5]['graphs']['root/15']['nodes']['4']['payload']['condition']==M[a5]['graphs']['root/3']['nodes']['347']['payload']['condition'] and '347' in M[a5]['graphs']['root/3']['reachable'] and ['347','Out','341','In'] in M[a5]['graphs']['root/3']['edges'],dict(old_resource=b5,old_graph='root/15',old_node=4,current_graph='root/3',current_node=347))
 for old,new in [(5,45),(6,46)]:ck('BreakingNews exact old Fox cleanup action duplicate '+str(old),M[b5]['graphs']['root/6']['nodes'][str(old)]['payload']['actions']==M[a5]['graphs']['root/4/6']['nodes'][str(new)]['payload']['actions'],dict(old_graph='root/6',old_node=old,current_graph='root/4/6',current_node=new))
 ck('SeriousEffects original current lab receipt',any(w.get('factName')=='sts_std_arr_01_patch_1_lab' and w.get('value')==1 for w in M[a1]['graphs']['root/5']['nodes']['381']['writes']),dict(resource=a1,graph='root/5',node=381))
 kp=r'towercontinued\phone_support_ph1\karl_ginsky.questphase';kh=r'base\quest\holocalls\karl_ginsky\karl_ginsky_holocall.questphase';ks=kh.replace('.questphase','.scene');init=r'towercontinued\gig_phone_u9\fixer_initializer.questphase';cle=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase';rh=r'base\quest\holocalls\rogue\rogue_holocall.questphase'
 for d in [kp,kh,ks,init,cle,rh]:load(d)
 ck('NastyHangover actual PH1 Karl listener and private receipt',M[kp]['graphs']['root']['nodes']['10']['refs']==[kh] and any(w.get('factName')=='PTFRPH1_karl_ginsky_Issued' and w.get('value')==1 for w in M[kp]['graphs']['root']['nodes']['4']['writes']),dict(resource=kp,nodes=[4,10]))
 er=load(r'towercontinued\native_gigs_u9\sts_std_arr_06_entry.questphase');ck('actual ARR06 PH1 barrier before native entry',any(x.get('factName')=='PTFRPH1_karl_ginsky_Issued' and x.get('comparisonType')=='Equal' and x.get('value')==1 for x in er['graphs']['root']['nodes']['64999']['reads']),er['graphs']['root']['edges'])
 for inp,i in [('audio_v_calls_karl_ginsky_start',40),('audio_v_calls_karl_ginsky_end',42)]:
  sg=M[ks]['graphs']['scene'];ck('Karl actual audio input to holo-named receipt '+inp,i in map(int,reachable(sg['nodes'],sg['edges'],[sg['entries'][inp]])) and any(w.get('factName')==inp.replace('audio_','holo_')+'_done' and w.get('value')==1 for w in sg['nodes'][str(i)]['writes']),dict(input=inp,node=i))
 ck('actual Rogue initializer distinct from Karl',M[init]['graphs']['root']['nodes']['86']['refs']==[rh] and M[cle]['graphs']['root']['nodes']['1408']['refs']==[kh.replace('_holocall','_cleanup')],dict(Rogue=86,Karl_cleanup=1408))
 for producer,wait in [(54,55),(45,48)]:
  gg=M[a6]['graphs']['root/3/471'];ck('Karl native caller real receipt names '+str(producer),[str(producer),'Out',str(wait),'In'] in gg['edges'] and gg['nodes'][str(wait)]['reads'][0]['factName'].startswith('holo_v_calls_karl_ginsky_'),dict(resource=a6,graph='root/3/471',producer=producer,wait=wait))
 result=read(P/'results.json');rows=[]
 for row in result['quest_results']:
  c=read(row['contracts']);ck('frozen ten source findings '+row['quest_id'],sha(row['contracts'])==row['contracts_sha256'] and len(c['contracts'])==10 and not c['fully_static_verified'],row['contracts']);rows.append(dict(id=row['quest_id'],path=row['contracts'],sha256=sha(row['contracts'])))
 # Inspect actual original own bugfix resources; historical inventory fixes need old-save proof.
 bugs=[]
 for q in Q:
  d=find(q+'_bugfixing.questphase');m=load(d);bugs.append(dict(resource=d,root_prefabs=m['root_prefabs'],predicate_sites=[dict(graph=gp,node=i,reads=n['reads'],writes=n['writes'],prefabs=n['prefabs']) for gp,g in m['graphs'].items() for i,n in g['nodes'].items() if n['reads'] or n['writes'] or n['prefabs']]))
 write(O/'native_bugfix_limits.json',bugs);write(O/'source_pins.json',pins);write(O/'tests.json',dict(count=len(checks),checks=checks));out=dict(status='APPROVE_SOURCE_FINDINGS_WITH_PRECISE_HISTORICAL_LIMITS',group='G05',checks=len(checks),quests=rows,tests=str(O/'tests.json'),tests_sha256=sha(O/'tests.json'),source_pins=str(O/'source_pins.json'),source_pins_sha256=sha(O/'source_pins.json'),code_sha256=sha(__file__),findings=['Actual native recipe slices and source-specific security/Fox cleanup/current lab receipt claims independently verified.','Rogue shared holocall versus Karl PH1 outgoing audio controller are distinct; actual audio input writes holo-named ACK and old audio-named clear is preserved, not a missing listener inference.','Old CYB/CP77 inventory, vehicle placement and saved mobility corrections remain separate historical applicability/retirement questions. Current duplicate predicate/action proves only the named duplicate, not that all old patch behavior is restored.','30 contracts retain explicit world placement/saved-owner/target-definition/runtime bounds; no full-static claim or speculative old counter reset.'],runtime_writes=[]);write(H/'G05.json',out);print(json.dumps(dict(checks=len(checks),review=str(H/'G05.json'))))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);run(Path(p.parse_args().output).resolve())
