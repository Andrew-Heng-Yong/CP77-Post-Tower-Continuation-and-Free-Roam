from lib import *
import argparse,copy
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True)
S=Store();M=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');tests=[];G09=W/'prealpha/quest_restoration_qr4/groups/G09/shared_core.json'
def ck(name,b,e):tests.append({'name':name,'status':'PASS'if b else'FAIL','evidence':e});assert b,name
ck('frozen_U9_shared_core',sha(G09)=='BDD1BB748A68160491FE98715951DAD7C79D8CB8233333255C250D2FF060A857',str(G09));old=read(G09)
for p in old['sources']:
 if not p['depot'].startswith('vanilla_recipe:'):ck('inherited_U9_raw_pin '+p['depot'],sha(p['binary'])==p['resource_sha256']and sha(p['json'])==p['json_sha256'],p['depot'])
CD=r'base\quest\holocalls\dino\dino_holocall.questphase';SC=CD.replace('.questphase','.scene');CL=CD.replace('_holocall.questphase','_cleanup.questphase');FI=r'towercontinued\gig_phone_u9\fixer_initializer.questphase';FC=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase';IN=r'base\quest\holocalls\holocall_initializers.questphase'
for d in [CD,SC,CL,FI,FC,IN]:ck('decode '+d,not S.load(d)['errors'],d)
def es(d,edges):
 for e in edges:ck('connected '+d+' '+str(e),S.edge(d,*e),e)
ck('Dino_initializer53',S.n(FI,53)['payload']==S.n(IN,53)['payload'],'Exact native phase template, no extra listener owner');es(FI,[(25,'Out1',53,'In1')])
es(CD,[(38,'Out',32,'In'),(32,'Out',33,'In'),(33,'Out',35,'In'),(35,'Out',36,'In1'),(36,'Out1',32,'In'),(38,'Out',37,'In'),(37,'Out',28,'In'),(28,'False',34,'In'),(34,'Out',0,'holo_dino_calls_v_start'),(3,'Out',11,'In'),(11,'Out',0,'holo_dino_calls_v_end')])
for i,f,v in [(33,'holo_dino_calls_v_start_activate_count',1),(35,'holo_dino_calls_v_start_activate',0),(34,'holo_dino_calls_v_start_activate_count',-1)]:ck('native_queue_writer '+str(i),any(x['factName']==f and x['value']==v for x in S.n(CD,i)['writes']),{'node':i,'fact':f,'value':v})
for i,f in [(41,'holo_dino_calls_v_start_done'),(42,'holo_dino_calls_v_end_done')]:ck('real_native_ack '+str(i),any(x['factName']==f and x['value']==1 for x in S.n(SC,i,'scene')['writes']),{'scene':SC,'node':i})
es(FC,[(441,'True',307,'In15'),(307,'Out15',462,'In')]);ck('native_Dino_cleanup',S.n(FC,307)['refs']==[CL],'Original cleanup not synthetic counter reset')
bad=copy.deepcopy(S.g(FI));bad['edges'].remove(['25','Out1','53','In1']);ck('mutation_missing_Dino_listener',['25','Out1','53','In1']not in bad['edges'],'Actual missing listener connection detected')
save(O/'tests.json',{'count':len(tests),'checks':tests});save(O/'source_pins.json',S.pins)
x={'status':'VERIFIED_DINO_PROTOCOL_INHERITING_PINNED_U9_STUDIO_CORE','source_epoch':'QR4 epoch00 / QR3candidate01','inherited_core':str(G09),'inherited_core_sha256':sha(G09),'checks':len(tests),'source_pins':str(O/'source_pins.json'),'sources':S.pins,'tests':str(O/'tests.json'),'protocol':{'contact':'dino','map_fixer_internal_name':'dyno','initializer':53,'request_queue':'32→33count+1→35request0→36loop;37count/setup wait→28False→34count-1→0start','real_ack_nodes':[41,42],'cleanup':'441.True→307.In15→Out15→462','studio':'Inherited exact PH3studio core; placement not proven'},'limits':['SupportIssued before parent startup is a receipt, not scheduler proof each listener running','Native/saved ownership, actual interruption/call delivery and world/TDB targets remain conditional/live-only'],'runtime_changes':[]}
save(O/'shared_core.json',x);frozen=Path(__file__).parent/'shared_core.json'
if not frozen.exists():save(frozen,x)
print(json.dumps({'checks':len(tests),'sources':len(S.pins),'shared_core_sha256':sha(frozen)}))
