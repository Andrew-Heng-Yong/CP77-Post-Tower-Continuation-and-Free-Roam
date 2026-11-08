"""Independent four-U10 C02 review; no worker verifier or input-loader imports."""
from pathlib import Path
import sys,copy,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'A01'));from source_lib import *
P=W/'prealpha/quest_restoration_qr6/groups/C02';O=H/'reviews/C02';R=read(P/'results.json')
def allpins():
 pp=[]
 for p in R['source_pin_paths']:pp+=read(p)
 return{p['depot']:p for p in pp if p.get('depot')}
def run(out):
 assert not out.exists();tests=[];issues=[];pins=[];M={};raw={}
 def ck(k,v,e):
  tests.append(dict(name=k,status='PASS'if v else'FAIL',evidence=e))
  if not v:issues.append(k)
 for d,p in allpins().items():
  ck('actual binary/JSON pin '+d,sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);raw[d]=read(p['json']);M[d]=Resource(raw[d]).normalize();pins.append(p)
  if d in E['source_resources']:ck('canonical current resource '+d,sha(p['binary'])==E['source_resources'][d],d)
 for p in read(O/'readback_01/manifest.json'):
  ck('fresh raw+JSON pin '+p['depot'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);fresh=Resource(read(p['json'])).normalize();ck('actual fresh semantic correspondence '+p['depot'],canon(fresh)==canon(M[p['depot']]),'complete normalization; typed TDBID/derived digests only');M[p['depot']]=fresh;pins.append(p)
 recipes=read(W/'prealpha/gigs_u10/native/build/native_06/component.json')['recipes'];nativeplan=read(W/'research/gigs_u10/native/build_plan_01.json')['jobs'];decisive=[];protocols=[]
 for q in R['quest_ids']:
  own=read(P/'quests'/q/'contracts.json');ck('ten source-specific bounded contracts '+q,len(own['contracts'])==10 and all(x.get('proven')and x.get('evidence')for x in own['contracts'].values())and not own['fully_static_verified'],q)
  for rec in[r for r in recipes if r['id']==q]:
   g=M[rec['depot']]['graphs']['root'];ck('native recipe edge multiset '+rec['depot'],g['edges']==sorted([[str(a),s,str(b),t]for a,s,b,t in rec['edges']]),rec)
   if not rec.get('raw'):continue
   src='recipe:'+rec['raw'];og=M[src]['graphs'][rec['graph']]
   for i in rec['ids']:
    a=copy.deepcopy(og['nodes'][str(i)]['payload']);b=g['nodes'][str(i)]['payload']
    if g['nodes'][str(i)]['type']=='questInputNodeDefinition':a['socketName']=copy.deepcopy(b['socketName'])
    if a.get('phaseResource')and b.get('phaseResource'):
     if a['phaseResource']['DepotPath']['$value']!=b['phaseResource']['DepotPath']['$value']:ck('original child target '+q+str(i),b['phaseResource']['DepotPath']['$value']==rec.get('native'),b['phaseResource'])
     a['phaseResource']=copy.deepcopy(b['phaseResource'])
    ck('actual original selected node '+rec['depot']+'/'+str(i),canon(a)==canon(b),dict(native=src,graph=rec['graph'],node=i))
    oldprefix=rec['graph']+'/'+str(i)
    for gp,gg in M[src]['graphs'].items():
     if gp==oldprefix or gp.startswith(oldprefix+'/'):ck('actual original selected nested graph '+rec['depot']+gp,canon(gg)==canon(M[rec['depot']]['graphs']['root'+gp[len(rec['graph']):]]),src)
  ev=read(P/'verification_01/quests'/q/'evidence.json');entry=ev['entry'];g=M[entry]['graphs']['root'];ns=g['nodes'];ck('native guard actual late recheck '+q,ns['65002']['payload']['condition']==ns['65008']['payload']['condition']and['65008','True','65003','In']in g['edges'],'late guard cannot silently differ')
  for ph in ev['protocols']:
   sg=M[ph['scene']]['graphs']['scene'];hc=M[ph['listener']]['graphs']['root'];hs=M[ph['ack_scene']]['graphs']['scene'];ck('source original producer/listener/realACK '+q+ph['scene']+ph['producer'],any(w['factName']==ph['request']and w['value']==1 for w in sg['nodes'][ph['producer']]['writes'])and all(any(x.get('factName')==ph['request']for x in hc['nodes'][i]['reads'])for i in ph['readers'])and all(any(w['factName']==ph['ack']and w['value']==1 for w in hs['nodes'][i]['writes'])for i in ph['ack_writers']),ph);protocols.append(ph)
  ck('independent conditional-save/opaque-placement boundary '+q,own['contracts']['presentation']['status']=='OPAQUE'and own['contracts']['persistence']['status']=='CONDITIONAL'and own['contracts']['completion_rewards_cleanup']['status']=='CONDITIONAL',q)
  spec={'sts_std_arr_03':('sts_std_arr_03_openworld.questphase','root/2','90','arr_03_finished'),'sts_wat_nid_07':('sts_wat_nid_07_warehouse_ow.questphase','root/3','72','aaron_confronted_about_recording'),'sts_wbr_hil_06':('sts_wbr_hil_06_openworld.questphase','root/6','19','completion_pacifist'),'sts_wbr_jpn_12':('sts_wbr_jpn_12_02_openworld.questphase','root/4','47','jpn_12b_finished')}[q]
  # Source names differ across shipped authoring. Resolve the exact claimed graph/node then verify literal payload, never assume suffix.
  options=[(d,z['graphs'][spec[1]]['nodes'][spec[2]])for d,z in M.items()if d.startswith('base\\')and q in d and spec[1]in z['graphs']and spec[2]in z['graphs'][spec[1]]['nodes']and spec[3]in str(z['graphs'][spec[1]]['nodes'][spec[2]]['payload'])]
  ck('independently selected decisive original route '+q,len(options)==1,{'node':spec[2],'graph':spec[1],'literal':spec[3],'options':[d for d,n in options]})
  if options:decisive.append(dict(quest=q,depot=options[0][0],graph=spec[1],node=spec[2],payload=options[0][1]['payload']))
 # One actual fault control is chosen independently and checked against exact native meaning.
 ph=protocols[0];obj=copy.deepcopy(raw[ph['ack_scene']]);nchanged=0
 for x in walk(obj):
  if x.get('$type')=='questSetVar_NodeType'and x.get('factName')==ph['ack']:x['value']=0;nchanged+=1
 mutant=Resource(obj).normalize();caught=nchanged>0 and not any(w['factName']==ph['ack']and w['value']==1 for z in mutant['graphs'].values()for n in z['nodes'].values()for w in n['writes']);ck('independent actual raw removed real ACK detected',caught,dict(depot=ph['ack_scene'],fact=ph['ack'],changed=nchanged));write(out/'mutation.json',dict(fault='all_real_ACK_writers_removed',detected=caught,changed=nchanged))
 for p in R['quest_results']:ck('frozen contract hash '+p['quest_id'],sha(p['contracts'])==p['contracts_sha256'],p)
 write(out/'tests.json',tests);write(out/'source_pins.json',pins);write(out/'decisive_routes.json',decisive);write(out/'review.json',dict(status='PASS_INDEPENDENT_SOURCE_REVIEW'if not issues else'REVIEW_ISSUES',group='C02',reviewer='qr6_a',checks=len(tests),issues=issues,mutations=1,fresh_readbacks=len(read(O/'readback_01/manifest.json')),reviewed_result=str(P/'results.json'),reviewed_result_sha256=sha(P/'results.json'),contract_count=40,limits=['All selected native recipe payloads, nested graphs, original decisive routes and real phone callbacks independently checked.','No worker checker/input-loader imported; actual current binaries and fresh readbacks examined.','No gameplay/save/streamed-world/TDB-winner certification.']));print(read(out/'review.json'))
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--output');a=ap.parse_args()
 if a.prepare:
  selection=[p for d,p in allpins().items()if d.endswith('_entry.questphase')or d.startswith('recipe:')or d.endswith('rogue_holocall.scene')];write(O/'readback_inputs.json',selection);print(len(selection))
 else:run(Path(a.output))
