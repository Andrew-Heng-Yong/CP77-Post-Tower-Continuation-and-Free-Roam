import sys,json,copy,zlib,re,argparse
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[1]));from lib import *
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True);S=Store();T=[];mut=[];mods={};pins=[]
def ck(n,b,e):T.append({'name':n,'status':'PASS'if b else'FAIL','evidence':e});assert b,n
def canon(x):
 c=copy.deepcopy(x)
 for z in walk(c):
  z.pop('payload_sha256',None);z.pop('metadata_sha256',None)
  if 'phaseResource'in z and z['phaseResource'].get('Flags')=='Embedded':z['phaseResource']['Flags']='Soft'
  if z.get('$type')=='TweakDBID':
   v=z['$value'];z['$value']=str((len(v.encode())<<32)|zlib.crc32(v.encode()))if z.get('$storage')=='string'else str(int(v));z['$storage']='uint64'
 return c
for x in read(P/'raw_exports_01/manifest.json'):
 ck('raw_pin '+x['depot'],sha(x['raw'])==x['raw_sha256'],x['raw']);ck('fresh_JSON_pin '+x['depot'],sha(x['json'])==x['json_sha256'],x['json']);m=Resource(read(x['json'])).normalize();ck('actual_raw_decode '+x['depot'],not m['errors'],m['errors']);mods[x['depot']]=m;pins.append(x)
 if x['depot']in S.I:ck('actual_selected_source_raw_model_agreement '+x['depot'],canon(m)==canon(S.load(x['depot'])),'Exact TweakDBID numeric identity and Embedded→Soft reference storage canonicalization only')
M=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');EP=read(W/'prealpha/quest_restoration_qr5/source_epoch_00.json');IDS=['sts_hey_gle_04','sts_hey_rey_09','sts_hey_rey_06','sts_hey_rey_08'];rows=[];GP={}
def g(d,gp='root'):return mods[d]['graphs'][gp]if d in mods else S.g(d,gp)
def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
def edge(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(d,gp)['edges']
def es(d,edges,gp='root'):
 for e in edges:ck('edge '+d+' '+gp+str(e),edge(d,*e,gp=gp),e)
def has(d,i,f,op,v,gp='root'):return any(x.get('factName')==f and x.get('comparisonType')==op and x.get('value')==v for x in n(d,i,gp)['reads'])
for q in IDS:
 er=next(r for r in M['recipes']if r['id']==q and r['kind']=='entry');ed=er['depot'];GP[q]=er;orig='ORIGINAL:'+er['raw'];ep=er['compiled_graph'];main=next(i for i,x in g(ed,ep)['nodes'].items()if er['native']in x['refs'])
 ck('effective_epoch00_private_entry '+q,sha(next(x['raw']for x in pins if x['depot']==ed))==EP['source_resources'][ed],ed)
 for i in er['ids']:
  if i:ck('independent_exact_native_entry_payload '+q+str(i),canon(n(ed,i,ep)['payload'])==canon(n(orig,i,er['graph'])['payload']),{'native':orig,'graph':er['graph'],'node':i})
 for e in er['edges']:ck('whole_compiled_entry_edge '+q+str(e),[str(e[0]),e[1],str(e[2]),e[3]]in g(ed,ep)['edges'],e)
 for gp,gr in mods[ed]['graphs'].items():
  if gp.startswith(ep+'/'):ck('whole_original_inline_graph '+q+gp,canon(gr)==canon(g(orig,gp)),gp)
 ck('native_main_not_replaced '+q,er['native']not in EP['source_resources'],'Exact original provider body remains external')
 body=S.load(er['native']);ck('whole_original_main_prefab '+q,bool(body['root_prefabs']),body['root_prefabs']);comparisons=0
 for d in [d for d in S.MI if '\\'+q+'\\'in d]:
  mm=S.load(d)
  ck('native_child_unchanged_provider '+d,d not in EP['source_resources'],S.I[d]['sha256'])
  for gp,gr in mm['graphs'].items():
   eg='embedded/'+d+'/'+gp
   if eg in mods[orig]['graphs']:ck('native_embedded_external_whole_graph '+d+gp,canon(gr)==canon(g(orig,eg)),eg);comparisons+=1
 guard=n(ed,65002,ep)['payload']['condition'];f={x['factName']:x['value']for x in n(ed,65002,ep)['reads']if'factName'in x};ck('fresh_admission_fixture '+q,evaluate(guard,f,{})is True,f);ck('all_zero_facts_refuse_positive_provenance '+q,evaluate(guard,{k:0 for k in f},{})is False,'Scalar missing facts also read0; missing expected0 is not a refusal claim')
 es(ed,[(int(main),'Out1',65005,'In'),(65005,'Out',65006,'In')],ep)
 qf=W/'prealpha/quest_restoration_qr5/groups/G01/quests'/q/'contracts.json';qd=read(qf);ck('ten_explicit_contracts '+q,len(qd['contracts'])==10 and qd['fully_static_verified']is False and not qd['repairs'],str(qf));rows.append({'quest_id':q,'contract':str(qf),'sha256':sha(qf),'main':main,'body':er['native'],'original_embedded_graph_comparisons':comparisons,'status_counts':{x:sum(c['status']==x for c in qd['contracts'].values())for x in set(c['status']for c in qd['contracts'].values())}})
# The title/ID region guess must not override the exact native producer.
q='sts_hey_rey_09';ed=GP[q]['depot'];ck('GettingWarmer_actual_Japantown_parent','westbrook/japantown/'in GP[q]['raw'],GP[q]['raw']);ck('GettingWarmer_native_tier',has(ed,3,'sts_wbr_jpn_tier_2','Greater',0,'root/3'),'Native root/3 node3 not invented Padre tier');es(ed,[(3,'Out1',49,'In'),(3,'Out1',60,'In'),(49,'Out',61,'In1'),(60,'Out',61,'In2'),(61,'Out1',54,'Active'),(54,'Out',65004,'In'),(65004,'Out',43,'In1')])
credits=[r for r in M['recipes']if r['id']==q and r['kind']=='credit'];ck('GettingWarmer_actual_wbr_counter',len(credits)==1 and any(x['factName']=='wbr_sts_counter'and x['value']==1 for gr in S.load(credits[0]['depot'])['graphs'].values()for nd in gr['nodes'].values()for x in nd['writes']),credits)
phone_bodies=[S.load(d)for d in S.MI if '\\'+q+'\\'in d];requests=[x['factName']for mm in phone_bodies for gr in mm['graphs'].values()for nd in gr['nodes'].values()for x in nd['writes']if x['factName'].endswith('_activate')];ck('GettingWarmer_actual_Wakako_producers',any(x.startswith('holo_wakako_calls_v_')for x in requests)and not any(x.startswith('holo_padre_calls_v_')for x in requests),requests)
FI=r'towercontinued\gig_phone_u9\fixer_initializer.questphase';FC=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase';ck('Wakako_native_initializer97',n(FI,97)['refs']==[r'base\quest\holocalls\wakako\wakako_holocall.questphase']and edge(FI,25,'Out1',97,'In1'),n(FI,97)['payload']);es(FC,[(488,'True',355,'In61'),(355,'Out61',424,'In1')])
WS=r'base\quest\holocalls\wakako\wakako_holocall.scene'
for i,f in [(41,'holo_wakako_calls_v_start_done'),(42,'holo_wakako_calls_v_end_done')]:ck('Wakako_real_ACK'+str(i),any(x['factName']==f and x['value']==1 for x in n(WS,i,'scene')['writes']),f)
# Missing native loot definition is upstream of a concrete startup AND, not a reward-name mismatch.
q='sts_hey_rey_08';ow=next(d for d in S.MI if '\\'+q+'\\'in d and d.endswith('_openworld.questphase'));es(ow,[(4,'Out',5,'In'),(5,'Out',2,'In1')],'root/2/10');ck('OldFriends_three_way_startup_AND',n(ow,2,'root/2/10')['payload']['inputSocketCount']==3,'Requires3 native input pulses after actual spawned actors/loot injection');item_nodes=[z for z in walk(n(ow,5,'root/2/10')['payload'])if z.get('$type')=='TweakDBID'];ck('OldFriends_actual_unknown_item131215478384',any(str(z['$value'])=='131215478384'for z in item_nodes),n(ow,5,'root/2/10')['payload'])
orig='ORIGINAL:'+GP[q]['raw'];eg='embedded/'+ow+'/root/2/10';ck('OldFriends_exact_same_original_embedded_loot_payload',canon(n(ow,5,'root/2/10')['payload'])==canon(n(orig,5,eg)['payload']),eg)
app=W/'prealpha/quest_restoration_qr5/shared/tdb_applicability_02/sts_hey_rey_08.json';aj=read(app);missing=[x for x in aj['targets']if x['id']=='131215478384'];ck('OldFriends_missing_in_both_captured_stock_DBs',len(missing)==1 and missing[0]['exists_in_stock']is False,missing);pins.append({'path':str(app),'sha256':sha(app),'scope':'Direct stock target definition absent, not runtime invalid-item behavior proof'})
# Current U10 guard supersedes obsolete excluded-source wording.
RD=r'towercontinued\special_gigs_u9\gang_retaliation.questphase';ck('current_Valentinos_rey02_owned_guard',has(RD,37,'PTFRU10_sts_hey_rey_02_Started','Equal',1,'root/22/33/227'),'Current serialized selector37 is owned U10 route, not historical excluded route')
# Regress actual resource fixtures against independently fixed native route requirements.
bad=copy.deepcopy(g(ow,'root/2/10'));bad['edges'].remove(['5','Out','2','In1']);mut.append({'fault':'missing_OldFriends_loot_to_AND','detected':['5','Out','2','In1']not in bad['edges']})
bad=copy.deepcopy(n(ow,5,'root/2/10')['payload']);next(x for x in walk(bad)if x.get('$type')=='TweakDBID'and str(x.get('$value'))=='131215478384')['$value']='0';mut.append({'fault':'unapproved_native_missing_item_replacement','detected':canon(bad)!=canon(n(orig,5,eg)['payload'])})
bad=copy.deepcopy(g(ed));bad['edges'].remove(['54','Out','65004','In']);mut.append({'fault':'lost_GettingWarmer_actual_native_admission','detected':['54','Out','65004','In']not in bad['edges']})
for x in mut:ck('mutation '+x['fault'],x['detected'],x)
report={'status':'PASS_INDEPENDENT_SCOPED_G01_SOURCE_REVIEW_WITH_LIMITS','quest_ids':IDS,'checks':len(T),'mutations':len(mut),'actual_raw_exports':len(read(P/'raw_exports_01/manifest.json')),'contracts':rows,'specific_findings':['Getting Warmer is native Japantown/Wakako/tier2/wbr counter despite Heywood questID','Old Friends native unknown loot131215478384 is before 3-way startup AND; exact same original embedded payload. Captured stock definitions absent in both DBs. Keep CONDITIONAL engine/provider gap, no replacement/bypass','Current Valentinos selector37 guarded by U10 rey02 Started, obsolete exclusion language not reused','All four current private entries/native whole/nested graphs and original recipe routes independently compared; no runtime repair justified by this review'],'limits':['Actual missing-item injection/output semantics, saved owner retirement, runtime TweakXL/CET providers, journal target identity and world/prefab placements remain unresolved','No gameplay or future save-compatibility certification','Case review frozen QR5epoch00; later one ARR12 change unrelated'],'runtime_changes':[],'source_pins':str(O/'source_pins.json'),'tests':str(O/'tests.json')};save(O/'review.json',report);save(O/'tests.json',{'checks':T,'mutations':mut});save(O/'source_pins.json',pins+S.pins);save(P.parent/'G01.json',report);print(json.dumps({'checks':len(T),'mutations':len(mut),'review_sha256':sha(P.parent/'G01.json')}))
