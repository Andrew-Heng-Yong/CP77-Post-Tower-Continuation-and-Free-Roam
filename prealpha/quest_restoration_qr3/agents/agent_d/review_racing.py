"""Separate raw-source review of Agent A's racing entry/phone/owner claims."""
from pathlib import Path
import json,hashlib,ast,copy
W=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent;O=D/'reviews';O.mkdir(exist_ok=True);dest=O/'racing.json';assert not dest.exists()
tree=ast.parse((D/'review_mq030.py').read_text());keep=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ['Raw','val','walk']];ns={};exec(compile(ast.Module(body=keep,type_ignores=[]),'<independent raw parser>','exec'),ns);Raw=ns['Raw'];walk=ns['walk'];val=ns['val']
I=json.loads((W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json').read_text());pins=[];checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def check(name,ok,ev):checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':ev});assert ok,name
def load(d):
 r=I[d];j=Path(r['json']);b=j.with_suffix('')
 if d.startswith('towercontinued\\'):b=W/'prealpha/phone_studios_ph3/candidate_01/archive_source'/Path(d.replace('\\','/'))
 if not b.is_file() and 'json'in j.parts:
  parts=list(j.parts);parts[parts.index('json')]='raw';b=Path(*parts).with_suffix('')
 check('binary pin '+d,sha(b)==r['sha256'],str(b));pins.append({'depot':d,'binary':str(b),'sha256':sha(b),'json':str(j),'json_sha256':sha(j)})
 return Raw(json.loads(j.read_text(encoding='utf-8-sig')))
def fact(r,n,f,op,v):return any(x.get('factName')==f and x.get('comparisonType')==op and x.get('value')==v for x in walk(r.clean(n)))
S=load(r'towercontinued\sidejobs_s27\claire\sq024_fresh.questphase');PAR=load(r'base\quest\side_quests\sidequests.questphase');N=load(r'base\quest\side_quests\sq024\sq024.questphase');BOOT=load(r'towercontinued\races_r1\boot.questphase');P=load(r'towercontinued\sidejobs_s27\phone\claire.questphase');INIT=load(r'base\quest\holocalls\holocall_initializers.questphase');C=load(r'base\quest\holocalls\claire\claire_holocall.questphase');SH=load(r'towercontinued\gig_phone_u9\fixer_cleanup.questphase')
sn,se=S.graph();pan,pae=PAR.graph();nn,ne=N.graph();bn,be=BOOT.graph();pn,pe=P.graph();ins,ine=INIT.graph();cn,ce=C.graph();shn,she=SH.graph()
one=S.clean(sn['100']);two=PAR.clean(pan['50']);one['id']=two['id']
check('native normal parent50 binding exact modulo savedprivate100',one==two,'S27 node100.sq024_in references exact native SQ024, instanceprefabs nativeempty')
check('original q101 parent prerequisite retained',fact(PAR,pan['31'],'q101_enable_side_content','Greater',0) and fact(S,sn['2'],'q101_enable_side_content','GreaterOrEqual',1),'Native sidequests31 versus S27 positive range')
required={('0','Out','1','In'),('1','Out','2','In'),('2','Out','3','In'),('3','False','2','In'),('3','True','4','In'),('4','Out','89','In'),('89','Out','90','In'),('90','True','92','In'),('92','Out','93','In'),('93','Out','100','sq024_in'),('100','sq024_out','101','In')}
check('actual S27 normal entry and completion connections',required<=se,sorted(required))
check('S27 claim changes only owned entry receipt',S.clean(sn['4'])['type']['factName']=='PTFRS27_SQ024_FRESH_Issued' and S.clean(sn['4'])['type']['value']==1,'Node4 before nativebody')
for i in ['2','3','90']:
 cond=S.clean(sn[i])['condition'];journals=[x for x in walk(cond) if x.get('$type')=='questJournalEntryState_ConditionType']
 check('all485 inactive journal predicates '+i,len(journals)==485 and all(x['state']=='Inactive' and x.get('inverted',0)==0 for x in journals),'No rootActive/Failed/Succeeded gate substituted')
 check('freshstory excludes done and repeatableowner '+i,fact(S,sn[i],'sq024_done','Equal',0) and fact(S,sn[i],'PTFRR1_Issued','Equal',0),i)
 check('own issued receipt exact '+i,fact(S,sn[i],'PTFRS27_SQ024_FRESH_Issued','Equal',1 if i=='90' else 0),i)
opening,oe=N.graph((92,));check('native q105 earned gate retained',fact(N,opening['6'],'q105_done','Greater',0) and ('8','Out','6','In')in oe and ('6','Out','7','In')in oe,'SQ024 root/92 actual q105_done wait')
check('native opening token AND outside trigger retained',N.clean(opening['7'])['condition']['operation']=='AND' and any(x.get('$type')=='questContentToken_ConditionType' and x.get('type')=='SideQuest_Standalone' for x in walk(N.clean(opening['7']))) and any(x.get('type')=='IsOutside' for x in walk(N.clean(opening['7']))),'Original offsite/token semantics preserved')
for i in ['2','3']:
 check('repeatable boot requires storydone '+i,fact(BOOT,bn[i],'sq024_done','Greater',0),'Mutually exclusive storydone0/replaydone>0')
check('private Claire listener connected',('1003','True','1004','In')in pe and ('1004','Out','46','In1')in pe,'1003.True->1004Issued->46.In1')
check('private Claire listener exact nativeinitializer46',P.clean(pn['46'])==INIT.clean(ins['46']),'Native resource/caller sockets unchanged')
check('Claire listener required before story',all(fact(S,sn[i],'PTFRS27_PHONE_CLAIRE_Issued','Equal',1) for i in ['2','3','90']),'All storyclaim/recheck guards')
check('native Claire incoming start/end connected',('0','Out','28','In')in ce and ('28','False','9','In')in ce and ('9','Out','21','holo_claire_calls_v_start')in ce and ('2','Out','10','In')in ce and ('10','Out','21','holo_claire_calls_v_end')in ce,'Actual native controller phase edges')
check('native Claire outgoing start/end connected',('3','Out','30','In')in ce and ('30','False','11','In')in ce and ('11','Out','21','holo_v_calls_claire_start')in ce and ('4','Out','12','In')in ce and ('12','Out','21','holo_v_calls_claire_end')in ce,'Actual native outgoing phase edges')
check('native Claire shared cleanup connected',('1002','True','1003','In7')in she and ('1003','Out7','1240','In')in she,'Existing sharedchain native Claire cleanup')
for body,inp in [('100','sq024_in')]:check('no alternate storyentry bypass',not any(e[2]==body and e[3]not in [inp,'CutDestination'] for e in se),'Story invokes only normal socket')
bad=copy.deepcopy(S.clean(sn['90']));
for x in walk(bad):
 if x.get('factName')=='PTFRS27_SQ024_FRESH_Issued':x['value']=0
check('mutation detects wrong postclaim owner receipt',bad!=S.clean(sn['90']),'Actual-node postclaimmutation')
check('mutation detects removed Claire listener connection',('1004','Out','46','In1')not in pe-{('1004','Out','46','In1')},'Actual resource unlink counterpart of connected-listener oracle')
report={'status':'PASS_SCOPED_RAW_REVIEW_WITH_STATIC_LIMITS','quest_id':'07_nc_underground','reviewer':'Agent D; independent raw-handle/socket parser, no AgentA verifier import','check_count':len(checks),'checks':checks,'source_pins':pins,'confirmed_runtime_defects':[],'scope':'Native normal entry/prerequisites, fresh-vs-repeatable owner separation, connected Claire listener/controller/cleanup and status boundaries. Not every native race frame/outcome replayed.','remaining':['AgentA correctly retains targetreward/vehicle TweakDB definitions, full placement/physics/camera/VO support and saved-owner transitions as CONDITIONAL/OPAQUE; no full static certification.','No gameplay/streaming/reload test is implied by agreement; preserved native branch/source references are independently checked above.'],'runtime_edits':False}
dest.write_text(json.dumps(report,indent=2,ensure_ascii=True)+'\n',encoding='utf-8');print(json.dumps({'status':report['status'],'checks':len(checks)}))
