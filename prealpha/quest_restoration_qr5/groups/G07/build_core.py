from lib import *
import argparse,copy
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True)
S=Store();M=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');tests=[];G09=W/'prealpha/quest_restoration_qr4/groups/G09/shared_core.json'
def ck(name,b,e):tests.append({'name':name,'status':'PASS'if b else'FAIL','evidence':e});assert b,name
ck('frozen_U9_shared_core',sha(G09)=='BDD1BB748A68160491FE98715951DAD7C79D8CB8233333255C250D2FF060A857',str(G09));old=read(G09)
for p in old['sources']:
 if not p['depot'].startswith('vanilla_recipe:'):ck('inherited_U9_raw_pin '+p['depot'],sha(p['binary'])==p['resource_sha256']and sha(p['json'])==p['json_sha256'],p['depot'])
CD=r'base\quest\holocalls\reggie\reggie_holocall.questphase';SC=CD.replace('.questphase','.scene');CL=CD.replace('_holocall.questphase','_cleanup.questphase');FI=r'towercontinued\gig_phone_u9\fixer_initializer.questphase';FC=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase';IN=r'base\quest\holocalls\holocall_initializers.questphase'
for d in [CD,SC,CL,FI,FC,IN]:ck('decode '+d,not S.load(d)['errors'],d)
def es(d,edges,gp='root'):
 for e in edges:ck('connected '+d+' '+str(e),S.edge(d,*e,gp=gp),e)
ck('Regina_initializer84',S.n(FI,84)['payload']==S.n(IN,84)['payload'],'Exact native phase template; reggie contact versus Regina display name is native')
es(FI,[(25,'Out1',84,'In1')])
es(CD,[(1,'Out1',41,'In'),(41,'Out',36,'In'),(41,'Out',40,'In'),(36,'Out',37,'In'),(37,'Out',38,'In'),(38,'Out',39,'In1'),(39,'Out1',36,'In'),(40,'Out',32,'In'),(32,'False',9,'In'),(9,'Out',21,'holo_reggie_calls_v_start'),(2,'Out',10,'In'),(10,'Out',21,'holo_reggie_calls_v_end'),(21,'End 0',27,'In1'),(15,'CutSource',40,'CutDestination'),(15,'Out',29,'In'),(29,'Out',24,'In2')])
for i,f,v in [(37,'holo_reggie_calls_v_start_activate_count',1),(38,'holo_reggie_calls_v_start_activate',0),(9,'holo_reggie_calls_v_start_activate_count',-1)]:ck('native_queue_writer '+str(i),any(x['factName']==f and x['value']==v for x in S.n(CD,i)['writes']),{'node':i,'fact':f,'value':v})
for i,f in [(396,'holo_reggie_calls_v_start_done'),(398,'holo_reggie_calls_v_end_done')]:ck('real_native_ACK '+str(i),any(x['factName']==f and x['value']==1 for x in S.n(SC,i,'scene')['writes']),{'node':i,'fact':f})
es(SC,[(39,'0:0',396,'0:1'),(396,'0:0',612,'0:1'),(398,'0:0',585,'0:1'),(566,'0:0',568,'0:1'),(568,'0:0',44,'0:1')],'scene')
es(FC,[(474,'True',342,'In48'),(342,'Out48',476,'In'),(474,'False',476,'In')]);ck('native_Regina_cleanup_reference',S.n(FC,342)['refs']==[CL],CL)
es(CL,[(1,'Out',4,'In'),(4,'True',6,'In'),(6,'Out',0,'holo_reggie_calls_v_end'),(0,'End 0',5,'In'),(5,'True',7,'In'),(7,'Out',2,'holo_v_calls_reggie_end')])
bad=copy.deepcopy(S.g(FI));bad['edges'].remove(['25','Out1','84','In1']);ck('mutation_missing_Regina_listener',['25','Out1','84','In1']not in bad['edges'],'Actual missing listener connection versus native mandatory initializer')
save(O/'tests.json',{'count':len(tests),'checks':tests});save(O/'source_pins.json',S.pins)
x={'status':'VERIFIED_REGINA_NATIVE_PROTOCOL_INHERITING_EXACT_U9_STUDIO_CORE','source_epoch':'QR5 frozen epoch00 / actual QR4 candidate03','inherited_core':str(G09),'inherited_core_sha256':sha(G09),'checks':len(tests),'source_pins':str(O/'source_pins.json'),'sources':S.pins,'tests':str(O/'tests.json'),'protocol':{'contact':'reggie','display_name':'Regina Jones','initializer':84,'queue':'1.Out1 to deletion41 fans to36 producer counter loop and40 queue waiter; 32False then9decrement to21native scene start','real_ack_nodes':[396,398],'cleanup':'474True to342.In48 native cleanup; native4/5 compare start_count>end_count,6/7 increment reset counters and play actual end scenes','interrupt':'native master566->568 interrupted1->44; cleanup end counters and actual End 0 sockets retained','studio':'Inherited exact PH3 studio root refs, placement unresolved'},'limits':['SupportIssued before parent startup is a receipt, not scheduler proof that every listener runs','Unobserved saved native owner retirement, actual interruption/call delivery, world placements and runtime TweakXL/CET modifiers remain unproven'],'runtime_changes':[]}
save(O/'shared_core.json',x);frozen=Path(__file__).parent/'shared_core.json'
assert not frozen.exists();save(frozen,x)
print(json.dumps({'checks':len(tests),'sources':len(S.pins),'shared_core_sha256':sha(frozen)}))
