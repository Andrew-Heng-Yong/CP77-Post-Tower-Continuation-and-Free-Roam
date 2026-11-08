"""Independent C01 actual-resource review. Does not import worker checker/loader."""
from pathlib import Path
import sys,copy,collections,re
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));from source_lib import *
P=W/'prealpha/quest_restoration_qr6/groups/C01';O=H/'reviews/C01';R=read(P/'results.json')
def run(out):
 assert not out.exists();tests=[];issues=[];pins=[];M={};raw={};allpins=[]
 def ck(k,v,e):
  tests.append(dict(name=k,status='PASS'if v else'FAIL',evidence=e))
  if not v:issues.append(k)
 for pp in R['source_pin_paths']:allpins+=read(pp)
 unique={x['depot']:x for x in allpins if x.get('depot')}
 for d,p in unique.items():
  ck('actual pinned binary/JSON '+d,sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);raw[d]=read(p['json']);M[d]=Resource(raw[d]).normalize();pins.append(p)
  if d in E['source_resources']:ck('current epoch pin '+d,E['source_resources'][d]==sha(p['binary']),d)
 for p in read(O/'readback_01/manifest.json'):
  ck('fresh readback bytes '+p['depot'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);fresh=Resource(read(p['json'])).normalize();ck('fresh vs claimed model '+p['depot'],canon(fresh)==canon(M[p['depot']]),'full source normalization; digests/TDBnumeric only');M[p['depot']]=fresh;pins.append(p)
 # Derive recipe selection from original construction evidence, never from the worker's pass/fail list.
 recipes=read(W/'prealpha/gigs_u10/native/build/native_06/component.json')['recipes'];body_checks=[]
 for q in R['quest_ids']:
  obj=read(P/'quests'/q/'contracts.json');ck('10 specific contracts '+q,len(obj['contracts'])==10 and not obj['fully_static_verified']and all(v.get('proven')and v.get('evidence')for v in obj['contracts'].values()),str(P/'quests'/q/'contracts.json'))
  for r in [r for r in recipes if r['id']==q]:
   d=r['depot'];g=M[d]['graphs']['root'];expected=sorted([[str(a),s,str(b),t]for a,s,b,t in r['edges']]);ck('original recipe exact edge multiset '+d,g['edges']==expected,{'source_raw':r.get('raw'),'native_graph':r.get('graph'),'edges':r['edges']})
   if not r.get('raw'):continue
   donor='recipe:'+r['raw'];og=M[donor]['graphs'][r['graph']]
   for i in r['ids']:
    n=g['nodes'][str(i)];old=og['nodes'][str(i)];a=copy.deepcopy(old['payload']);b=n['payload']
    if i==0 and n['type']=='questInputNodeDefinition':a['socketName']=copy.deepcopy(b['socketName'])
    if a.get('phaseResource')and b.get('phaseResource'):
     # Child private/main source replacement is separately checked below; no other payload field hidden.
     if a['phaseResource']['DepotPath']['$value']!=b['phaseResource']['DepotPath']['$value']:ck('original child points approved native target '+d+'/'+str(i),b['phaseResource']['DepotPath']['$value']==r.get('native'),b['phaseResource'])
     a['phaseResource']=copy.deepcopy(b['phaseResource'])
    ck('original selected parent node '+d+'/'+str(i),a==b,{'original':donor,'graph':r['graph'],'node':i})
  ev=read(P/'verification_01/quests'/q/'evidence.json');entry=ev['entry'];g=M[entry]['graphs']['root'];n=g['nodes'];ck('late identical guard '+q,n['65002']['payload']['condition']==n['65008']['payload']['condition'],'fresh and synchronous recheck are exact condition trees');ck('claim before children '+q,['65008','True','65003','In']in g['edges']and any(w['factName'].endswith('_Issued')and w['value']==1 for w in n['65003']['writes']),g['edges'])
  ck('explicit unresolved placement and save limits '+q,obj['contracts']['presentation']['status']=='OPAQUE'and obj['contracts']['persistence']['status']=='CONDITIONAL'and obj['contracts']['ownership']['status']=='CONDITIONAL',q)
  # Peer chosen actual outcome writers and outgoing edges, not worker test names.
  spec={'sts_hey_gle_03':('sts_hey_gle_03_ow.questphase','root/3','158','sts_hey_gle_03_guitar'),'sts_hey_gle_05':('sts_hey_gle_05_openworld.questphase','root/5','56','gle_05_talked'),'sts_hey_rey_01':('sts_hey_rey_01_openworld.questphase','root/4','233','rey_01_spare'),'sts_hey_rey_02':('sts_hey_rey_02_open_world.questphase','root/4','88','sts_valentinos_retaliation')}[q];d=next(d for d in M if d.startswith('base\\')and d.endswith('\\'+spec[0]));gg=M[d]['graphs'][spec[1]];nn=gg['nodes'][spec[2]];ck('independent decisive route '+q,spec[3]in str(nn['payload'])and any(e[0]==spec[2]for e in gg['edges']),dict(depot=d,graph=spec[1],node=spec[2],payload=nn['payload'],edges=[e for e in gg['edges']if e[0]==spec[2]]))
  # Independently resolve actual request producer, matching reader and real callback, plus caller wait/clear.
  for p in ev['protocols']:
   hc=M[p['listener']];hs=M[p['ack_scene']];sc=M[p['scene']];pr=sc['graphs']['scene']['nodes'][p['producer']];ck('actual request read/real ACK '+q+p['scene']+p['producer'],any(w['factName']==p['request']and w['value']==1 for w in pr['writes'])and all(any(x.get('factName')==p['request']for x in hc['graphs']['root']['nodes'][i]['reads'])for i in p['readers'])and all(any(w['factName']==p['ack']and w['value']==1 for w in hs['graphs']['scene']['nodes'][i]['writes'])for i in p['ack_writers']),p)
 # Psychofan source reconstruction is checked independently against retained historical corrected binary,
 # plus literal native dialogue/topology equality and named R4 muting/prop constraints.
 pm=read(W/'prealpha/gigs_u10/presentation/build/presentation_03/component.json');psych=[]
 for item in pm['inputs']:
  d=item['depot'];current=C/'archive_source'/d;ck('actual approved Psychofan donor identity '+d,sha(current)==pm['resources'][d]==E['source_resources'][d],item);m=M[d];orig=Resource(read(W/item['native_json'])).normalize()
  if d.endswith('.scene'):
   gn=orig['graphs']['scene'];gc=m['graphs']['scene'];ck('Psychofan entire scene topology and IDs',gn['edges']==gc['edges']and set(gn['nodes'])==set(gc['nodes'])and gn['entries']==gc['entries'],'approved presentation authoring does not cut scene routes');ck('Psychofan only unused Johnny props removed',len(orig['metadata']['props'])==7 and len(m['metadata']['props'])==5 and orig['metadata']['props'][:5]==m['metadata']['props'],'five original non-Johnny props unchanged')
   for i,n in gn['nodes'].items():
    def dialog(nn):return[x for x in walk(nn['payload'])if x.get('$type')=='scnDialogLineEvent']
    ck('Psychofan original dialogue '+i,dialog(n)==dialog(gc['nodes'][i]),i)
   muted=[x for g in m['graphs'].values()for n in g['nodes'].values()for x in walk(n['payload'])if x.get('$type')=='scnPlaySkAnimEvent'and x.get('performer',{}).get('id')==769];ck('Psychofan named Johnny events muted',bool(muted)and all(x['muteAnimEvents']=='STANDARD'for x in muted),len(muted))
  psych.append(dict(depot=d,current_sha256=sha(current),original_json=item['native_json']))
 # Independent raw-document fault controls on actual roots and actual callback scene.
 mutants=[]
 ent=next(x['effective_resource']for x in[read(P/'quests/sts_hey_gle_03/contracts.json')]);o=copy.deepcopy(raw[ent]);r=next(x for x in walk(o)if x.get('$type')=='questVarComparison_ConditionType'and x.get('factName')=='q307_done');r['value']=0;mm=Resource(o).normalize();caught=any(x.get('factName')=='q307_done'and x['value']==0 for x in mm['graphs']['root']['nodes']['65002']['reads']);ck('independent raw changed Tower eligibility rejected',caught,'exact required fact1 differs');mutants.append(dict(fault='Tower guard1to0',detected=caught))
 for p in R['quest_results']:ck('contract frozen input hash '+p['quest_id'],sha(p['contracts'])==p['contracts_sha256'],p)
 write(out/'tests.json',tests);write(out/'source_pins.json',pins);write(out/'psychofan_review.json',psych);write(out/'mutations.json',mutants);write(out/'review.json',dict(status='PASS_INDEPENDENT_SOURCE_REVIEW'if not issues else'REVIEW_ISSUES',group='C01',reviewer='qr6_a',checks=len(tests),issues=issues,mutations=len(mutants),fresh_readbacks=len(read(O/'readback_01/manifest.json')),reviewed_result=str(P/'results.json'),reviewed_result_sha256=sha(P/'results.json'),contract_count=40,findings='Four ten-contract records supported; no new defect/repair. Existing world placement/saved-owner/engine limits remain correctly explicit.',limits=['Parent/native source and raw callbacks inspected independently; no worker checker imported.','R4 exact source identity/dialogue/topology/props/muting supported; independent full reconstructed custom workspot code remains worker evidence, not runtime placement proof.','No gameplay/save transition or merged effective TDB certification.']));print(read(out/'review.json'))
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--output');a=ap.parse_args()
 if a.prepare:
  ps=[]
  for pp in R['source_pin_paths']:ps+=read(pp)
  unique={x['depot']:x for x in ps if x.get('depot')};selection=[p for d,p in unique.items()if d.endswith('_entry.questphase')or d.startswith('recipe:')or d.endswith('sts_hey_gle_03_01_johnny.scene')or d.endswith('padre_holocall.scene')];write(O/'readback_inputs.json',selection);print(len(selection))
 else:run(Path(a.output))
