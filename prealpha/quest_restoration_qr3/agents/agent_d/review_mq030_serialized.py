"""Independent serialized MQ030 lease handback verification, no mutations on disk."""
from pathlib import Path
import json,hashlib,ast,copy
W=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent;O=D/'reviews';O.mkdir(exist_ok=True);dest=O/'mq030_serialized.json';assert not dest.exists()
tree=ast.parse((D/'review_mq030.py').read_text());defs=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ['Raw','val','walk']];ns={};exec(compile(ast.Module(body=defs,type_ignores=[]),'<independent raw parser>','exec'),ns);Raw=ns['Raw'];walk=ns['walk'];val=ns['val']
P=W/'prealpha/quest_restoration_qr3/candidate_01/repair_mq030';bf=P/'before.json';af=P/'after.json';B=Raw(json.loads(bf.read_text(encoding='utf-8-sig')));A=Raw(json.loads(af.read_text(encoding='utf-8-sig')))
bn,be=B.graph();an,ae=A.graph();bhn,bhe=B.graph((1020,));ahn,ahe=A.graph((1020,));bin_,bie=B.graph((1020,2));ain,aie=A.graph((1020,2));checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def check(name,ok,ev):checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':ev});assert ok,name
check('additive root node IDs only',set(an)-set(bn)=={'1022','1023'} and set(bn)<=set(an),{'old_count':len(bn),'new_count':len(an)})
for i in bn:
 if i!='1021':check('existing root payload unchanged '+i,B.clean(bn[i])==A.clean(an[i]),i)
 bs=[(str(val(B.d(s)['name'])),B.d(s)['type']) for s in bn[i]['sockets']];as_=[(str(val(A.d(s)['name'])),A.d(s)['type']) for s in an[i]['sockets']]
 check('existing root sockets retained '+i,bs==as_,i)
check('saved helper node IDs retained',set(bhn)==set(ahn),'root/1020')
for i in bhn:
 if i!='3':check('helper payload retained '+i,B.clean(bhn[i])==A.clean(ahn[i]),i)
check('helper nested edges unchanged',bhe==ahe,'Native retire3->mapInactive5->Terminating1 remains')
check('native inner service nodes/edges untouched',set(bin_)==set(ain) and bie==aie and all(B.clean(bin_[i])==A.clean(ain[i]) for i in bin_),'root/1020/2 original #zane/default community spawn,scene,departure/deactivate retained')
expected_removed={('1007','Out','1012','In'),('1020','Out1','1021','In'),('1021','Out','1020','In1')}
expected_added={('1020','Out1','1022','In'),('1022','True','1012','In'),('1022','False','1021','In'),('1021','Out','1023','In'),('1023','True','1012','In'),('1023','False','1020','In1')}
check('only approved removed root edges',be-ae==expected_removed,list(be-ae))
check('only approved added root edges',ae-be==expected_added,list(ae-be))
finished={'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRS23_MQ030_Finished','value':1}}
for i in ['1022','1023']:check('new decision exactowned Finished '+i,A.clean(an[i])['condition']==finished,{'node':i})
for label,bnode,anode in [('active helper retirement3',bhn['3'],ahn['3']),('pending rearm1021',bn['1021'],an['1021'])]:
 old=B.clean(bnode)['condition'];new=A.clean(anode)['condition']
 check('completion wakes original wait '+label,new=={'$type':'questLogicalCondition','conditions':[old,finished],'operation':'OR'},new)
check('lease release only from acknowledgement decisions',{e for e in ae if e[2]=='1012'}=={('1022','True','1012','In'),('1023','True','1012','In')},'No direct Finished fanout or CutSource release branch')
check('native helper Terminating output retained',A.clean(ahn['1'])['type']=='Terminating' and ('3','Out','5','Inactive')in ahe and ('5','Out','1','In')in ahe,'Actual root/1020 retirement then outerOut1')
check('native quest complete still writes only owned Finished',B.clean(bn['1007'])==A.clean(an['1007']) and A.clean(an['1007'])['type']['factName']=='PTFRS23_MQ030_Finished' and ('18','Out1','1007','In')in ae,'No nativefact/ack writer changed')
def evalcond(c,f):
 if c['$type']=='questLogicalCondition':return any(evalcond(x,f) for x in c['conditions'])
 x=c['type'];a=f[x['factName']];b=x['value'];return {'Equal':a==b,'Less':a<b,'Greater':a>b}[x['comparisonType']]
for default in [0,1,2]:
 for done in [0,1]:
  f={'cct_dtn_cloth_01_default_on':default,'PTFRS23_MQ030_Finished':done}
  check('actual serialized retire predicate %s/%s'%(default,done),evalcond(A.clean(ahn['3'])['condition'],f)==(default<1 or done==1),f)
  check('actual serialized pendingwait predicate %s/%s'%(default,done),evalcond(A.clean(an['1021'])['condition'],f)==(default>0 or done==1),f)
  for gate in ['1022','1023']:check('actual reentry/release decision %s %s/%s'%(gate,default,done),evalcond(A.clean(an[gate])['condition'],f)==bool(done),f)
check('regression faulty directrelease detected',('1007','Out','1012','In')in be and ('1007','Out','1012','In')not in ae,'Defective baseline versus actual serialized successor')
check('regression stale pendingwait repeat detected',('1021','Out','1020','In1')in be and ('1021','Out','1020','In1')not in ae,'Actual pending1021 requires completion decision before any reentry')
patch=json.loads((P/'patch.json').read_text(encoding='utf-8-sig'));raw=W/'prealpha/quest_restoration_qr3/candidate_01/archive_source/towercontinued/sidejobs_s23/base_b/mq030.questphase'
check('stage rawhash matches patchafter',sha(raw)==patch['after'],str(raw))
out={'status':'PASS_SERIALIZED_NATIVE_RETIREMENT_ACKNOWLEDGEMENT','reviewer':'Agent D independent raw handle/socket parser; actual candidate readback, no root/AgentE verifier import','check_count':len(checks),'checks':checks,'inputs':{'before_json':{'path':str(bf),'sha256':sha(bf)},'after_json':{'path':str(af),'sha256':sha(af)},'staged_raw':{'path':str(raw),'sha256':sha(raw)},'proposal_review':'mq030_duplicate_owner.json'},'scope':'Actual two-condition/two-decision authored helperretirement and pendingwait protection, preserving all native body/old saved IDs. No CutSource, fabricated ack or lease release before authored helper Out1.','remaining':['Actual engine prefab cancellation relative to Out1 dispatch, saved already-overlapping owners, midframe input queue and visual streaming remain LIVE_ONLY.','No zero-extra-helper-entry scheduling claim: completion after finalrecheck may begin an owned epoch, but lease staysheld until its Finished-aware retirement.'],'runtime_edits':False}
dest.write_text(json.dumps(out,indent=2,ensure_ascii=True)+'\n',encoding='utf-8');print(json.dumps({'status':out['status'],'checks':len(checks)}))
