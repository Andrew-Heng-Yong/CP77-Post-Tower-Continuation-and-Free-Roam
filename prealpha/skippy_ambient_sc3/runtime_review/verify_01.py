"""Independent SC3 saved-state, lifecycle and dependency assertions.

Uses cooked resources plus native inputs, never imports SC3 builders.
No engine execution, installed writes, fact writes or save writes.
"""
import argparse,copy,hashlib,json,re,zlib
from pathlib import Path

H=Path(__file__).resolve().parent; W=H.parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--output',default='verification_01.json')
args=parser.parse_args()
N=W/'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq007/mq007.questphase.json'
O=W/'prealpha/skippy_coaster_sc1/candidate_06/skippy_owner_readback_01.json'
C=H.parent/'native_review/candidate_02/owner_readback_01.json'
S=H.parent/'candidate_02/script_source/PTFR_SideJobsS23.reds'
OLD=W/'prealpha/skippy_coaster_sc2/candidate_01/script_source/PTFR_SideJobsS23.reds'
F=H/'saved_facts_01/ManualSave-23.json'
checks=[]
def check(name,truth):
    checks.append({'name':name,'passed':bool(truth)})
    assert truth,name
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
class Resource:
    def __init__(self,p):
        self.raw=load(p);self.handles={str(v['HandleId']):v['Data'] for v in walk(self.raw) if 'HandleId' in v and 'Data' in v}
        self.root=self.raw['Data']['RootChunk'];self.graph=self.deref(self.root['graph'])
    def deref(self,h):return h.get('Data',self.handles.get(str(h.get('HandleRefId'))))
    def nodes(self,g):return {self.deref(h)['id']:self.deref(h) for h in g['nodes']}
    def edges(self,g):
        nodes=self.nodes(g);sockets={}
        for i,n in nodes.items():
            for h in n.get('sockets',[]):
                d=self.deref(h);hid=str(h.get('HandleId',h.get('HandleRefId')))
                sockets[hid]=(i,d['name']['$value'])
        edges=set()
        for n in nodes.values():
            for h in n.get('sockets',[]):
                for c in self.deref(h).get('connections',[]):
                    d=self.deref(c)
                    a=d['source'];b=d['destination']
                    ai=str(a.get('HandleId',a.get('HandleRefId')));bi=str(b.get('HandleId',b.get('HandleRefId')))
                    if ai in sockets and bi in sockets:edges.add((*sockets[ai],*sockets[bi]))
        return edges
    def condition(self,h,facts):
        c=self.deref(h);t=c['$type']
        if t=='questLogicalCondition':
            values=[self.condition(x,facts) for x in c['conditions']]
            assert c['operation'] in ('AND','OR')
            return all(values) if c['operation']=='AND' else any(values)
        assert t=='questFactsDBCondition',t
        x=self.deref(c['type']);assert x['$type']=='questVarComparison_ConditionType' and x['comparisonType']=='Equal'
        return facts.get(x['factName'],0)==x['value']

native=Resource(N);old=Resource(O);new=Resource(C)
nn=native.nodes(native.graph);on=old.nodes(old.graph);cn=new.nodes(new.graph)
old_edges=old.edges(old.graph)
check('Old Stopped has exactly its intended two predecessors',{(a,b) for a,b,c,d in old_edges if c==13}=={(10,'TurnOff'),(12,'Out')})
check('Old Stopped flows to terminating output',(13,'Out',14,'In') in old_edges and on[14]['type']=='Terminating')
old_writers=[v for v in walk(old.raw) if v.get('$type')=='questSetVar_NodeType' and v.get('factName')=='PTFRSKIP_Ambient_Stopped']
check('Old Stopped is a sole exact receipt writer',len(old_writers)==1 and old_writers[0]['value']==1 and old_writers[0]['setExactValue']==1)
ng=native.deref(nn[3]['phaseGraph']);native_ambient=native.nodes(ng)
check('Native unequipped condition is inverted exact Skippy',any(v.get('$type')=='questCharacterEquippedItem_ConditionType' and v.get('inverted')==1 and v.get('itemID',{}).get('$value')=='Items.mq007_skippy' for v in walk(native_ambient[34])))
check('Native TurnOff is terminating',native_ambient[35]['type']=='Terminating' and native_ambient[35]['socketName']['$value']=='TurnOff')
check('Native parent rearms after TurnOff',(3,'TurnOff',12,'In') in native.edges(native.graph) and (12,'Out',3,'In1') in native.edges(native.graph))

loop=new.deref(cn[10]['phaseGraph']);ln=new.nodes(loop);le=new.edges(loop);ce=new.edges(new.graph)
required_loop={(0,'Out',12,'In'),(12,'Out',13,'In'),(13,'Out',3,'In1'),(3,'TurnOff',14,'In'),(14,'Out',12,'In')}
check('New lifecycle is the native re-equip loop with active telemetry',le==required_loop)
check('New stop cuts entire loop, including pending equip',(12,'CutSource',10,'CutDestination') in ce)
check('New stop finishes after cut and clears Active',all(e in ce for e in [(11,'Out',12,'In'),(12,'Out',15,'In'),(15,'Out',13,'In'),(13,'Out',14,'In')]) and cn[14]['type']=='Terminating')
check('New Stopped cannot be written on normal native TurnOff',{a for a,b,c,d in ce if c==13}=={15})

def strip(x):
    if isinstance(x,dict) and x.get('$type')=='TweakDBID':
        v=x['$value'];number=int(v) if x.get('$storage')=='uint64' else zlib.crc32(v.encode())+(len(v.encode())<<32)
        return {'$type':'TweakDBID','value':number}
    if isinstance(x,dict):return {k:strip(v) for k,v in x.items() if k not in ('HandleId','HandleRefId','sockets')}
    if isinstance(x,list):return [strip(v) for v in x]
    return x
check('Exact native equipped admission retained',strip(nn[12]['condition'])==strip(ln[12]['condition']))
an=copy.deepcopy(nn[3]);ac=copy.deepcopy(ln[3])
an['phaseInstancePrefabs'][0]['prefabNodeRef']=ac['phaseInstancePrefabs'][0]['prefabNodeRef']
check('Native ambient node payload preserved including attachments and dependencies',strip(an)==strip(ac))
check('Explicit native hologram prefab retained',ac['phaseInstancePrefabs'][0]['prefabNodeRef']['$value']=='$/03_night_city/#c_heywood/vista_del_rey/hvdr_03/hvdr_03_questdesign_prefabXYPFG2Y/#mq007_pr_oneliners_screen')

base={
 'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'q307_done':1,'q307_finished':1,
 'q307_2079':1,'q307_main_game_killed':1,'q307_ep1_killed':1,
 'PTFRSKIP_SC3_Request':1,'PTFRSKIP_Ambient_Stop':1,
}
def admits(extra):return new.condition(cn[2]['condition'],base|extra)
matrix=[
 ('old never requested, stop latched',{},True),
 ('old request still pending',{'PTFRSKIP_Ambient_Request':1},False),
 ('old admission not disabled',{'PTFRSKIP_Ambient_Stop':0},False),
 ('old active await acknowledgement',{'PTFRSKIP_Ambient_Claimed':1,'PTFRSKIP_Ambient_Entered':1},False),
 ('old stopped as saved',{'PTFRSKIP_Ambient_Claimed':1,'PTFRSKIP_Ambient_Entered':1,'PTFRSKIP_Ambient_Stopped':1},True),
 ('old inconsistent entered without claim',{'PTFRSKIP_Ambient_Entered':1},False),
 ('fresh quest already issued',{'PTFRS23_MQ007_Issued':1},False),
 ('resume quest already issued',{'PTFRS23_MQ007_RESUME_Issued':1},False),
 ('new owner already claimed',{'PTFRSKIP_SC3_Claimed':1},False),
 ('new owner already entered',{'PTFRSKIP_SC3_Entered':1},False),
 ('new owner has pending stop',{'PTFRSKIP_SC3_Stop':1},False),
 ('new owner terminal receipt',{'PTFRSKIP_SC3_Stopped':1},False),
 ('Tower unfinished',{'q307_finished':0},False),
 ('Tower active',{'q307_active':1},False),
 ('restoration suspended',{'PTFRBASE_Suspended':1},False),
 ('Johnny story active',{'q305_johnny_scene_active':1},False),
 ('point of no return',{'q115_point_of_no_return':1},False),
]
for name,changes,expected in matrix:check('Serialized guard: '+name,admits(changes)==expected)

source=S.read_text();old_source=OLD.read_text()
start=source.index('  private func SkippyAmbient()');end=source.index('  public func LC1SetupReady()',start);body=source[start:end]
check('Historical old receipt never reset','SetFactStr("PTFRSKIP_Ambient_Stopped"' not in body)
writes=re.findall(r'qs\.SetFactStr\("([^"]+)", ([01])\)',body)
check('Driver writes only own request/stop controls',set(writes)=={('PTFRSKIP_Ambient_Request','0'),('PTFRSKIP_Ambient_Stop','1'),('PTFRSKIP_SC3_Stop','1'),('PTFRSKIP_SC3_Request','0'),('PTFRSKIP_SC3_Request','1')})
check('Driver cancels old request before latching old Stop',body.index('SetFactStr("PTFRSKIP_Ambient_Request", 0)')<body.index('SetFactStr("PTFRSKIP_Ambient_Stop", 1)'))
check('No permanent saved fields added',re.findall(r'.*persistent let.*',source)==re.findall(r'.*persistent let.*',old_source))

def expr(text,name):return re.search(r'let '+name+r' = (.*?);',text,re.S).group(1)
def evaluate(expression,facts,variables):
    x=re.sub(r'this\.Fact\("([^"]+)"\)',lambda m:str(facts.get(m.group(1),0)),expression)
    x=x.replace('&&',' and ').replace('||',' or ');x=re.sub(r'!(?!=)',' not ',x)
    x=' '.join(x.split())
    assert re.fullmatch(r'[\w\s()=<>.]+',x),x
    return bool(eval(x,{'__builtins__':{}},variables))
saved=load(F)['facts'];sf={k:v[0] for k,v in saved.items() if v}
check('Saved fixture is actual SC1 terminated state',sf['PTFRSKIP_Ambient_Claimed']==sf['PTFRSKIP_Ambient_Entered']==sf['PTFRSKIP_Ambient_Stopped']==1 and sf.get('PTFRSKIP_Ambient_Stop',0)==0)
check('Candidate retires actual saved fixture',evaluate(expr(body,'oldRetired'),sf,{}))
for name,changes,expected in matrix[:6]:check('Script old retirement: '+name,evaluate(expr(body,'oldRetired'),base|changes,{})==expected)
variables={'safe':True,'oldRetired':True,'progressed':True,'history':False,'owned':True,'freshWanted':False,'resumeWanted':False,'storyOwns':False}
f=sf|{'PTFRSKIP_SC3_Ready':1}
check('Actual progressed saved fixture can request SC3',evaluate(expr(body,'eligible'),f,variables))
for flag in ['freshWanted','resumeWanted','storyOwns']:check('Script gives priority to '+flag,not evaluate(expr(body,'eligible'),f,variables|{flag:True}))
for flag in ['safe','oldRetired']:check('Script requires '+flag,not evaluate(expr(body,'eligible'),f,variables|{flag:False}))
check('Fresh gun still needs history and ownership',not evaluate(expr(body,'eligible'),f,variables|{'progressed':False,'history':False}))
check('New request requires consecutive eligible polls','if eligible && this.skippyPreviousPresent && this.Fact("PTFRSKIP_SC3_Request") == 0' in body)
check('Story requests wait for new owner termination','if (i == 1 || i == 8) && this.Fact("PTFRSKIP_SC3_Claimed") == 1 && this.Fact("PTFRSKIP_SC3_Stopped") == 0 { return false; }' in source)

# Actual old source is a negative control, not merely a hand-coded bad model.
oldbody=old_source[old_source.index('  private func SkippyAmbient()'):old_source.index('  public func LC1SetupReady()')]
oldelig=expr(oldbody,'eligible')
oldelig=re.sub(r'this\.Own\((1|8), "Issued"\)','0',oldelig)
check('Negative control: SC2 rejects actual saved terminated fixture',not evaluate(oldelig,sf,variables))
check('Negative control: SC1 has the erroneous terminal TurnOff edge',(10,'TurnOff',13,'In') in old_edges and (3,'TurnOff',14,'In') in le)
bad=copy.deepcopy(cn[2]['condition']);bad_text=json.dumps(bad).replace('PTFRSKIP_Ambient_Stopped','PTFRSKIP_SC3_NeverWritten')
check('Negative control: removing saved retirement route rejects fixture',not new.condition(json.loads(bad_text),base|sf))

# Event sequences test the graph projection at the ownership boundary.
for sequence in [('equip','unequip','equip','unequip','equip'),('unequip','equip','unequip'),('stop',),('equip','stop','equip')]:
    state='waiting';active=0;entries=0;stopped=0
    for event in sequence:
        if event=='stop':state='terminated';active=0;stopped=1
        elif state!='terminated' and event=='equip' and state=='waiting':state='active';active=1;entries+=1
        elif state!='terminated' and event=='unequip' and state=='active':state='waiting';active=0
        check('Projected loop state '+','.join(sequence)+' after '+event,active in [0,1] and (stopped==0 or active==0))
    check('Projected stop remains terminal '+','.join(sequence),('stop' not in sequence) or state=='terminated')

dep_base=W/'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq007/phases'
comments=dep_base/'mq007_gameplay_comments.questphase.json';expressions=dep_base/'mq007_expression_facts_reset.questphase.json'
comment_data=load(comments);refs={v['sceneFile']['DepotPath']['$value'] for v in walk(comment_data) if 'sceneFile' in v}
reaction_ref='base\\quest\\minor_quests\\mq007\\scenes\\mq007_02_skippy_reactions.scene'
return_ref='base\\quest\\minor_quests\\mq007\\scenes\\mq007_04_skippy_return.scene'
check('Native comments preserve both original Skippy scene dependencies',refs=={reaction_ref,return_ref})
comments_resource=Resource(comments);comment_nodes=comments_resource.nodes(comments_resource.graph);comment_edges=comments_resource.edges(comments_resource.graph)
reachable={0}
while True:
    nxt=reachable|{c for a,b,c,d in comment_edges if a in reachable}
    if nxt==reachable:break
    reachable=nxt
check('Native comments ordinary entry excludes test item-add branch',comment_nodes[0]['socketName']['$value']=='In1' and comment_nodes[39]['socketName']['$value']=='SkippyTestIn' and not ({39,42,43,45}&reachable))
check('Native ambient invokes only ordinary comments entry',{d for a,b,c,d in native.edges(ng) if c==31}=={'In1'})
add_remove_nodes={i for i,n in comment_nodes.items() if any(v.get('$type')=='questAddRemoveItem_NodeType' for v in walk(n))}
check('All native comments item additions/removals are unreachable from ordinary entry',add_remove_nodes=={42,43,45} and not (add_remove_nodes&reachable))
check('Original normal item operation remains weapon use',comments_resource.deref(comment_nodes[21]['type'])['$type']=='questUseWeapon_NodeType')
return_nodes={i for i,n in comment_nodes.items() if n.get('sceneFile',{}).get('DepotPath',{}).get('$value')==return_ref}
check('Return scene only invoked at native refusal one-liner entry',return_nodes=={54,56,58,60,77} and all(d=='SkippyNoReturnOneliner' for a,b,c,d in comment_edges if c in return_nodes))
for target in sorted(return_nodes):
    incoming=[(a,b) for a,b,c,d in comment_edges if c==target]
    check('Return one-liner gated by emo state at node '+str(target),len(incoming)==1 and incoming[0][1]=='False' and comments_resource.condition(comment_nodes[incoming[0][0]]['condition'],sf))
    check('Native emo behavior preserved at node '+str(target),not comments_resource.condition(comment_nodes[incoming[0][0]]['condition'],sf|{'mq007_skippy_goes_emo':1}))
scene=W/'research/sidejobs_s23/base_a/native_02/json/base/quest/minor_quests/mq007/scenes/mq007_02_skippy_reactions.scene.json'
scene_data=load(scene)
check('Native reaction scene has dialogue events',any(v.get('$type')=='scnDialogLineEvent' for v in walk(scene_data)))
check('Native ambient retains reaction prop attach/detach',str(nn[3]).count('#mq007_01_skippy_prop')>0 and str(ln[3]).count('#mq007_01_skippy_prop')==str(nn[3]).count('#mq007_01_skippy_prop'))
pins=[{'path':str(p.relative_to(W)),'sha256':sha(p)} for p in [N,O,C,S,OLD,F,comments,expressions,scene,Path(__file__),H/'review_01.md']]
report={'status':'PASS_INDEPENDENT_SC3_LIFECYCLE_SOURCE_AND_SAVED_STATE_NOT_LIVE','checks':len(checks),'results':checks,
 'saved_fixture_sha256':load(F)['sha256'],'lifecycle_cases':len(matrix),'negative_controls':3,
 'dependencies':{'reaction_scene':reaction_ref,'return_scene':return_ref,'return_scene_input':'SkippyNoReturnOneliner','return_scene_blocked_by_saved_emo_zero':True,'item_add_test_nodes_unreachable_from_normal_input':sorted(add_remove_nodes),'native_prop':'#mq007_01_skippy_prop','native_prefab':ac['phaseInstancePrefabs'][0]['prefabNodeRef']['$value']},
 'limits':['Static graph and evaluated source predicates do not prove engine execution or rendered/audio output.','Lifecycle event sequences abstract native timings and scene interruption.','Native dependency definitions are retained; current archive winner extraction is parent packaging work.'],
 'game_writes':0,'save_writes':0,'fact_writes':0,'pins':pins}
out=H/args.output;assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'checks':len(checks),'sha256':sha(out)}))
