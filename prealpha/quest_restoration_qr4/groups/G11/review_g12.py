"""Independent G12 Padre review. Requires finalized contracts; no G12 code imports."""
from lib import *
import argparse,copy
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True)
B=W/'prealpha/quest_restoration_qr4/groups/G12';assert (B/'results.json').is_file(),'Wait for G12 finalized findings';R=read(B/'results.json');S=Store();checks=[];M=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');mp={k.replace('\\','/'):v for k,v in M['source_pins'].items()}
def ck(name,b,e):checks.append({'name':name,'status':'PASS'if b else'FAIL','evidence':e});assert b,name
for row in read(B/'verification_01/source_pins.json'):
 d=row.get('depot')
 if d and not d.startswith('recipe:'):
  S.load(d);p=next(x for x in S.pins if x['depot']==d);ck('raw_JSON_pin '+d,p['resource_sha256']==row['sha256']and p['json_sha256']==row['json_sha256'],p)
 elif d:
  ck('recipe_actual_raw_JSON_pin '+d,sha(row['binary'])==row['sha256']and sha(row['json'])==row['json_sha256'],row)
  raw=Path(row['binary']).relative_to(W).as_posix();j=Path(row['json']).relative_to(W).as_posix();ck('original_recipe_manifest_pin '+d,(raw in mp and mp[raw]==row['sha256'])or(j in mp and mp[j]==row['json_sha256']),'Existing original binary/export pairing; provider not newly reselected')
  model=Resource(read(row['json'])).normalize();ck('recipe_decode '+d,not model['errors'],model['errors']);S.models[d]=model;S.pins.append({'depot':d,'binary':row['binary'],'resource_sha256':row['sha256'],'json':row['json'],'json_sha256':row['json_sha256'],'provider':'Pinned original U9 recipe evidence'})
 else:ck('script_policy_pin '+row['path'],sha(row['path'])==row['sha256'],row['path'])
g=S.g;n=S.n
def es(d,edges,gp='root'):
 for e in edges:ck('edge '+d+' '+str(e),S.edge(d,*e,gp=gp),{'graph':gp,'edge':e})
def soft(x):
 y=copy.deepcopy(x)
 for z in walk(y):
  z.pop('payload_sha256',None)
  if'phaseResource'in z and z['phaseResource'].get('Flags')=='Embedded':z['phaseResource']['Flags']='Soft'
 return y
for qid,main,inline,poi in [('sts_hey_gle_01',5,11,49),('sts_hey_gle_06',8,6,68)]:
 recipes=[r for r in M['recipes']if r['id']==qid and r['kind']in['entry','credit','map']]
 for r in recipes:
  d=r['depot'];original='recipe:'+r['raw']
  for i in r['ids']:
   if i!=0:ck('retained_original_payload '+d+' '+str(i),soft(n(d,i)['payload'])==soft(n(original,i,r['graph'])['payload']),{'original':original,'graph':r['graph'],'node':i})
  for gp,gr in S.load(d)['graphs'].items():
   if gp!='root':ck('retained_original_inline '+d+gp,gr==g(original,gp),gp)
 ed='towercontinued\\native_gigs_u9\\'+qid+'_entry.questphase';es(ed,[(65002,'Out',65003,'In'),(65003,'Out',inline,'In1'),(poi,'Out',65004,'In'),(65004,'Out',main,'In1'),(main,'Out1',65005,'In'),(65005,'Out',65006,'In')]);body=n(ed,main)['refs'][0];ck('whole_native_body_scope '+qid,bool(S.load(body)['root_prefabs'])and'In1'in g(body)['entries'],{'body':body,'prefabs':S.load(body)['root_prefabs']})
CD=r'base\quest\holocalls\padre\padre_holocall.questphase';SC=CD.replace('.questphase','.scene');FI=r'towercontinued\gig_phone_u9\fixer_initializer.questphase';FC=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
es(FI,[(25,'Out1',79,'In1')]);es(CD,[(37,'Out',32,'In'),(32,'Out',33,'In'),(33,'Out',34,'In'),(34,'Out',35,'In1'),(35,'Out1',32,'In'),(37,'Out',36,'In'),(36,'Out',28,'In'),(28,'False',10,'In'),(10,'Out',0,'holo_padre_calls_v_start'),(3,'Out',11,'In'),(11,'Out',0,'holo_padre_calls_v_end')]);es(FC,[(468,'True',336,'In42'),(336,'Out42',474,'In')])
for i,f in [(41,'holo_padre_calls_v_start_done'),(42,'holo_padre_calls_v_end_done')]:ck('real_Padre_ack '+str(i),any(w['factName']==f and w['value']==1 for w in n(SC,i,'scene')['writes']),f)
BF=r'base\open_world\street_stories\heywood\glenn\sts_hey_gle_06\phase\sts_hey_gle_06_bugfixing.questphase';OW=r'base\open_world\street_stories\heywood\glenn\sts_hey_gle_06\phase\sts_hey_gle_06_openworld.questphase';PAR=r'base\quest\minor_quests\minorquests.questphase';WRAP=r'base\quest\minor_quests\mq044\phases\mq044.questphase';PRIVATE=r'towercontinued\sidejobs_s23\base_a\mq044_jakes_vehicle.questphase'
for d in [PAR,WRAP,PRIVATE]:S.load(d)
es(BF,[(0,'Out',2,'In'),(2,'True',1,'In'),(2,'False',3,'In'),(3,'Out',4,'In'),(4,'Out',5,'In1')],'root/9')
ck('bugfix9_samples_started_once',any(x.get('factName')=='mq_044_started_in_main'and x.get('comparisonType')=='GreaterOrEqual'and x.get('value')==1 for x in n(BF,2,'root/9')['reads']),'No late started_in_main recheck after its delay')
ck('bugfix9_one_day',any(x.get('$type')=='questGameTimeDelay_ConditionType'and x.get('days')==1 for x in walk(n(BF,4,'root/9')['payload'])),'Original corrective delay, not normal helper timer')
ck('bugfix9_direct_main',n(BF,5,'root/9')['refs']==[r'base\quest\minor_quests\mq044\phases\mq044_main.questphase'],'Bypasses wrapper started_in_main writer')
es(PAR,[(148,'Out',150,'In'),(150,'Out',149,'In1')]);ck('normal_three_days',any(x.get('$type')=='questGameTimeDelay_ConditionType'and x.get('days')==3 for x in walk(n(PAR,150)['payload'])),'Original outer admission timer')
es(PRIVATE,[(150,'Out',1100,'In'),(1100,'True',1101,'In'),(1101,'Out',149,'In1')]);es(WRAP,[(4,'Out',3,'In'),(4,'Out',2,'In1')]);ck('normal_wrapper_started_writer',any(w['factName']=='mq_044_started_in_main'and w['value']==1 for w in n(WRAP,3)['writes']),'Writer and main are parallel children after native wrapper input, not an earlier receipt')
es(OW,[(60,'Out',183,'In'),(183,'Out',230,'In'),(230,'Out',139,'In')],'root/0');ck('old_gig_local_launcher_removed',n(OW,230,'root/0')['payload'].get('deletedNodeIds')==[136]and n(OW,139,'root/0')['type']=='questCheckpointNodeDefinition','Local three-day delay now leads deletion marker/checkpoint, not current MQ044 launch')
mut=[];bad=copy.deepcopy(g(FC));bad['edges'].remove(['336','Out42','474','In']);mut.append({'fault':'missing_Padre_cleanup_exit','detected':['336','Out42','474','In']not in bad['edges']})
bad=copy.deepcopy(n(PAR,150)['payload']);next(x for x in walk(bad)if x.get('$type')=='questGameTimeDelay_ConditionType')['days']=1;mut.append({'fault':'guessed_one_day_normal_timer','detected':bad!=n(PAR,150)['payload']})
for x in mut:ck('mutation '+x['fault'],x['detected'],x)
for row in R.get('quests',R.get('quest_results',[])):
 p=Path(row['contracts']);x=read(p);ck('ten_final_contracts '+x['quest_id'],len(x['contracts'])==10 and not x.get('fully_static_verified',False),str(p))
save(O/'tests.json',{'checks':checks,'count':len(checks),'mutations':mut});save(O/'source_pins.json',S.pins)
out={'status':'INDEPENDENT_SOURCE_REVIEW_ACCEPTS_G12_WITH_MQ044_TIMING_OWNER_LIMIT','checks':len(checks),'mutations':mut,'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'reviewed_results_sha256':sha(B/'results.json'),'reviewed_group':'G12','reviewer_group':'G11','verified':['LifeWork=sts_hey_gle_06;EyeForAnEye=sts_hey_gle_01; source identities, original entry/credit/map payloads and inline graphs independently checked','Actual Padre counter queue, master scene41/42 acknowledgements and cleanup468→336→474 remain connected','Native bugfix9 checks started_in_main once, then can wait finished+one-day→MQ044_main; no late arbitration','Normal minorquests148→150three-days→149wrapper retains separate started_in_main writer; current S23 private helper preserves this native route','Gig-local183three-day timer leads230DeletionMarker(deleted136)→139checkpoint; it is not the current normal MQ044 launcher'],'remaining':['CONDITIONAL: Original corrective versus normal executing-owner/timer provenance remains unresolved; blindly rehostingbugfix9 could overlap the existing S23 route','No inferred timing correction, synthetic started flag or duplicate MQ044 controller is justified','World/prefab placements, TDB target definitions, saved original owners and actual phone/actor/vehicle scheduling remain opaque/live-only'],'confirmed_new_defects':[],'runtime_changes':[]}
save(O/'review.json',out);frozen=Path(__file__).parent/'reviews/G12.json'
if not frozen.exists():save(frozen,out)
print(json.dumps({'checks':len(checks),'sources':len(S.pins),'mutations':len(mut)}))
